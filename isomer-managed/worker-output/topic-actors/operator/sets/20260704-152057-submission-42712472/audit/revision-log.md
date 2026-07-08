# Revision Log — FlashAttention-4 White-Box Runtime Model

## Revision Summary
- current draft state: revised draft produced by revision-pass `20260704-151501-pipeline-a9527450`; route decision `finalize`.
- review_followup_policy: no further text revision; only packaging (data statement) and closure.
- manuscript_edit_mode: finalize
- highest-priority fixes: add data-availability statement, record closure decision.
- blockers: none

## Issue-by-issue log

### Issue REV-001
- source issue: Missing data-availability / code-availability statement.
- severity: medium
- why it matters: Reproducibility expectations at most venues; Nature-family journals require a data availability statement.
- fix type: text revision
- concrete change: Add a general data-availability statement to the bundle (produced in `data_statement/`).
- status: resolved
- blocks finalize: no

### Issue REV-002
- source issue: Venue unspecified; exact data-policy cannot be verified.
- severity: low
- why it matters: Statement must match target journal policy.
- fix type: claim downgrade
- concrete change: Statement is labeled general and notes venue is unspecified; controller must replace before final submission.
- status: resolved
- blocks finalize: no

## Deferred / downgraded items
- item: Real B200 silicon validation
- reason: Out of current experiment budget; emulator is the agreed ground-truth source.
- how the manuscript should reflect the limitation: Already explicit in Section 6.
