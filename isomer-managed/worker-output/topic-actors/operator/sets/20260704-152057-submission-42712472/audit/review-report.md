# Review Report — FlashAttention-4 White-Box Runtime Model

## Review mode
- review_followup_policy: no further revision required
- manuscript_edit_mode: finalize
- source_compile_preference: Tectonic first
- manuscript_source_status: Markdown + BibTeX bundle ready

## Summary
- paper / draft: `revised-draft.md` from revision-pass set `20260704-151046-write-08687c39`
- overall judgment: **Accept for submission/archive after minor data-availability packaging.**
- top 3 highest-risk issues:
  1. Emulator-grounded validation, not real B200 silicon.
  2. Venue unspecified; submission target and artifact policy not confirmed.
  3. Synthetic configuration matrix omits production workloads and custom launch parameters.

## Strengths
- Clear white-box modeling motivation and interpretable corrections.
- Strong held-out metrics: 4.50% MAPE, 100% within 30% error, 100% bottleneck accuracy.
- Honest limitation section that does not hide the emulator caveat.
- Complete references and three rendered figures referenced in text.

## Weaknesses
- No public code or dataset repository linked in the bundle.
- The strongest claim rests on a synthetic emulator; silicon transfer is an open question.
- Abstract is long for some venues.

## Key Issues

### Issue 1 — Emulator vs. silicon generalization
- why it matters: The central accuracy claim could be challenged if reviewers want silicon evidence.
- evidence anchor: Section 4.2 and Section 6 state the emulator basis explicitly.
- risk level: medium
- likely route: keep as acknowledged limitation; do not overclaim.

### Issue 2 — Artifact availability
- why it matters: Many systems/modeling venues require code and data for reproducibility.
- evidence anchor: No repository URL in draft or bundle.
- risk level: medium
- likely route: add a data-availability statement and, if possible, deposit the synthetic matrix and predictor code.

## Actionable Suggestions
- problem: artifact links missing
- cause: submission-pass entered before repository deposit
- actionable fix: produce a general data-availability statement noting that code, synthetic config matrix, and emulator are available from the authors on request; deposit in a public repository before final submission if venue requires it.
- acceptance criterion: data-availability statement exists and does not invent identifiers.

## Priority Revision Plan
1. Add data-availability statement.
2. Confirm venue or keep statement general.
3. Route to finalize.

## Experiment Inventory & Research Experiment Plan
- what existing experiments already cover: 160 held-out synthetic configurations, five predictor ablations, per-precision/per-bottleneck breakdown.
- what still lacks evidence: real B200 silicon transfer validation.
- which gaps are text-only rather than experiment-only: repository links and venue policy.

## Novelty Verification & Related-Work Matrix

| Topic | This paper | Closest prior work | Overlap | Residual novelty / value |
| --- | --- | --- | --- | --- |
| FA4 algorithm | Uses FA4 forward pass | Zadouri et al. 2026 | Baseline roofline | Adds bounded corrections |
| Blackwell hardware | B200 bandwidth/throughput assumptions | Jarmusch & Chandrasekaran 2025/2026 | Hardware rates | Calibrated white-box predictor |
| GPU roofline | Hierarchical memory domains | Yang et al. 2019; Williams et al. 2009 | Framework | Occupancy + transfer-size bandwidth |

## References
- See `references.bib` in the paper bundle.

## Optional Internal Score
- overall score: 7/10
- post-revision target: 8/10 after data statement and venue confirmation
