# Pipeline Terminal Report: empirical-pass

## Identity
- **pipeline_id:** `empirical-pass`
- **status:** `complete`
- **topic:** `flash-attention-4-whitebox-runtime-model`
- **actor:** `operator`

## Stages run

| Stage | Skill | Status | Artifacts in | Artifacts out | Route |
|---|---|---|---|---|---|
| frame | `isomer-deepsci-scout` | complete | — | `research-frame` | `baseline` |
| comparator | `isomer-deepsci-baseline` | complete | `research-frame` | `comparator-contract` | `idea` |
| ideate | `isomer-deepsci-idea` | complete | `research-frame`, `comparator-contract` | `selected-hypothesis` | `model` |
| run | `isomer-deepsci-experiment` | complete | `selected-hypothesis`, `comparator-contract` | `experiment-result` | `inconclusive` |
| interpret | `isomer-deepsci-analysis` | complete | `experiment-result`, `comparator-contract` | `analysis-finding` | `decision` |

## Final artifact
`analysis-finding`

## Key finding
The AccelSim-inspired inner-GPU model beats the coarse baseline predictor (validation MAPE 21.4 % vs 56.2 %) after a physically-scoped calibration on 16 B200 measurements, but it does not yet outperform the existing improved predictor (14.9 %). The decomposition correctly identifies the tensor-core bottleneck; the remaining error is mainly launch/tile overhead and coarse causal scaling.

## Recommended next
Route to `isomer-deepsci-decision` to decide whether to:
1. Refine the inner model with launch overhead and per-tile dispatch terms, then recalibrate, or
2. Keep the inner model as a diagnostic complement and continue with the improved predictor as the production runtime estimator.

## Blocker
None.

## Resume point
None — pipeline complete.

## Durable records
- `artifact-SELECTED_HYPOTHESIS-1e9712415f07`
- `artifact-EXPERIMENT_RESULT-6aea1f5ad322`
- `artifact-ANALYSIS_FINDING-0a113bba9db5`

## Files
`isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/actors/operator/isomer-managed/worker-output/topic-actors/operator/sets/20260705-inner-gpu-calibration-faddf4/`
