# Review Audit Plan: FA4 B200 White-Box Runtime Predictor

## Claim set under audit

1. The combined white-box predictor achieves 4.50% MAPE on 160 held-out validation configurations, versus 22.22% for the reproduced FA4 roofline baseline.
2. 100% of validation configurations are within 30% absolute error and 100% bottleneck labels match the emulator.
3. The TMA/L2 effective-bandwidth correction is the dominant improvement by itself (5.76% MAPE).
4. Occupancy and precision terms refine the combined model from 5.76% to 4.50% MAPE.
5. The combined model's correction factors are bounded, physically interpretable, and calibrated from data.

## Strongest evidence

- `validation_metrics.json` (operation set `20260704-130224-experiment-7f255a5e`) reports the exact metrics claimed in the draft.
- `evidence_item-CLAIM_VALIDATION_RECORD-087e55583673` traces each claim to an observed value and verdict.
- `combined_predictions.csv` gives per-configuration predictions, measured values, and bottleneck labels.
- Source code in `repos/topic-main/src/fa4_b200_predictor/` is white-box and auditable.

## Weakest evidence

- Claim 5 (calibrated factors) is weaker than stated. The combined model only calibrates four factors; `l2_factor` and `tma_factor` are fixed defaults. The draft reports ablation values as if they were combined-model values.
- Figures are described but not produced, so visual claims about clustering and residual shape are unverified.
- Citation placeholders in Related Work have not been resolved against the literature scouting reports.

## Likely rejection reasons

1. **Scientific accuracy:** A reviewer reading `calibrate.py` or `calibration_params.json` will notice the mismatch between the six-factor calibration claim and the four-factor calibration reality.
2. **Citation incompleteness:** Placeholder citations and a sparse reference list signal an unfinished manuscript.
3. **Missing figures:** Described-but-absent figures prevent assessment of the visual argument.

## Experiment / analysis inventory

- Experiment stage: completed. All metrics, ablations, and predictions exist.
- Analysis stage: completed. Per-precision and per-bottleneck breakdowns exist.
- No new experiment is needed to address the findings.

## Comparator papers

- FlashAttention-4 paper roofline (baseline comparator, cited as arXiv 2603.05451v1).
- Blackwell microbenchmarks (arXiv 2512.02189v1) for hardware peak/achieved numbers.
- White-box GPU performance modeling methodology (arXiv 2605.04178v1).
- FlashAttention-1/2 and FlashAttention-3 for family positioning.

## Language hygiene risks

- The draft generally avoids operator/agent/route-control language.
- One risk: the phrase "we show" in the Abstract is acceptable for an analytical paper but should not be read as a silicon claim.

## Likely routes

- Preferred: `revise` to fix the calibration description, citations, and figures, then re-review or finalize.
- Alternative if fixes are waived: `finalize` with explicit pre-submission todos — not recommended because of the calibration misstatement.
