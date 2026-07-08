# Experiment Route Decision (Amended with GPU-Load Caveat)

## Decision question
What is the next research stage after validating the overlap-aware roofline revision?

## Measured result (provisional)
- The overlap-aware predictor with `overlap_frac=0.6` raised coarse bottleneck accuracy from **62.5% to 87.5%** on the expanded 24-config saturation matrix.
- The TMA regime improved from **0% to 100%** accuracy.
- MMA and MUFU regimes remained at 100% accuracy.
- HBM accuracy remained at 62.5%.

## Critical caveat
The NCU validation run was executed while `cuda:0` was under heavy load (99% GPU utilization by `VLLM::Worker_TP` processes). NCU SpeedOfLight throughput percentages can be distorted by GPU sharing. The reported accuracy numbers and bottleneck labels are **provisional** and must be re-measured on an idle GPU before a final decision.

## Options considered
1. **Accept the revision as the new default predictor.** Not safe until idle-GPU re-validation confirms the result.
2. **Re-run NCU validation on an idle GPU.** This is the conservative and correct next step.
3. **Return to analysis to diagnose remaining HBM misclassifications.** Defer until idle-GPU measurements are available.

## Chosen route
**Re-run the experiment's NCU validation on an idle GPU.** Do not make a durable adoption decision from GPU-contested measurements.

- If idle-GPU re-validation confirms `overlap_frac ≈ 0.6` and coarse accuracy ≥ 80%, route to `isomer-deepsci-decision` for adoption.
- If idle-GPU measurements materially change the result, route back to `isomer-deepsci-analysis`.

## Blockers
- GPU availability: `cuda:0` is currently occupied by VLLM workers.

## Next action
Wait for or obtain an idle B200 GPU, then re-run `overlap_experiment.py` and update the experiment result summary.
