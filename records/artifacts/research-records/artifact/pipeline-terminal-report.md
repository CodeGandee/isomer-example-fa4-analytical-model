# Pipeline Terminal Report: cycle-level refinement

## Identity
- **pipeline_id:** `empirical-pass` (continuation after previous `complete` terminal report)
- **status:** `complete`
- **topic:** `flash-attention-4-whitebox-runtime-model`
- **actor:** `operator`

## Stages run

| Stage | Skill | Status | Artifacts in | Artifacts out | Route |
|---|---|---|---|---|---|
| frame | `isomer-deepsci-scout` | complete | — | `research-frame` | `baseline` |
| comparator | `isomer-deepsci-baseline` | complete | `research-frame` | `comparator-contract` | `idea` |
| ideate | `isomer-deepsci-idea` | complete | `research-frame`, `comparator-contract` | `selected-hypothesis` | `cycle-level-model` |
| run | `isomer-deepsci-experiment` | complete | `selected-hypothesis`, `comparator-contract` | `experiment-result` | `supported` |
| interpret | `isomer-deepsci-analysis` | complete | `experiment-result`, `comparator-contract` | `analysis-finding` | `continue` |

## Final artifact
`analysis-finding`

## Key finding
The cycle-level FA4 mini-simulator beats the existing improved white-box predictor on the held-out validation split:

| Predictor | Validation MAPE |
|---|---|
| Baseline | 56.23 % |
| Improved | 14.89 % |
| **Cycle-level model** | **13.16 %** |

Calibration MAPE on 16 configs: 7.37 %.

## Recommended next
1. Replace the single `tc_efficiency` scalar with a tile-shape-aware tensor-core rate (`block_m`, `block_n`, `head_dim`, precision/accumulator).
2. Replace the scalar `memory_overlap_factor` with a sequence-length-dependent overlap curve.
3. Add per-tile scheduler dispatch cost separate from fixed launch overhead.
4. Recalibrate and validate; if validation MAPE drops below ~10 %, integrate the cycle-level model as the default predictor backend.

## Blocker
None.

## Resume point
None — pipeline complete for this refinement cycle.

## Durable records
- `experiment-result`: `artifact-EXPERIMENT_RESULT-937733b98359`
- `analysis-finding`: `artifact-ANALYSIS_FINDING-8359fbe7e9a6`

## Files
`isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/actors/operator/isomer-managed/worker-output/topic-actors/operator/sets/20260705-cycle-level-fa4-model-46121e/`
