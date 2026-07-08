# Experiment Result Summary: Overlap-Aware Roofline Revision

## Research question
Does implementing an overlap-aware roofline in the FA4 B200 predictor improve bottleneck classification accuracy on an expanded saturation matrix?

## Hypothesis verdict
**Supported.** The overlap-aware revision raises coarse bottleneck accuracy from 62.5% to 87.5% on the expanded 24-config matrix.

## Intervention
- Added an `overlap_frac` parameter to `Predictor` and `combined_predictor` in `repos/topic-main/src/fa4_b200_predictor/predictor.py`.
- Calibrated `overlap_frac` on the original 12 saturation configs (known NCU labels).
- Validated the best `overlap_frac` against NCU SpeedOfLight on an expanded 24-config matrix.

## Metrics
- **Best overlap_frac:** 0.6
- **Expanded matrix size:** 24 configs
- **NCU ok/error:** 24/0
- **Baseline coarse accuracy (overlap_frac=0.0):** 62.5%
- **Best coarse accuracy (overlap_frac=0.6):** 87.5%
- **Per-regime best accuracy:**
  - hbm: 62.5% (unchanged from baseline)
  - tma: 0% → 100%
  - mma: 100% (unchanged)
  - mufu: 100% (unchanged)

## Key findings
- The overlap term fixes the systematic TMA misclassification observed in the parent experiment.
- HBM accuracy does not improve; some HBM-targeted configs are still measured as compute-bound by NCU, suggesting a separate scheduler/launch effect not captured by overlap alone.
- MMA and MUFU regimes remain perfectly classified.

## Caveats
- Calibration used only the original 12 configs; a larger calibration set might yield a slightly different `overlap_frac`.
- Only bf16 precision was tested.
- The optimal overlap fraction (0.6) is a fitted value, not derived from first principles.
- HBM misclassifications persist and require further diagnosis.

## Baseline relation
The overlap-aware predictor strictly improves on the baseline combined predictor for this task.

## Failure mode
None; all 24 NCU profiles completed successfully.

## Next action
Route to `isomer-deepsci-decision` to decide whether to accept the overlap-aware revision as the new default predictor, or to `isomer-deepsci-analysis` to diagnose the remaining HBM misclassifications.

## Files
- `overlap_calibration.csv`
- `overlap_ncu_results.csv`
- `overlap_accuracy_report.json`
- `overlap_experiment.py`
- `implementation-change-map.md`
- `main-run-record.md`
