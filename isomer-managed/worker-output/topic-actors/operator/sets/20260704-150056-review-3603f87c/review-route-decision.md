# Review Route Decision: FA4 B200 White-Box Runtime Predictor

## Decision question

Should the `isomer-deepsci-pipeline paper-pass` route the FA4 B200 white-box runtime predictor manuscript to `finalize` or `revise`?

## Considered options

1. **Finalize** — Accept the draft with pre-submission todos for BibTeX and rendered figures. This would be appropriate if the only remaining gaps were production artifacts.
2. **Revise** — Return the draft for a focused text correction and citation/figure production pass. This is appropriate because the manuscript contains a material misstatement about what was calibrated in the combined model.

## Chosen route

**`revise`**

## Evidence basis

- `calibration_params.json` in operation set `20260704-130224-experiment-7f255a5e` shows the combined model calibrates only `hbm_factor`, `mma_efficiency`, `mufu_efficiency`, and `launch_overhead_us`.
- `calibrate.py` confirms that `l2_factor`, `tma_factor`, and `smem_factor` are hardcoded defaults in `calibrate_combined` and are only calibrated in the `tma_l2_effective_bw` ablation.
- The draft Sections 3.3, 3.4, and 5.6 describe a six-factor calibration and report ablation values (`f_L2 = 0.45`, `f_TMA = 0.70`) as combined-model calibrated factors.
- This misstatement is a scientific-accuracy issue, not merely a missing figure or citation.

## Rejected alternatives

- `finalize` was rejected because the calibration-factor misstatement would survive into any submission bundle and could be flagged by a reviewer checking the code/artifact.

## Blocker

None that requires new experiments. The blocker is a text/artifact correction task.

## Next action

1. Apply the revision log (`<REVISION_LOG>`) from this review: correct the calibration description, resolve citations, render figures, add BibTeX.
2. Re-run manuscript validation.
3. Re-route to `isomer-deepsci-review` for a final pass or to `isomer-deepsci-finalize` if validation passes and the revision log is closed.

## Durable records

- Review report: `<REVIEW_REPORT>`
- Revision log: `<REVISION_LOG>`
- Audit plan: `<REVIEW_AUDIT_PLAN>`
- Literature benchmark note: `<LITERATURE_BENCHMARK_NOTE>`
- This decision: `<REVIEW_ROUTE_DECISION>`
