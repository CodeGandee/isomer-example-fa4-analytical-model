# Analysis Finding: TMA Misclassification Root Cause and Proposed Predictor Revision

## Parent result
Experiment Result Summary `experiment-result-summary-bottleneck-sat-20260706`: bottleneck-saturation validation of the FA4 B200 white-box predictor.

## Question answered
Why does the combined predictor label three configs as `tma`-bound while NCU SpeedOfLight labels them `compute`/`mma`-bound, and what concrete model revision fixes this?

## Slices performed
- **Slice A (diagnostic ratios):** Computed `tma_time / mma_time` and `memory_time / compute_time` for all 12 saturation configs.
- **Slice B (overlap counterfactual):** Tested an overlap-aware roofline with `overlap_frac` ∈ {0.0, 0.25, 0.50, 0.75}.
- **Slice C (factor sweep):** Grid-searched `tma_factor` × `mma_efficiency` to check for a realistic single-factor recalibration.

## Key findings
1. The three TMA-misclassified configs have predicted `memory_time / compute_time` of only **1.2-2.4x**; they sit in a band where the real kernel is still compute-limited.
2. An overlap-aware roofline with `overlap_frac = 0.75` raises coarse accuracy from 66.7% to **91.7%** and flips all three TMA configs to compute-bound.
3. No realistic single-factor recalibration reaches the same accuracy; the best factor pair (`tma_factor=1.0`, `mma_efficiency=0.5`) requires an implausibly low MMA efficiency.

## Proposed revision
Replace the pure `max(compute, memory)` roofline with an **overlap-aware roofline**:

```
mem_eff = mem_time * (1 - overlap_frac)
predicted_stage_time = max(compute_time, mem_eff)
```

where `overlap_frac` is calibrated from hardware counters or a broader config matrix.

## Caveats
- `overlap_frac = 0.75` is a probe value, not a calibrated physical constant.
- One HBM config (batch=32, heads=16, seqlen=512, head_dim=64) remains misclassified; overlap alone does not explain it.
- L2 and SMEM labels remain non-saturatable with the current workload model.

## Claim impact
The parent claim is **narrowed and strengthened**: the predictor's bottleneck classification is sound for strongly compute-bound regimes, but its `max()` roofline over-states memory dominance for moderate-size problems where TMA overlaps with MMA.

## Next action
Route to `isomer-deepsci-experiment` or `isomer-deepsci-optimize` to implement the overlap term, calibrate `overlap_frac`, and re-validate on an expanded saturation matrix.

## Files
- `slice_a_diagnostic_ratios.csv`
- `slice_b_overlap_counterfactual.csv`
- `slice_c_factor_sweep.csv`
- `analysis_slices_summary.json`
- `analysis-slice-records.md`
- `analysis-campaign-summary.md`
- `analysis-route-decision.md`
