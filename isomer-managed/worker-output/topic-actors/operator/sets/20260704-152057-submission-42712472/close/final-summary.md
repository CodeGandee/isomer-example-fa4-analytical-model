# Final Summary — FlashAttention-4 White-Box Runtime Model

## Executive state
- **Closure recommendation:** `park` (pause and continue later).
- **Current stage:** submission-pass close.
- **Accepted comparator:** reproduced FlashAttention-4 roofline baseline.
- **Route status:** paused pending real-silicon validation and venue confirmation.

## Supported findings
- The combined white-box predictor achieves **4.50% MAPE** and **14.36% max APE** on 160 held-out synthetic FlashAttention-4 forward-pass configurations.
- **100%** of validation configurations fall inside the 30% absolute-error envelope.
- Bottleneck-label accuracy is **100%** on the held-out set.
- The TMA/L2 effective-bandwidth correction is the single largest improvement; the occupancy and precision corrections provide further refinement.

## Partial claims
- The predictor is *potentially* useful for kernel design; this has not been validated in a real design loop.

## Negative / unresolved risks
- Real B200 silicon measurements are not available, so emulator-grounded accuracy may not transfer directly.
- The synthetic matrix omits custom tile sizes, `num_splits`, fused variants, and production workloads.
- No public repository or DOI exists yet for code and data.

## Deliverables
- Revised paper bundle: `revised-draft.md`, `references.bib`, three figures.
- Review report, revision log, and route decision (`finalize`).
- General data-availability statement and supporting inventory/audit.
- Final summary, claim ledger, limitations report, resume packet, and closure decision.

## Package status
- Final bundle copied to submission-pass operation set `20260704-152057-submission-42712472/bundle/`.

## Recommendation
Choose **`park`** rather than `publish` because the strongest claim rests on an emulator, the target venue is unspecified, and no public artifacts exist yet. The work is high quality within its evidence boundary, but honest closure requires silicon validation and repository deposit before submission.

## Reopen conditions
1. Real B200 silicon transfer-validation slice is collected and calibrated factors are re-evaluated.
2. A target venue is chosen and its data-availability policy is confirmed.
3. Code, synthetic configuration matrix, and emulator usage notes are deposited in a public repository with persistent identifiers.
4. (Optional) The matrix is extended to custom tile sizes and `num_splits`.

## Resume material
- See `resume-packet.md` and `finalize-continuity.md` in this directory.
