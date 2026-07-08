# Cycle-Level Math Model for FlashAttention-4 Forward Pass on NVIDIA B200

This report describes `cycle_level_model.py`, a deterministic, closed-form cycle-math model for one FlashAttention-4 (FA4) forward pass on NVIDIA B200. The model replaces the single coarse bandwidth term used in earlier roofline predictors with an explicit, per-hop account of how data is sliced, routed, and transformed through GPU hardware components. A calibration script, `calibrate_cycle_model.py`, fits eight physically-scoped parameters to 16 real B200 measurements and validates on 8 held-out configs.

## Hardware Components Modeled

The model is built around `B200CycleLevelModelSpec`, which captures the B200 at four levels:

1. **SM / scheduler / register file**: 180 SMs, a peak SM clock of 1,965 MHz, 4 warp schedulers per SM, 64 resident warps per SM, 32 threads per warp, and an operand-collector efficiency scalar.
2. **Tensor Core MMA unit**: per-precision FLOPs per SM per clock, a pipeline latency of 16 cycles, and an initiation interval of 1 cycle. A latency-hiding penalty is applied when resident warps are insufficient to fill the pipeline.
3. **MUFU / SFU**: per-precision exp throughput per SM per clock (used for the softmax exponentiation) plus a small shared-memory reduction term.
4. **Memory hierarchy**: L1 (128 B lines, 32 B sectors), L2 (128 B lines), the xbar / NoC to memory partitions, and HBM with row-buffer locality, bank-level parallelism, and read/write turnaround effects.

The model is pure Python, importable, and contains no CUDA execution. It produces a predicted runtime in milliseconds together with per-phase and per-component cycle breakdowns.

## Step-by-Step Data-Flow for One FA4 Tile Block

A tile block corresponds to one output tile (a `block_m x head_dim` fragment of `O`) iterating over the KV dimension. The model follows seven phases:

### 1. Q tile load: HBM → L2 → xbar → L1 → RF/SMEM

For each output row tile, a `block_m x head_dim` Q fragment is loaded once. The transfer is sliced into 32 B L1 sectors and 128 B L2 lines. Only L1 misses traverse the xbar and L2; only L2 misses reach HBM. Each hop is costed separately:

- **L1**: all bytes pay the L1 bandwidth.
- **xbar / NoC**: `bytes / 32` flits, serialized across 16 memory partitions with a contention factor that grows with the SM load.
- **L2**: only the L1-miss fraction is charged at effective L2 bandwidth.
- **HBM**: only the `L1-miss × L2-miss` fraction reaches DRAM, subject to row-buffer hit rate, bank-level parallelism, and a small write turnaround tax.

### 2. K tile load: HBM → L2 → xbar → L1 → RF/SMEM

For each KV iteration, a `block_n x head_dim` K fragment is loaded through the same hop-level model. K tiles are responsible for most of the memory traffic because they are loaded once per (output tile, KV tile) pair.

### 3. MMA Q@K^T: tensor-core accumulator registers

The Q and K fragments are consumed by the tensor core. The MMA FLOPs are `2 × block_m × block_n × head_dim`. Cycles are `FLOPs / (rate_per_sm × active_sms × effective_compute_scale)`, where `effective_compute_scale` combines occupancy and an efficiency scalar. A pipeline latency-hiding penalty is added when too few warps are resident.

### 4. Softmax scaling / exp per row

The `block_m × block_n` attention scores pass through MUFU for `exp` and a lightweight shared-memory / warp-shuffle row reduction for the max and sum. The reduction is modeled as a small term proportional to `rows × log2(cols)` rather than a full SMEM bandwidth sweep.

### 5. V tile load: HBM → L2 → xbar → L1 → RF/SMEM

A `block_n x head_dim` V fragment is loaded for the same KV iteration using the same per-hop cost model as K.

### 6. MMA P@V: output accumulator

The softmax-normalized scores multiply V, again producing `2 × block_m × block_n × head_dim` FLOPs through the tensor core.

### 7. O tile store: RF/SMEM → L1 → xbar → L2 → HBM

After all KV iterations finish, the `block_m x head_dim` output tile is written back. The store path mirrors the load path with a small read/write turnaround penalty.

## Aggregation and Overlap

Across the whole forward pass, the model counts:

- `total_row_tiles = batch × heads × tiles_m` Q loads and O stores.
- `total_iterations = batch × heads × tiles_m × tiles_n × causal_factor` K/V loads and MMA/softmax phases.

Memory and compute are assumed to overlap via prefetching and pipelining. The visible memory cost is `total_memory_cycles × (1 − memory_overlap_factor)`, and the critical path is `max(total_compute_cycles, visible_memory_cycles)`. A fixed launch overhead is added at the end. This closed-form `max()` logic keeps the model deterministic and fast while still exposing the hardware mechanisms that produce each bound.

## Calibration and Validation

`calibrate_cycle_model.py` reads `../20260705-inner-gpu-calibration-faddf4/measurements.csv`, which contains 24 B200 configurations (batch=2, heads=16, seqlen ∈ {1024, 4096, 8192}, head_dim ∈ {64, 128}, causal ∈ {True, False}, precision ∈ {fp16, fp8}). The existing `split` column is used for 16 calibration and 8 validation configs.

Eight parameters are fit with `scipy.optimize.minimize` (L-BFGS-B):

- `tc_efficiency` (tensor-core effective throughput)
- `mufu_efficiency` (MUFU effective throughput)
- `hbm_efficiency` (HBM bandwidth multiplier)
- `l1_miss_rate` and `l2_miss_rate` (cache miss traffic fractions)
- `occupancy_efficiency` (additional occupancy/friction scalar)
- `memory_overlap_factor` (fraction of memory time hidden by compute)
- `launch_overhead_us` (fixed kernel/grid launch cost)

### Results

| Model | Calibration MAPE | Validation MAPE |
|---|---|---|
| Cycle-level model | **7.37%** | **13.16%** |
| Baseline predictor | — | 56.23% |
| Improved predictor | — | 14.89% |

The cycle-level model outperforms the baseline roofline predictor and edges out the improved predictor on the held-out validation split. The fitted values are:

- `tc_efficiency = 3.0` (upper bound, indicating the default FP16/FP8 SM throughput rates are conservative for FA4 tiles)
- `mufu_efficiency = 0.49`
- `hbm_efficiency = 1.0`
- `l1_miss_rate = 0.08`, `l2_miss_rate = 0.25`
- `occupancy_efficiency = 1.31`
- `memory_overlap_factor = 0.85`
- `launch_overhead_us = 16.0 µs`

## Key Assumptions and Residual Error

The largest modeling assumption is that memory and compute overlap according to a single scalar `memory_overlap_factor`. In reality, overlap varies with sequence length, tile size, and the exact instruction schedule; small configs are dominated by launch latency and pipeline fill, while large configs approach steady-state compute. The fitted `launch_overhead_us = 16 µs` compensates for small-sequence fixed costs, but the model still tends to slightly over-predict the smallest configurations and under-predict some large FP8 cases.

The biggest source of residual error is the treatment of tensor-core throughput as a single precision-wide scalar per SM. Modern Blackwell tensor cores have instruction shapes, sub-core count, and warp-scheduler interaction that depend on head dimension, tile shape, and accumulator layout. Calibrating to `tc_efficiency = 3.0` absorbs this, but it is a coarse correction rather than a mechanistic account.

A secondary source of error is the simplified shared-memory reduction model. Although it is much cheaper than a full SMEM bandwidth sweep, it still does not capture warp-shuffle latencies or the fusion of online softmax updates.

## Next Refinement Steps

If asked to proceed further, the next refinement would be to split the single `tc_efficiency` scalar into a tile-shape-aware effective MMA rate. Specifically:

1. Make tensor-core throughput depend on `(block_m, block_n, head_dim)` and accumulator precision, reflecting the actual warp-level mma.sync instruction shape.
2. Add a separate fixed plus per-tile scheduler dispatch cost, rather than a single launch overhead, to better capture small-grid behavior.
3. Replace the scalar `memory_overlap_factor` with a sequence-length-dependent overlap curve derived from the ratio of memory latency to compute per iteration.

These changes would retain the interpretable closed-form structure while pushing validation MAPE closer to single digits.
