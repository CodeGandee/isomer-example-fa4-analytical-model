# Experiment Route Decision (Clean Remote Validation)

## Decision question
What is the next research stage after validating the overlap-aware roofline revision on an idle remote GPU?

## Measured result (clean)
- The overlap-aware predictor with `overlap_frac=0.6` raised coarse bottleneck accuracy from **62.5% to 87.5%** on the expanded 24-config saturation matrix.
- The TMA regime improved from **0% to 100%** accuracy.
- MMA and MUFU regimes remained at 100% accuracy.
- HBM accuracy remained at 62.5%.
- The result was replicated on an idle B200 GPU (cuda:2 on <GPU_HOST>), confirming it is not an artifact of local GPU load.

## Options considered
1. **Accept the revision as the new default predictor.** The improvement is large, physically grounded, and replicated on idle hardware. The remaining HBM misclassifications are a smaller secondary issue.
2. **Re-run on additional GPUs or a larger matrix.** Would add confidence but the current evidence is already solid.
3. **Return to analysis to diagnose remaining HBM misclassifications.** Defer adoption until the secondary HBM issue is resolved.

## Chosen route
**Route to `isomer-deepsci-decision` to adopt the overlap-aware predictor as the new default.** The evidence is strong enough: the main failure mode is fixed, compute-bound regimes are preserved, and the result is replicated under clean conditions. The remaining HBM issue can be tracked as a separate follow-up.

## Blockers
None.

## Next action
Create a decision record on whether to:
- Make `overlap_frac=0.6` the default in `combined_predictor`, or
- Keep `overlap_frac=0.0` as default and expose overlap as an optional predictor variant.
