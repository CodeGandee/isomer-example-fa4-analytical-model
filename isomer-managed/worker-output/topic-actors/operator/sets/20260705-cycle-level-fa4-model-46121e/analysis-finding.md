# Analysis Finding: Cycle-Level FA4 Model Beats Improved Predictor

## Claim
A deterministic, closed-form cycle-level model that traces FA4 data through SM scheduler, RF, L1, xbar, L2, and HBM components step-by-step can achieve lower validation error than the existing improved white-box predictor, after calibrating a small set of physically-scoped parameters on real B200 measurements.

## Evidence
- **Calibration MAPE:** 7.37 % on 16 configs.
- **Validation MAPE:** 13.16 % on 8 held-out configs.
- **Baseline validation MAPE:** 56.23 %.
- **Improved predictor validation MAPE:** 14.89 %.

The cycle-level model therefore outperforms both the coarse baseline and the previous best improved predictor on this data split.

## Mechanism
The model decomposes one FA4 forward pass into per-tile-block phases:
1. Q tile load (HBM → L2 → xbar → L1 → RF/SMEM)
2. K tile load (same path)
3. MMA Q@K^T (tensor core)
4. Softmax exp + row reduction (MUFU/SFU + shared memory)
5. V tile load
6. MMA P@V
7. O tile store (RF/SMEM → L1 → xbar → L2 → HBM)

Each memory hop is costed separately with sector/line slicing, contention, row-buffer locality, and bank-level parallelism. Compute phases use tensor-core throughput, pipeline latency/II, and MUFU throughput. Aggregation uses `max(compute, visible_memory) + launch_overhead`, with a calibrated memory-overlap factor.

## Fitted parameters
```json
{
  "tc_efficiency": 3.0,
  "mufu_efficiency": 0.49,
  "hbm_efficiency": 1.0,
  "l1_miss_rate": 0.08,
  "l2_miss_rate": 0.25,
  "occupancy_efficiency": 1.31,
  "memory_overlap_factor": 0.85,
  "launch_overhead_us": 16.03
}
```

## Limitations
- `tc_efficiency` is a single scalar; it absorbs tile-shape and instruction-layout effects rather than modeling them.
- `memory_overlap_factor` is a single scalar; real overlap varies with sequence length and tile schedule.
- Shared-memory softmax reduction is approximated.

## Route decision
**Continue / refine.** The cycle-level architecture is validated. Next, split `tc_efficiency` into a tile-shape-aware effective MMA rate and replace the scalar memory-overlap factor with a sequence-length-dependent curve to push validation MAPE toward single digits.
