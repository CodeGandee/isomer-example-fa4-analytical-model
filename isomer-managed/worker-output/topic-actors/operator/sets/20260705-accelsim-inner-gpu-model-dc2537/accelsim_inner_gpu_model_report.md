# AccelSim/GPGPU-Sim Inner-GPU Model for FlashAttention-4 on B200

## 1. What AccelSim/GPGPU-Sim Models

[AccelSim](https://github.com/accel-sim/accel-sim-framework) is a trace-driven GPU simulation framework built around the [GPGPU-Sim 4.0](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim4.md) performance model.  Its value for this work is not black-box accuracy, but the explicit mechanistic decomposition of GPU execution that it exposes in its source code.  The relevant subsystems are the SM core front-end, the execution units and operand collectors, the cache hierarchy, the on-chip interconnect, and the DRAM scheduler.

**SM core front-end.**  Each shader core maintains per-warp instruction buffers (`shd_warp_t::m_ibuffer` in [`src/gpgpu-sim/shader.h`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h)) and one or more warp schedulers.  [`scheduler_unit::cycle()`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc) walks the prioritized warp list and, if the scoreboard reports no register hazard, issues at most one warp instruction per scheduler per cycle to the appropriate pipeline.  The scoreboard ([`src/gpgpu-sim/scoreboard.cc`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard.cc)) blocks WAW and RAW dependencies; long operations such as global loads are tracked separately.  This gives us the first concrete inner-GPU bound: **warp-scheduler issue throughput** equals `schedulers_per_sm × issue_rate × num_sms × clock`.

**Execution units and operand collectors.**  After issue, instructions move through an operand-collector register-file stage and then into one of several SIMD pipelines.  [`shader_core_ctx::cycle()`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc) executes the classic fetch/decode/issue/read-operands/execute/writeback pipeline.  Tensor-core instructions are dispatched to the `tensor_core` unit, which is a [`pipelined_simd_unit`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h) with configurable latency and initiation interval (`max_tensor_core_latency`, `tc_initiation_interval`).  The unit accepts a new warp instruction every cycle if the dispatch register is free and the pipeline stage is empty.  That gives two more bounds: **tensor-core MMA issue rate** and **pipeline latency-hiding efficiency**, the latter depending on whether enough warps are resident to cover the tensor-core latency.

**Memory hierarchy.**  GPGPU-Sim models L1 data, texture, and constant caches and a shared L2.  The cache supports both line-based and sector-based allocation; a sector miss only fetches the missing 32-byte sector rather than the full 128-byte line ([`src/gpgpu-sim/gpu-cache.h`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-cache.h), [`src/gpgpu-sim/gpu-cache.cc`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-cache.cc)).  Misses are forwarded to the memory partition unit.  For FA4 this matters because tiled matrix-multiply kernels repeatedly access the same K/V tiles; L1/L2 sector behavior directly changes the bytes that reach HBM.

**Interconnect.**  Misses from SMs travel through a local input-queued crossbar described in [`src/gpgpu-sim/local_interconnect.h`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/local_interconnect.h) and [`src/gpgpu-sim/local_interconnect.cc`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/local_interconnect.cc).  `xbar_router::RR_Advance` and `iSLIP_Advance` show how output-port conflicts serialize requests when many SMs target the same memory partition.  A simple contention model can therefore be parameterized by the ratio of active SMs to memory partitions.

**DRAM.**  The DRAM subsystem in [`src/gpgpu-sim/dram.h`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/dram.h), [`src/gpgpu-sim/dram.cc`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/dram.cc), and [`src/gpgpu-sim/dram_sched.cc`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/dram_sched.cc) implements FR-FCFS scheduling per bank, tracks row-buffer hits, bank-group timing, and read/write turnaround penalties.  The address decoder ([`src/gpgpu-sim/addrdec.cc`](https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/addrdec.cc)) maps linear addresses to chip, bank, row, and column, with optional bitwise or IPOLY hashing.  For an analytical predictor, the key knobs are **row-buffer hit rate**, **bank-level parallelism (BLP)**, and the **read/write turnaround tax**.

## 2. Mechanisms Most Relevant for FlashAttention-4 on B200

FlashAttention-4 on B200 is a tensor-core-heavy, memory-tiled kernel.  The dominant inner-GPU mechanisms are:

- **Warp-scheduler issue rate.**  Even with enough FLOPs and enough HBM bandwidth, the kernel cannot run faster than schedulers can issue warp instructions.  Each MMA tile, each TMA copy, and each softmax step consumes scheduler cycles.
- **Tensor-core throughput and pipeline latency.**  Blackwell's tensor cores are deeply pipelined.  The throughput bound is `mma_flops / (rate_per_sm × num_sms × clock × occupancy)`.  If occupancy is low, the latency-hiding bound can exceed the pure throughput bound.
- **Operand-collector and register-file pressure.**  FA4's large tile registers and frequent operand reuse create collector/register friction.  This is best modeled as a small multiplicative efficiency on the scheduler issue rate rather than as a detailed collector simulation.
- **L1/L2 sector traffic.**  FA4 streams K/V tiles through L1/L2 repeatedly.  Configurable miss rates plus sector overfetch let us estimate how many bytes actually reach HBM.
- **HBM row locality and BLP.**  HBM effective bandwidth is not the datasheet peak; it is `peak × row_hit_factor × blp_factor × rw_turnaround_factor`.
- **Crossbar contention.**  When many SMs miss simultaneously, output-port conflicts at the memory partitions add latency, especially for small batches.

## 3. Proposed Analytical Extension

The existing FA4 predictor uses `max(FLOPs/peak, bytes/bandwidth)` plus occupancy and TMA corrections.  We propose replacing the single compute and single memory terms with five explicit per-component bounds and taking the maximum:

1. **Compute-issue bound** — total warp instructions divided by aggregate scheduler issue throughput.
2. **Tensor-core throughput bound** — MMA FLOPs divided by effective tensor-core rate.
3. **MUFU throughput bound** — softmax `exp` ops divided by MUFU rate.
4. **Execution-pipeline / occupancy bound** — tensor-core throughput inflated when resident warps cannot cover tensor-core latency.
5. **Memory-pipeline bound** — the maximum of L1, L2, and HBM transfer times, where HBM bandwidth uses row locality, BLP, and read/write turnaround factors.
6. **Interconnect bound** — crossbar serialization added as an additive latency proportional to the contention factor.

Each bound is a closed-form expression; there is no event-driven simulation.  The model is implemented in `inner_gpu_model.py` as `B200InnerGPUModel`, which accepts a `FA4WorkloadDesc` and an optional `B200InnerGPUModelSpec` and returns a breakdown of predicted time by component together with the dominant bottleneck.

## 4. Sources

- AccelSim framework repository: <https://github.com/accel-sim/accel-sim-framework>
- GPGPU-Sim 4.0 overview in AccelSim docs: <https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim4.md>
- `scheduler_unit::cycle()` and `issue_warp`: <https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc>
- `Scoreboard`: <https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard.cc>
- `tensor_core` unit and `pipelined_simd_unit`: <https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h>
- `gpu-cache.h` / `gpu-cache.cc` (sector caches): <https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-cache.h>
- `dram.h`, `dram.cc`, `dram_sched.cc` (FR-FCFS scheduler): <https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/dram_sched.cc>
- `local_interconnect.h` / `local_interconnect.cc` (crossbar): <https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/local_interconnect.h>
- `addrdec.cc` (address decoding): <https://github.com/accel-sim/accel-sim-framework/blob/dev/gpu-simulator/gpgpu-sim/src/gpgpu-sim/addrdec.cc>
- AccelSim ISCA 2020 paper: <https://conferences.computer.org/isca/pdfs/ISCA2020-4QlDegUf3fKiwUXfV0KdCm/466100a473/466100a473.pdf>
