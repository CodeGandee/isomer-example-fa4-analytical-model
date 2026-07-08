# Experiment Result Summary: Bottleneck-Saturation Validation of the FA4 B200 Predictor

**Research question:** Can the FA4 B200 white-box predictor correctly predict the dominant bottleneck regime when configurations are pushed to saturate a specific hardware component?

**Verdict:** partially_supported.

**Intervention:** Selected 12 extreme FA4 configurations across hbm/tma/mma/mufu regimes, predicted bottleneck labels with the combined white-box predictor, and profiled each config with `ncu --section SpeedOfLight` on cuda:0.

**Metrics:**
- Total configs: 12
- NCU ok/error: 12/0
- Overall coarse bottleneck accuracy (compute vs memory): 66.7%
- Overall fine bottleneck accuracy: 66.7%
- Per-regime coarse accuracy: hbm 66.7%, tma 0.0%, mma 100.0%, mufu 100.0%

**Caveats:**
- Only four of six white-box bottleneck labels (hbm, tma, mma, mufu) are independently saturatable with the current workload model; l2 and smem bandwidths dominate other memory stages in every tested configuration.
- NCU SpeedOfLight reports only coarse compute/memory families. Fine label mapping uses predictor per-stage times.
- Single-GPU profiling on cuda:0; multi-GPU and concurrency effects not captured.
- Combined predictor kept default calibration.

**Next action:** Proceed to isomer-deepsci-analysis to diagnose why the model over-weights TMA relative to MMA for medium-size configs.

**Files:**
- saturation_predictions.csv
- saturation_ncu_results.csv
- saturation_accuracy_report.json
- saturation_experiment.py
