# Experiment Result Summary: Overlap-Aware Roofline Revision (Clean Remote Validation)

## Research question
Does implementing an overlap-aware roofline in the FA4 B200 predictor improve bottleneck classification accuracy on an expanded saturation matrix?

## Validation environment
- **Host:** <GPU_HOST> (resolved as b200-4)
- **GPU:** NVIDIA B200, cuda:2 (verified idle during profiling)
- **NCU:** 2025.4.1.0
- **Torch:** 2.12.1+cu130
- **flash_attn.cute:** importable from `repos/extern/flash-attention`

## Hypothesis verdict
**Supported.** The overlap-aware revision raises coarse bottleneck accuracy from 62.5% to 87.5% on the expanded 24-config matrix when measured on an idle GPU.

## Intervention
- Added an `overlap_frac` parameter to `Predictor` and `combined_predictor` in `repos/topic-main/src/fa4_b200_predictor/predictor.py`.
- Calibrated `overlap_frac` on the original 12 saturation configs.
- Validated the best `overlap_frac` against NCU SpeedOfLight on an expanded 24-config matrix on remote idle GPU.

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
- The remote idle-GPU result matches the earlier local GPU-busy result, confirming the improvement is not an artifact of GPU load.
- MMA and MUFU regimes remain perfectly classified.
- HBM accuracy does not improve; some HBM-targeted configs are still measured as compute-bound by NCU.

## Caveats
- Calibration used only the original 12 configs; a larger calibration set might yield a slightly different `overlap_frac`.
- Only bf16 precision was tested.
- The optimal overlap fraction (0.6) is a fitted value, not derived from first principles.
- One HBM config (batch=32, heads=16, seqlen=512, head_dim=64) and two expanded HBM configs remain misclassified; overlap alone does not explain them.

## Baseline relation
The overlap-aware predictor strictly improves on the baseline combined predictor for this task.

## Next action
Route to `isomer-deepsci-decision` to decide whether to adopt the overlap-aware predictor as the new default.

## Files
- `overlap_calibration.csv`
- `overlap_ncu_results.csv`
- `overlap_accuracy_report.json`
- `overlap_experiment.py`
- `implementation-change-map.md`
- `main-run-record.md`
- `experiment-route-decision.md`
