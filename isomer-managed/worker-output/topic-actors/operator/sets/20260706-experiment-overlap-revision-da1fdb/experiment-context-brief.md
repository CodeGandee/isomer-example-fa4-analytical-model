# Experiment Context Brief

## Recovered context
- **Parent analysis:** `analysis-finding-tma-overlap-revision-20260706`
- **Route decision:** `route-decision-tma-overlap-revision-20260706`
- **Research Topic:** flash-attention-4-whitebox-runtime-model
- **Topic Workspace:** <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model
- **Effective Topic Actor:** operator (ready)
- **Comparator basis:** NCU SpeedOfLight coarse bottleneck (compute vs memory) on real B200 hardware, same as the parent saturation experiment.
- **Metric contract:** Coarse bottleneck accuracy (compute vs memory) and fine bottleneck accuracy (mma/mufu/hbm/l2/smem/tma) against NCU-derived labels.

## Evidence target
- **Role:** main/test
- **Level:** solid

## Research question
Does implementing an overlap-aware roofline in the FA4 B200 predictor improve bottleneck classification accuracy on an expanded saturation matrix, and what is the best calibrated `overlap_frac`?

## Hypotheses
- **Null hypothesis:** The overlap-aware roofline does not improve coarse bottleneck accuracy over the current combined predictor.
- **Alternative hypothesis:** The overlap-aware roofline raises coarse bottleneck accuracy above the current 66.7% on the expanded saturation matrix.
- **Selected hypothesis:** The alternative hypothesis, derived from `route-decision-tma-overlap-revision-20260706`.

## Expected answer signal
A calibrated `overlap_frac` in the range [0.5, 0.85] yields coarse accuracy ≥ 80% on the expanded matrix, with TMA configs no longer systematically misclassified.
