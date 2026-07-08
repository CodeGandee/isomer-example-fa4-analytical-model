# Analysis Finding: Inner-GPU Model Calibration on B200

## Experiment
Calibrated the AccelSim-inspired inner-GPU model on 16 real B200 `flash_attn_func` measurements and evaluated it on 8 held-out configurations. The calibration optimized five physically-scoped parameters:

- `tc_scale` — scalar on the per-precision tensor-core throughput table
- `operand_collector_efficiency` — scheduler/RF friction
- `l1_miss_rate` — L1 sector miss rate
- `l2_miss_rate` — L2 miss rate forwarded to HBM
- `hbm_row_buffer_hit_rate` — DRAM row-locality factor

## Key result

| Predictor | Calibration MAPE | Validation MAPE |
|---|---|---|
| Baseline (`predictor.py`) | — | 56.2 % |
| Improved (`improved_predictor.py`) | — | 14.9 % |
| Inner-GPU model (initial instruction count) | 38.4 % | 119.3 % |
| Inner-GPU model (refined instruction count) | 18.3 % | 21.4 % |

The initial inner-GPU model massively over-predicted large configs because its warp-instruction-count heuristic made the scheduler-issue bound scale with `S^4`. Refining the instruction model so that tensor-core issue is consistent with tensor-core throughput (one warp instruction per `mma_throughput / issue_rate` FLOPs) removed that pathology and brought validation error below the baseline predictor.

## Bottleneck diagnosis

Across the calibration and validation sets, the refined model's dominant predicted component is **tensor-core throughput**, with occasional **memory-pipeline** dominance at the smallest sequence lengths. This matches the prior NCU observation that FA4 on B200 is generally compute-bound.

## Why it still trails the improved predictor

The improved predictor includes explicit launch/grid overhead and a per-tile scheduler/dispatch term that the inner model currently lacks. The residual 21 % validation error is concentrated at:

- Small sequence lengths (1024), where fixed launch overhead is a large fraction of runtime.
- Causal versus non-causal transitions, where the simple `seq_factor = 0.5` scaling under-counts the actual work reduction.
- FP8 versus FP16 transitions, where the current per-precision throughput table is a single scalar and does not capture Blackwell FP4/FP8 scheduling subtleties.

## Interpretation

The inner-GPU decomposition is **supported as an explanatory framework**: it beats the coarse baseline, identifies the tensor-core bottleneck, and grounds each term in AccelSim/GPGPU-Sim mechanisms. It is **not yet supported as a replacement** for the improved predictor.

## Recommended next route

1. Add explicit launch overhead and a per-tile dispatch term to the inner model (mirroring `ImprovedPredictor`).
2. Replace the scalar `seq_factor` with a tile-aware causal work estimate.
3. Re-run the calibration/validation; if validation MAPE drops below the improved predictor, integrate the inner model as the default backend.
4. If the gap persists, keep the inner model as a diagnostic complement and route to `isomer-deepsci-decision` to decide whether further mechanism fidelity (e.g., TMA modeling, warp-specialization) is worth the added complexity.
