# Literature Benchmark Note: FA4 B200 White-Box Runtime Predictor

## Scope

This note benchmarks the draft's Related Work and citation coverage against the topic's existing literature scouting reports and standard venue expectations for a systems/ML-hardware paper.

## Source records consulted

- `artifact-LITERATURE_SCOUTING_REPORT-fc6d5ca8b4a3`
- `artifact-LITERATURE_SURVEY_REPORT-1cf5125a64f8`
- `artifact-DRAFT_SECTION_SET-db586e5e0d48` (Related Work and References)

## Coverage assessment

| Expected topic | Draft status | Gap |
| --- | --- | --- |
| FlashAttention-1/2 | Placeholder `[citation: FlashAttention-1/2]` | Needs real citations |
| FlashAttention-3 | Placeholder `[citation: FA3]` | Needs real citation |
| FlashAttention-4 | arXiv ID only (2603.05451v1) | Needs full BibTeX |
| Roofline model | Placeholder `[citations: roofline; GPU performance modeling]` | Needs real citations |
| GPU performance modeling | Placeholder | Needs real citations |
| Blackwell microbenchmarks | arXiv ID only (2512.02189v1) | Needs full BibTeX |
| White-box methodology | arXiv ID only (2605.04178v1) | Needs full BibTeX |

## Venue expectations

A strong systems or ML-hardware submission typically cites:
- The algorithm paper (FA4) with full bibliographic data.
- Prior FlashAttention versions (FA1, FA2, FA3) to establish the family lineage.
- Roofline / machine-balance literature.
- Recent white-box GPU modeling work to position against black-box surrogates.
- Architecture/microbenchmark papers that justify the hardware constants.

The current draft's Related Work discusses all of these topics but leaves the citations unresolved.

## Recommendation

Resolve placeholders using the literature scouting reports, add full BibTeX entries, and ensure every arXiv ID is accompanied by title, authors, year, and primary category. This is a production task, not a research gap.
