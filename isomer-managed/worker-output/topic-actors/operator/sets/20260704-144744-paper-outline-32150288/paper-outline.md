# Paper Outline: A White-Box Analytical Model for FlashAttention-4 Runtime on NVIDIA B200

## One-Sentence Idea

A white-box analytical model that adds occupancy-aware throughput, effective HBM/L2/TMA bandwidth curves, and precision-specific Tensor Core rates to the FlashAttention-4 roofline predicts B200 kernel runtime within 4.5% MAPE and labels the dominant bottleneck correctly on every held-out configuration, demonstrating that the largest errors in a pure roofline model come from bandwidth-efficiency assumptions rather than from the algorithmic quantity estimates.

## Thesis

The FlashAttention-4 paper roofline is a useful first-order model, but it systematically overestimates achievable throughput because it assumes peak HBM/L2/TMA bandwidth and full occupancy. By adding three physically interpretable corrections—tile-size-dependent occupancy, transfer-size-dependent effective bandwidth, and precision-specific Tensor Core/MUFU rates—the model predicts B200 forward-pass runtime within 4.5% MAPE and correctly labels the dominant bottleneck on every held-out configuration.

## Story Spine

1. Kernel runtime prediction is usually treated as a black-box regression problem; a white-box model grounded in the GPU execution model is more useful for bottleneck diagnosis.
2. The FlashAttention-4 roofline provides a clean algorithmic baseline but ignores occupancy saturation and effective bandwidth on Blackwell.
3. We extend the roofline with bounded, interpretable corrections and calibrate them on a disjoint set of emulator-generated measurements.
4. Ablations show that effective TMA/L2 bandwidth is the dominant error source; occupancy and precision terms refine the result.
5. The combined model satisfies every success criterion and can identify the limiting hardware domain without launching the kernel.

## Scoped Claims

- On the held-out synthetic validation set of 160 FlashAttention-4 forward-pass configurations, the combined predictor achieves 4.50% MAPE versus 22.22% for the reproduced roofline baseline.
- All 160 validation configurations fall within 30% absolute error, and the predicted dominant bottleneck matches the emulator on all 160.
- The TMA/L2 effective-bandwidth correction alone achieves 5.76% MAPE; occupancy and precision terms reduce MAPE further to 4.50% and max APE from 19.9% to 14.4%.
- The model operates from the input configuration alone and does not use measured runtime of the target input.

## Method Abstraction

- **Input**: batch, heads, sequence length, head dimension, causal mask, precision (BF16/FP16/FP8/FP4).
- **Algorithm quantities**: white-box MMA FLOPs, exponential/softmax ops, HBM/L2/SMEM/TMA bytes.
- **Baseline**: max-domain roofline using peak B200 throughput numbers.
- **Corrections**: occupancy factor; effective HBM/L2/TMA bandwidth curves; precision-specific MMA/MUFU throughput.
- **Output**: predicted runtime in milliseconds, predicted dominant bottleneck, per-stage time breakdown.

## Evaluation Plan

- **Dataset**: synthetic configuration matrix covering batch, heads, seqlen, head_dim, causal, precision.
- **Split**: 20% calibration, 20% held-out validation, 60% reserved test.
- **Metrics**: MAPE, Max APE, % within 30% APE, bottleneck-label accuracy.
- **Comparator**: reproduced FlashAttention-4 roofline baseline for B200.
- **Fairness**: no model uses target measured runtime; calibration constants from disjoint split only.

## Analysis Plan

- Ablation table across baseline, occupancy-only, TMA/L2-effective-bandwidth, precision-only, and combined models.
- Per-precision MAPE/max APE breakdown.
- Per-bottleneck residual analysis.
- Worst-case inspection and calibration-overfitting check.

## Section Outline

1. **Abstract** — problem, approach, key results, implication.
2. **Introduction** — motivate white-box modeling, state goal, preview corrections, list contributions, roadmap.
3. **Related Work** — FlashAttention family, GPU performance models, Blackwell specifics, gap.
4. **Method / Model** — workload computation, baseline roofline, corrections, calibration, bottleneck labeling.
5. **Experiments** — config matrix, split, emulator, variants, calibration, metrics.
6. **Results** — ablation table, combined metrics, precision/bottleneck breakdowns, figures.
7. **Limitations** — emulator ground truth, synthetic matrix, approximations, transfer risk.
8. **Conclusion** — summary, practical use, future silicon validation.

## Figures and Tables

- Table 1: ablation metrics.
- Table 2: per-precision MAPE/max APE.
- Table 3: per-bottleneck MAPE/max APE.
- Figure 1: predicted vs measured runtime scatter.
- Figure 2: residual distribution by bottleneck.
- Figure 3: predictor pipeline diagram.

## Route Decision

- **Ready for write**: true
- **Route to**: `isomer-deepsci-write`
- **Reason**: paper view and evidence view are separated, claim-evidence boundary is explicit, validation passes with no blockers, and section writing plan is ready.

## Key Evidence Records

- `artifact-ANALYSIS_CAMPAIGN_SUMMARY-6fc33c201154`
- `decision_record-ANALYSIS_ROUTE_DECISION-21767b5a6cb1`
- `evidence_item-EXPERIMENT_RESULT_SUMMARY-7390c54fdef5`
- `evidence_item-CLAIM_VALIDATION_RECORD-087e55583673`
- `artifact-SELECTED_HYPOTHESIS-bab659036a3c`
- `artifact-EVALUATION_CONTRACT-7f255a5e6694`
- `artifact-ACCEPTED_BASELINE_RECORD-e673ec2be9b4`
