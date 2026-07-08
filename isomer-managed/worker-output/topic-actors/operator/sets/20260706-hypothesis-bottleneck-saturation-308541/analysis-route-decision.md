# Analysis Route Decision

## Decision question
What concrete revision to the FA4 B200 white-box predictor best explains the TMA misclassification observed in the bottleneck-saturation experiment?

## Considered options
1. **Recalibrate `mma_efficiency` down to ~0.5.** Reaches 91.7% accuracy but is physically unrealistic for B200 Tensor Cores and would break runtime prediction. Rejected.
2. **Introduce a compute/memory overlap term.** A simple `overlap_frac` probe reaches 91.7% accuracy with all TMA configs corrected. Physically grounded because TMA is an async copy engine that can run concurrently with MMA warps. **Selected.**
3. **Add a fixed compute bias / slack like `ImprovedPredictor.bottleneck_mem_slack`.** Would require slack > 1.4 to flip TMA configs, which is too large to be a clean modeling choice. Rejected as the primary revision; useful as a secondary knob.

## Chosen route
Implement an **overlap-aware roofline** in the predictor package. The revision should:
- Keep per-stage compute and memory time estimates.
- Compute an effective memory time: `mem_eff = mem_time * (1 - overlap_frac)`.
- Predict the bottleneck from `max(compute_time, mem_eff)`.
- Calibrate `overlap_frac` on a broader matrix (not just the 12 saturation configs) and validate against NCU SpeedOfLight.

## Evidence basis
- Slice A: TMA misclassified configs have moderate `memory/compute` ratios (1.2-2.4x).
- Slice B: `overlap_frac = 0.75` flips all three TMA configs and raises coarse accuracy to 91.7%.
- Slice C: No realistic single-factor recalibration matches the overlap result.

## Blockers
- None for the modeling decision. The actual calibration of `overlap_frac` requires a broader experiment.

## Next action
Route to `isomer-deepsci-experiment` or `isomer-deepsci-optimize` to implement the overlap term, choose a calibration procedure, and re-validate on an expanded saturation matrix.
