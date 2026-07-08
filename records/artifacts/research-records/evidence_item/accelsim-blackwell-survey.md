# Accel-Sim / GPGPU-Sim Blackwell Survey

## Purpose
Understand whether Accel-Sim (and its GPGPU-Sim 4.x performance model) contains any experimental Blackwell (sm_100 / sm_120) GPU simulation implementation that we can learn from for our FA4 white-box cycle-level model.

## Method
1. Search local Accel-Sim clone (`repos/extern/accel-sim-framework`) for `sm100`, `sm120`, `Blackwell`, `GB100`, `GB200`.
2. Clone the GPGPU-Sim 4.x dependency (`accel-sim/gpgpu-sim_distribution`, `dev` branch, depth=1) and search the simulator source.
3. Query GitHub issues/PRs in `accel-sim/accel-sim-framework`, `accel-sim/gpgpu-sim_distribution`, and upstream `gpgpu-sim/gpgpu-sim_distribution`.
4. Check NVBit releases because Accel-Sim's tracer is built on NVBit.

## Bottom-line Finding
**There is no experimental Blackwell simulation implementation in Accel-Sim or GPGPU-Sim today.** The newest supported ISA is Ampere (sm_80 / sm_86). Ada (sm_89) is currently proposed in an open PR by mapping Ada binaries to the Ampere opcode table because the two architectures share the same SASS ISA.

## Detailed Findings

### Accel-Sim Framework
- **ISA definitions** (`gpu-simulator/ISA_Def/`): only Kepler, Pascal, Volta, Turing, and Ampere opcode tables exist.
- **Tested configs** (`gpu-simulator/configs/tested-cfgs/`): up to `SM86_RTX3070` and `SM80_A100`.
- **Trace frontend** (`gpu-simulator/trace-driven/trace_driven.cc`): maps binary versions 80/86/75/70/61/35 to the corresponding opcode table; any other version prints `unsupported binary version: <N>` and exits.
- **Tracer tool** (`util/tracer_nvbit/install_nvbit.sh`): pinned to NVBit 1.7.6.

### GPGPU-Sim 4.x Performance Model
- Searched the `dev` branch of `accel-sim/gpgpu-sim_distribution`.
- Only one hit for SM120: a `cub/block/block_histogram.cuh` header mentioning “SM120 or later.”
- No Blackwell, GB100, GB200, or sm_100/sm_120 references in simulator source (`src/gpgpu-sim/`, `src/cuda-sim/`, configs).

### GitHub Issues and PRs
| Repository | Item | Content |
| --- | --- | --- |
| `accel-sim/accel-sim-framework` | Issue #385 | RTX 5090 (Blackwell) tracing fails with `cuobjdump fatal: Value 'sm_120' is not defined for option 'gpu-architecture'` on CUDA 12.4; on 12.8 it later aborts with `unsupported binary version: 120`. |
| `accel-sim/accel-sim-framework` | Issue #488 | RTX 5070 Ti reports `unsupported binary version: 120`. |
| `accel-sim/accel-sim-framework` | Issue #408 | “How to add a new GPU?” — mentions `hopper_opcode.h` was finished in a prior commit and asks about `blackwell_opcode.h`. |
| `accel-sim/accel-sim-framework` | PR #548 (open) | Adds `sm_89` Ada support by mapping Ada binaries to the **Ampere** opcode table, because Ada and Ampere share SASS ISA. Adds only a `trace.config` and a config entry. |
| `accel-sim/gpgpu-sim_distribution` | PR #80 (closed) | “Hopper config” — only changed hardware parameters (SM count, HBM channels, L1/L2 sizes), not ISA modeling. |

### NVBit
- **NVBit 1.7.6** (what Accel-Sim uses): added SM_110 support; no SM_120 support.
- **NVBit 1.8** (April 2026): alpha TMA support for Hopper and Blackwell, but Accel-Sim has not updated its tracer pin to 1.8.
- NVBit issue #152 reports crashes on SM_120 even in newer releases.

## What We Can Learn from Accel-Sim for Our White-Box Model
Even though Blackwell is not modeled, Accel-Sim/GPGPU-Sim is a useful structural reference for a cycle-level GPU simulator.

### 1. Shader-Core Pipeline (`src/gpgpu-sim/shader.h`)
- A shader core contains configurable counts of functional units:
  - SP (single-precision FP)
  - DP (double-precision FP)
  - SFU (special function / transcendental)
  - INT (integer)
  - Tensor Core
  - MEM (load/store)
  - Up to 8 `specialized_unit` entries for future ISA extensions.
- Each unit is modeled as a `pipelined_simd_unit` with latency and initiation interval (II).
- This maps directly to a white-box model where we track per-unit occupancy and issue cycles.

### 2. SASS-to-Execution-Unit Dispatch
- `gpu-simulator/ISA_Def/ampere_opcode.h` maps each SASS mnemonic to:
  - an opcode enum (`OP_FMA`, `OP_HMMA`, `OP_LDG`, ...), and
  - an execution-unit category (`SP_OP`, `DP_OP`, `INTP_OP`, `TENSOR_CORE_OP`, `SPECIALIZED_UNIT_3_OP`, `LOAD_OP`, `STORE_OP`, ...).
- `trace_driven.cc` selects the opcode table by binary version.
- For Blackwell we would need a new table, or—like Ada—map sm_120 to Ampere/Hopper if new instructions are ignored.

### 3. Memory Hierarchy Timing (`src/gpgpu-sim/gpu-cache.h`, `dram.h`, `gpu-sim.h`)
- Per-SM caches: L1I, L1T (texture), L1C (constant), L1D (data) with configurable line size, sets, associativity, MSHRs.
- Shared L2 cache with partition/bank hashing (`src/gpgpu-sim/hashing.cc`).
- DRAM controller with row/bank state machines and FR-FCFS scheduling; timing parameters include RCD, RAS, RP, CCD, RTW, WTR.
- This supports the “slice data into N parts and model each transfer through the hierarchy” style we want.

### 4. Interconnect (`src/gpgpu-sim/local_interconnect.*`, `icnt_wrapper.*`)
- Models NoC/ICNT contention between SMs and memory partitions.
- Essential for capturing bottleneck shifts between compute and memory.

## Implications for a Blackwell-Specific Model
Since Accel-Sim has no Blackwell code, we must supply architecture-specific details ourselves:

1. **ISA additions**: Blackwell introduces FP4/FP6 Tensor Core instructions, improved FP8 paths, and 5th-generation Tensor Cores. None of these opcodes exist in Accel-Sim.
2. **Hardware parameters**: SM count, HBM4 channels/width, L1/L2 sizes, register file size, clock domains, Tensor Core throughput/latency must come from NVIDIA documentation or microbenchmarks.
3. **Execution units**: We can model new Blackwell units as additional `SPECIALIZED_UNIT_N_OP` entries, following Accel-Sim's pattern.
4. **Tracing**: To trace real Blackwell kernels, Accel-Sim would need NVBit 1.8+ and a new opcode/config table; we do not need to run the simulator, but we should know this is the gap.

## Recommendation
Use Accel-Sim as a **structural template** for the mini-simulator:
- Adopt its separation of shader core, cache hierarchy, DRAM, and interconnect.
- Adopt its trace-driven “SASS op → execution unit → latency/throughput” dispatch model.
- Do not wait for upstream Blackwell support; derive Blackwell parameters from the B200 whitepaper and CUDA binary utilities docs, and add the new opcodes to our own opcode-to-unit mapping.

## Files and Repositories Referenced
- Local Accel-Sim: `repos/extern/accel-sim-framework`
- Local GPGPU-Sim: `repos/extern/accel-sim-framework/gpu-simulator/gpgpu-sim`
- Upstream Accel-Sim: https://github.com/accel-sim/accel-sim-framework
- Upstream GPGPU-Sim: https://github.com/accel-sim/gpgpu-sim_distribution
- NVBit: https://github.com/NVlabs/NVBit

## Citation Ledger
- Accel-Sim GitHub issue #385 — RTX 5090 / Blackwell tracing failure.
- Accel-Sim GitHub issue #488 — RTX 5070 Ti `unsupported binary version: 120`.
- Accel-Sim GitHub issue #408 — “What should I do to add and simulate a new GPU?”
- Accel-Sim GitHub PR #548 — sm_89 Ada support by mapping to Ampere ISA.
- Accel-Sim GPGPU-Sim PR #80 — Hopper config (hardware parameters only).
- NVBit release notes v1.7.6 and v1.8.
