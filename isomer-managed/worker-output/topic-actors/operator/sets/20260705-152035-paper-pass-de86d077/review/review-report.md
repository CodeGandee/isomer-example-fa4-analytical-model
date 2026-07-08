# Review Report: White-Box FA4 B200 Predictor on Real Hardware

## Audit scope

Review the revised-draft.md manuscript for claim-evidence alignment, language hygiene, figure-table consistency, and completeness of the real-hardware narrative.

## Strengths

- The manuscript clearly distinguishes the emulator-grounded preliminary result (4.50% MAPE) from the final real-hardware result (12.62% validation / 10.01% query MAPE). The reader cannot confuse the two.
- All main numerical claims map directly to metrics.json rows or analysis-campaign-summary records: 540 measured configs, 60 NCU-profiled, first-pass refutation, launch-overhead fix, and bottleneck refinement.
- The NCU profiling methodology and bottleneck-label calibration are described in enough detail for reproduction.
- Tables 2 and 3 are internally consistent with the source CSVs.
- Figures 1 and 2 are regenerated from the refined real-hardware predictions; Figure 3 is the unchanged conceptual pipeline diagram.
- Limitations are explicit: fp4 unsupported, all NCU labels compute-bound, synthetic matrix, driver-specific calibration.

## Weaknesses and likely reviewer objections

1. **Limited NCU diversity.** Every NCU profile is compute-bound, so the memory-bound side of the slack calibration is untested. This is already stated as a limitation but is the largest empirical gap.
2. **Small-absolute-runtime outliers.** The worst cases are small configs where launch overhead dominates. A reviewer may ask whether a relative-error metric is fair for sub-0.5 ms kernels. The draft notes this but does not quantify it beyond the top five cases.
3. **No LaTeX/PDF bundle.** The repository has no LaTeX/pandoc/PDF toolchain, so the output is Markdown only. PDF generation is a post-pipeline step requiring external tooling.
4. **References.** The bibliography is inherited from the previous draft and should be checked for accuracy before external submission. In particular the arXiv identifiers for FlashAttention-4 and the Jarmusch/Blackwell papers are placeholders consistent with the prior bundle but should be verified.

## Actionable suggestions

- Keep the compute-bound NCU caveat prominent in the Limitations section.
- Add a sentence in Section 5.7 noting that worst-case APEs occur when measured runtime is below 0.4 ms, where launch latency dominates absolute time.
- Do not claim generalisation beyond the measured matrix.
- Route to finalize after the minor wording checks below.

## Revision priority

- Minor text fixes only. No new experiments are required because the current evidence already satisfies the stated thresholds.

## Recommendation

Route to `finalize` after applying the minor textual notes above.
