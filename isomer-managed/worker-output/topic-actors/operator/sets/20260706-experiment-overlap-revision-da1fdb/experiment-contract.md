# Experiment Contract

## Run identification
- **run id:** 20260706-experiment-overlap-revision-da1fdb
- **operation set:** 20260706-experiment-overlap-revision-da1fdb
- **research question:** Does an overlap-aware roofline revision improve FA4 B200 bottleneck classification accuracy?
- **research type:** model-revision validation
- **research objective:** Implement the overlap term, calibrate `overlap_frac`, and validate against NCU SpeedOfLight on an expanded saturation matrix.

## Hypotheses
- **Null hypothesis:** The overlap-aware roofline does not improve coarse bottleneck accuracy over the current combined predictor (66.7%).
- **Alternative hypothesis:** The overlap-aware roofline raises coarse bottleneck accuracy above 66.7% on the expanded saturation matrix.
- **Selected hypothesis:** Alternative hypothesis.
- **Strongest alternative hypothesis:** The improvement comes only from an unrealistic single-factor recalibration (e.g., `mma_efficiency=0.5`) rather than from a physically grounded overlap term.

## Comparator basis
- **Comparator id:** NCU SpeedOfLight coarse bottleneck (compute vs memory) on real B200 hardware.
- **Dataset:** Expanded saturation matrix of FA4 forward-pass configs.
- **Split:** All configs are used for validation; calibration of `overlap_frac` uses a small hold-out subset or predictor-only grid search, then validated against NCU.
- **Required metric keys:**
  - `coarse_bottleneck_accuracy`
  - `fine_bottleneck_accuracy`
  - `per_regime_accuracy`
  - `best_overlap_frac`
  - `baseline_accuracy` (combined predictor, for comparison)
- **Primary metric:** `coarse_bottleneck_accuracy`

## Evaluator assumptions
- NCU SpeedOfLight reports the dominant throughput family (compute vs memory). We map NCU `compute` to the predictor's larger compute stage (`mma` or `mufu`) and NCU `memory` to the predictor's largest memory stage (`hbm`, `l2`, `smem`, or `tma`).
- The expanded matrix keeps bf16 precision and causal masking to preserve comparability with the parent experiment.

## Expected outputs
- Modified predictor source file (`predictor.py`) with `overlap_frac` support.
- `overlap_calibration.csv`: predictor-only accuracy vs `overlap_frac` on the expanded matrix.
- `overlap_ncu_results.csv`: NCU-measured vs predicted bottlenecks for the best `overlap_frac`.
- `overlap_accuracy_report.json`: final accuracy summary.
- `experiment-result-summary` durable record.

## Stop condition
Stop when the best `overlap_frac` is identified and validated with NCU on the expanded matrix.

## Abandonment condition
Abandon if the overlap term cannot be implemented without breaking existing predictor tests or if NCU profiling fails on more than 30% of configs.

## Compute budget
- Implementation + smoke: <5 min
- Calibration (predictor-only): <2 min
- NCU validation: ≤24 configs, estimated 5-15 min

## Route linkage
- **From:** `route-decision-tma-overlap-revision-20260706`
- **To:** `isomer-deepsci-analysis` if the result needs further interpretation, or `isomer-deepsci-decision` if the revision is accepted.
