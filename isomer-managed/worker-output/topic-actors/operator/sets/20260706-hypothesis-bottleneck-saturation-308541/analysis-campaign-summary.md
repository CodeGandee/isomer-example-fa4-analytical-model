# Analysis Campaign Summary

## Stable support
- The predictor is **100% accurate on strongly compute-bound regimes** (`mma` and `mufu`).
- The `mma` vs `mufu` distinction is internally consistent: the model flips to `mufu` when `head_dim` is small, matching the softmax-to-MMA ratio.

## Contradiction / partial support
- The predictor labels three configs as `tma`-bound, but NCU reports them as `compute`/`mma`-bound.
- Diagnostic ratios show these configs have predicted `memory_time / compute_time` of only **1.2-2.4x**, not the large memory dominance the model name implies.
- One HBM config is also misclassified; its ratio is 13.4x, so overlap alone does not explain it.

## Model-revision finding
- A **compute/memory overlap counterfactual** with `overlap_frac = 0.75` raises coarse accuracy from 66.7% to **91.7%** and flips all three TMA configs to compute-bound.
- A **factor-sweep recalibration** can reach the same accuracy only with an unrealistic `mma_efficiency = 0.5` (halving Tensor Core throughput), so it is not the preferred explanation.
- The most plausible concrete revision is to **replace the pure `max()` roofline with an overlap-aware roofline** where a fraction of memory/TMA time is hidden behind compute warps.

## Unresolved ambiguity
- The optimal overlap fraction (0.75) is a probe value, not a calibrated physical constant.
- The one remaining HBM misclassification (batch=32, heads=16, seqlen=512, head_dim=64) is not fixed by overlap; it may be a launch/scheduler effect below the model's resolution.
- L2 and SMEM remain non-saturatable with the current workload model.

## Next route
- Return to `isomer-deepsci-experiment` or `isomer-deepsci-optimize` to calibrate the overlap fraction against a broader config matrix and measured per-stage counters, or implement the overlap term in the predictor package and re-validate.
