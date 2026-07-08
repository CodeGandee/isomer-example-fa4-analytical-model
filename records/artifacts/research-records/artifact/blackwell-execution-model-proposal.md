# Proposal: Per-SM Execution-Unit Reservation Model for FlashAttention-4 on Blackwell

## Background

Our current FA4 white-box model decomposes one forward pass into coarse phases (Q/K/V loads, MMA QK^T, softmax, MMA PV, O store) and uses scalar efficiency factors (`tc_efficiency`, `mufu_efficiency`, `hbm_efficiency`, `memory_overlap_factor`) to absorb contention, scheduling, and overlap effects. The model already beats the prior improved predictor (validation MAPE 13.16 % vs 14.89 %), but the scalar factors hide the actual hardware execution flow and are hard to generalize across tile shapes, sequence lengths, and SKU differences.

Recent evidence from Accel-Sim/GPGPU-Sim and a Blackwell microbenchmark study (arXiv:2507.10789v2) shows that contemporary GPUs expose enough structure to build a more mechanistic model:

- Accel-Sim maps SASS instructions to a small set of execution-unit categories (SP, INT, DP, SFU, Tensor Core, MEM, specialized units) and dispatches them through a configurable pipeline.
- The Blackwell microbenchmark paper reports per-SM resource counts, instruction latencies, and memory-hierarchy latencies/bandwidths for both GH100 (Hopper) and GB203 (consumer Blackwell).
- NVIDIA tuning guides and architecture whitepapers confirm SM100/SM120 differences in warp counts, shared-memory sizes, register files, and cache sizes.

## Objective

Replace the scalar-efficiency abstraction with a **per-SM execution-unit reservation model** that computes kernel runtime by scheduling FA4's SASS-level micro-ops onto Blackwell's actual pipelines and memory hierarchy. The model should remain analytical (closed-form or small iterative solve) rather than becoming a full cycle-accurate simulator.

## Core Idea: Pipeline-Residue Critical-Path Model

### 1. Micro-op Decomposition

Instead of coarse phases, decompose one FA4 tile iteration into a directed acyclic graph (DAG) of micro-ops derived from PTX/SASS:

- `LDG` / `LDS` / `STS` / `STG` for memory movement
- `HMMA` / `QMMA` / `OMMA` for tensor-core MMA (precision-dependent)
- `MUFU` for `exp` / `log` in softmax
- `FMA`, `IADD3`, `SHFL`, `BAR`, `DEPBAR` for reductions, indexing, and synchronization

Each node carries:
- Execution-unit category (`TENSOR`, `MEM`, `SP/INT`, `SFU`, `SYNC`)
- Input/output register/shared-memory operands
- Dependency edges (register / shared-memory RAW/WAW)

### 2. Execution-Unit Reservation

Per SM, maintain a reservation table for each unit type:

| Unit | GB203 (RTX 5080) | SM100 (B200) | Notes |
| --- | --- | --- | --- |
| Unified INT32/FP32 | 128 cores / SM | 128 cores / SM | Can only issue INT or FP per cycle; mixed workloads create hazards |
| Tensor Core | 4 × 5th-gen / SM | 4 × 5th-gen / SM | FP4→OMMA, FP6/FP8→QMMA, FP16→HMMA |
| FP64 | 2 / SM | 64 / SM | Negligible for FA4 |
| SFU (MUFU) | shared pipeline | shared pipeline | Measured latency ~21 cycles, throughput limited |
| MEM (LD/ST) | 1 load/store pipeline per sub-core | 1 per sub-core | Coalesces warp accesses into cache-line requests |

For a tensor-core micro-op, the per-SM throughput is bounded by:

```
tensor_cycles = ceil(num_mma_ops * mma_latency / (num_tensor_cores * warps_per_sm * ops_per_warp_per_cycle))
```

This replaces `tc_efficiency` with an occupancy- and instruction-count-aware bound.

### 3. Memory-Hierarchy Queueing

Model memory traffic as moving through a multi-level network with measured service times:

| Level | GB203 latency | GH100 latency | GB203 measured BW | GH100 measured BW |
| --- | --- | --- | --- | --- |
| Shared memory | low warp count: lower; high warp count: higher | higher at low warp count, better at high warp count | ~shared with L1 | ~shared with L1 |
| L1 data cache | 30–40 cycles | 30–40 cycles | limited by partition | limited by partition |
| L2 cache | ~358 cycles | ~273 cycles | monolithic, higher under full load | partitioned, lower ceiling |
| Global memory | ~877 cycles | ~659 cycles | read ~8.2 TB/s, write ~1.6 TB/s | read ~15.8 TB/s, write ~2.2 TB/s |

For each memory micro-op, compute:
- Number of cache lines / sectors touched (coalescing model)
- Time at each level = service_time + queueing_delay
- Queueing delay from concurrent warps accessing the same partition/bank

This replaces the scalar `memory_overlap_factor` and `hbm_efficiency` with a contention model that depends on access pattern, tile size, and SM count.

### 4. Critical-Path Scheduling

Combine the micro-op DAG with resource reservations:

- Earliest-start time for each node = max(predecessor finish times).
- Finish time = earliest-start + max(unit-latency, throughput-bound duration).
- Resource contention shifts start times according to the reservation table.
- The kernel runtime is the maximum finish time over all nodes, divided by the number of active SMs and adjusted for wave quantization.

Because FA4's outer loop is regular, the DAG for one tile iteration can be unrolled across iterations; the steady-state throughput is determined by the bottleneck stage (often tensor-core throughput or HBM bandwidth).

### 5. SKU-Aware Parameters

Use different default parameter sets for SM100 (B200, HBM3e, TMEM, 64 warps/SM, 228 KB shared) and SM120 (consumer Blackwell, GDDR7, no TMEM, 48 warps/SM, 128 KB shared). The model selects the parameter set by compute capability.

## Falsifiable Claim

**Claim:** For FlashAttention-4 forward passes on Blackwell, a per-SM execution-unit reservation model that uses measured microbenchmark latencies and per-instruction execution-unit mapping predicts kernel runtime with lower validation MAPE than the scalar-efficiency model, after calibrating no more than five SKU-level scaling knobs.

**Metric:** Validation MAPE on held-out (head dim, sequence length, batch size) configurations, measured against `nvprof`/`ncu` kernel durations on B200.

**Boundary condition:** The comparison holds for configs where FA4 is compute-bound or balanced; pure memory-bound configs may still be dominated by HBM bandwidth and show smaller gains.

**Minimal experiment:**
1. Implement a Python prototype of the reservation model for one FA4 tile iteration.
2. Extract micro-op counts from CUTLASS/FlashAttention SASS for FP16 and FP8 variants on sm_100.
3. Calibrate five knobs (e.g., shared-memory contention factor, L2 partition factor, tensor-core pipeline depth, MUFU throughput, warp-scheduler issue width) on 8 training configs.
4. Predict runtime on 8 held-out configs and compare MAPE to the existing scalar model.

**Abandonment condition:** If the reservation model does not improve validation MAPE by at least 2 percentage points over the scalar model, or if calibrating the new knobs requires more than 16 measured configs, fall back to extending the scalar model with sequence-length-dependent overlap curves.

## Mechanism Sketch

The scalar model treats FA4 as a sequence of phases connected by a single overlap factor. In reality, the GPU overlaps independent micro-ops across warps and SMs. The reservation model captures this by:

1. Keeping the instruction mix explicit (tensor vs memory vs SFU vs sync).
2. Binding each instruction type to a finite per-SM resource.
3. Propagating delays through the dependency graph rather than assuming a global overlap scalar.
4. Letting contention emerge from shared resources (register file ports, L1/L2 partitions, HBM channels) rather than being absorbed into efficiency factors.

For example, softmax currently uses a single `mufu_efficiency` scalar. In the new model, softmax is a subgraph of `MUFU` + `SHFL` + `STS`/`LDS` + `BAR` nodes, and its runtime is the critical path through that subgraph under the SFU and shared-memory reservations.

## Strongest Alternative Hypothesis

The alternative is that the scalar-efficiency model is already close to the irreducible error limit for this workload, and the extra complexity of per-instruction scheduling does not reduce MAPE because compiler optimizations, occupancy variation, and kernel-launch overheads dominate. In that case, the better investment is to make `tc_efficiency` and `memory_overlap_factor` depend on tile shape and sequence length rather than adding a full micro-op scheduler.

## Strongest Objection

Micro-op counts and scheduling details depend on the compiled SASS, which changes with CUDA version, `flash-attn` version, and kernel parameters. If the SASS cannot be obtained automatically for every config, the model becomes a manual reverse-engineering effort rather than a reusable predictor.

**Mitigation:** Use PTX-level micro-op counts as a proxy (PTX is stable and emitted by `nvcc`), and calibrate a small per-architecture SASS→PTX expansion factor. This is how Accel-Sim's trace-driven frontend stays portable across GPU generations.

## Anti-Win Condition

The model is **not** a win if it requires per-kernel SASS inspection to beat the scalar model. It is a win only if a small, architecture-level parameter set generalizes across FA4 configs.

## Code-Level Plan

1. **SASS/PTX extractor** — add a script that compiles a small FA4 kernel for `sm_100` and extracts instruction counts per category using `nvdisasm` or `cuobjdump`.
2. **Micro-op DAG builder** — construct a template DAG for one FA4 tile iteration from the PTX instruction stream.
3. **Reservation solver** — implement the iterative critical-path scheduler in Python/SymPy or NumPy.
4. **Parameter calibrator** — fit the five SKU-level knobs to measured B200 runtimes.
5. **Validation harness** — compare predicted vs measured cycles and produce MAPE and per-component breakdown.

## Risks

- **Risk:** SASS for Blackwell FP4/FP6 is still evolving; `OMMA`/`QMMA` encodings may not be stable across CUDA 12.8/12.9.
  - *Mitigation:* Start with FP16 (`HMMA`) and FP8 (`QMMA`), which are already documented.
- **Risk:** The microbenchmark paper measures GB203 (consumer), while our target is B200/SM100 (datacenter). Some latencies differ.
  - *Mitigation:* Use the paper as initial values and calibrate SM100-specific parameters on the B200 directly.
- **Risk:** The reservation solver may be too slow for large sequence lengths if the DAG is huge.
  - *Mitigation:* Solve one tile iteration analytically and scale by iteration count; do not build a per-instruction graph for the whole sequence.

## Next Route

**Experiment.** The idea is ready for a bounded implementation pass: build the Python prototype, extract PTX/SASS counts for a few FA4 configs, calibrate on B200 measurements, and compare MAPE against the scalar model. If the prototype shows ≥2 percentage point MAPE improvement, continue to full integration; otherwise, route to decision to evaluate the simpler tile-shape-aware scalar extension.

## References

- Khairy et al., *Accel-Sim: An Extensible Simulation Framework for Validated GPU Modeling*, ISCA 2020. (`custom.blackwell_papers/accel-sim-framework.pdf`)
- Jarmusch et al., *Dissecting the NVIDIA Blackwell Architecture with Microbenchmarks*, arXiv:2507.10789v2, 2025. (`custom.blackwell_papers/blackwell-microbenchmarks-arxiv-2507.10789v2.pdf`)
- NVIDIA, *Blackwell Tuning Guide*, CUDA 12.8, 2025. (`custom.blackwell_papers/nvidia-blackwell-tuning-guide-cuda12.8.pdf`)
- NVIDIA, *NVIDIA RTX Blackwell GPU Architecture*, 2025. (`custom.blackwell_papers/nvidia-rtx-blackwell-gpu-architecture.pdf`)
- Local survey: `custom.accelsim_blackwell_survey`
- Local research report: `custom.blackwell_simulation_research`

---

**Status:** Selected hypothesis ready for experiment.  
**Produced by:** isomer-deepsci-idea (operator-assisted)  
**Consumer:** isomer-deepsci-experiment  
**Topic:** flash-attention-4-whitebox-runtime-model
