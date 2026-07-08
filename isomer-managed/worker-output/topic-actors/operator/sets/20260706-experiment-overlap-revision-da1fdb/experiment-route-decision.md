# Experiment Route Decision

## Decision question
What is the next research stage after validating the overlap-aware roofline revision?

## Measured result
- The overlap-aware predictor with `overlap_frac=0.6` raises coarse bottleneck accuracy from **62.5% to 87.5%** on the expanded 24-config saturation matrix.
- The TMA regime improves from **0% to 100%** accuracy.
- MMA and MUFU regimes remain at 100% accuracy.
- HBM accuracy remains at 62.5%; some HBM-targeted configs are still measured as compute-bound by NCU.

## Options considered
1. **Accept the revision as the new default predictor.** The improvement is large and the mechanism is physically grounded. HBM misclassifications are a separate, smaller problem.
2. **Return to analysis to diagnose remaining HBM misclassifications.** This would delay adoption but might yield a more complete fix.
3. **Run a larger calibration experiment.** More configs could refine `overlap_frac` but the current result is already solid.

## Chosen route
**Route to `isomer-deepsci-decision`** to decide whether to adopt the overlap-aware predictor as the new default. The evidence is strong enough for a decision: the revision fixes the main failure mode (TMA misclassification), preserves perfect accuracy on compute-bound regimes, and leaves only a secondary HBM issue.

## Blockers
None.

## Next action
Create a `route-decision` durable record and hand off to decision-making.
