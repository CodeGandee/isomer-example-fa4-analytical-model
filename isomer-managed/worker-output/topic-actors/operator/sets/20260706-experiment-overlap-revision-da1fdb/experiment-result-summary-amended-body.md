# Experiment Result Summary: Overlap-Aware Roofline Revision (Amended with GPU-Load Caveat)

## Research question
Does implementing an overlap-aware roofline in the FA4 B200 predictor improve bottleneck classification accuracy on an expanded saturation matrix?

## Important caveat: GPU load during profiling
At the time of the NCU validation run, `cuda:0` was under heavy concurrent load (`nvidia-smi` reported 99% GPU utilization by `VLLM::Worker_TP` processes). NCU SpeedOfLight throughput percentages can be affected by GPU sharing and scheduling contention. The measured `compute_pct` and `memory_pct` values, and therefore the NCU-derived bottleneck labels, may not reflect idle-GPU behavior. **The reported accuracy numbers should be treated as provisional until the experiment is re-run on an idle GPU.**

## Hypothesis verdict
**Provisionally supported**, pending idle-GPU re-validation.

## Intervention
- Added an `overlap_frac` parameter to `Predictor` and `combined_predictor` in `repos/topic-main/src/fa4_b200_predictor/predictor.py`.
- Calibrated `overlap_frac` on the original 12 saturation configs (known NCU labels from a prior run).
- Validated the best `overlap_frac` against NCU SpeedOfLight on an expanded 24-config matrix.

## Provisional metrics
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

## Provisional findings
- The overlap term is directionally consistent with the hypothesis: it flips TMA-targeted configs from memory-bound to compute-bound, matching the parent analysis.
- MMA and MUFU regimes remain perfectly classified.
- HBM accuracy does not improve; some HBM-targeted configs are still measured as compute-bound.

## Required follow-up
1. Re-run NCU SpeedOfLight on the same 24-config matrix when `cuda:0` is idle (no VLLM or other compute processes).
2. Re-calibrate `overlap_frac` using the idle-GPU NCU labels.
3. If the idle-GPU result confirms the provisional result, proceed to decision. If not, return to analysis.

## Files
- `overlap_calibration.csv`
- `overlap_ncu_results.csv`
- `overlap_accuracy_report.json`
- `overlap_experiment.py`
- `implementation-change-map.md`
- `main-run-record.md`
- `experiment-route-decision.md`

## Baseline relation
The overlap-aware predictor code change is in place and backward-compatible (`overlap_frac=0.0` reproduces the old behavior). The measured improvement is provisional pending idle-GPU re-validation.

## Next action
Re-run the NCU validation on an idle GPU before making a durable decision. Until then, route to `isomer-deepsci-decision` with the GPU-load caveat noted.
