# Final Summary — FlashAttention-4 White-Box Runtime Model

## Executive state
- **Closure recommendation:** `park` (pause and continue later).
- **Current stage:** submission-pass close.
- **Accepted comparator:** reproduced FlashAttention-4 roofline baseline on real B200.
- **Route status:** paused pending public repository deposit and venue selection.

## Supported findings
- The final refined white-box predictor achieves **12.62% validation MAPE** and **10.01% query MAPE** on 435 real B200 configurations.
- **93.3%** of validation and **96.4%** of query configurations fall inside the 30% absolute-error envelope.
- **100%** NCU bottleneck accuracy on both validation and query splits after the NCU-guided slack.
- A bounded **launch-overhead term** is the dominant correction when moving from emulator to real B200 silicon.
- The NCU slack $\gamma = 3.0$ closes the memory-vs-compute label gap without changing predicted runtimes.

## Partial claims
- The predictor is *potentially* useful for kernel design; this has not been validated in a real design loop.

## Negative / unresolved risks
- The matrix omits custom tile sizes, `num_splits`, fused variants, production workloads, and fp4.
- Every NCU profile in this dataset is compute-bound, so the slack is not validated for memory-bound regimes.
- No public repository or DOI exists yet for code and data.
- References have not been externally verified.

## Deliverables
- Final reviewed paper bundle: `revised-draft.md`, `references.bib`, three figures, prediction CSVs, `generate_figures.py`.
- Review report, revision log, and route decision (`finalize`).
- General data-availability statement and supporting inventory/audit.
- Final summary, claim ledger, limitations report, resume packet, and closure decision.

## Package status
- Final bundle copied to submission-pass operation set `20260705-153222-submission-4948b3fa/bundle/`.

## Recommendation
Choose **`park`** rather than `publish` because, although the model is now supported on real B200 hardware, no public repository exists and the target venue is unspecified. The bundle is submission-ready within its evidence boundary, but honest closure requires a public deposit and venue confirmation before external submission.

## Reopen conditions
1. Code, real B200 measurement CSVs, NCU profiles, and configuration matrix are deposited in a public repository with persistent identifiers.
2. A target venue is chosen and its data-availability policy is confirmed.
3. References are verified against the venue's style requirements.
4. (Optional) Memory-bound NCU profiles and fp4 measurements are collected to extend coverage.

## Resume material
- See `resume-packet.md` and `finalize-continuity.md` in this directory.
