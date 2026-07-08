# Analysis Context Brief

## Parent Boundary
- **Parent object:** Experiment Result Summary `experiment-result-summary-bottleneck-sat-20260706` (bottleneck-saturation validation of the FA4 B200 white-box predictor).
- **Parent claim:** The combined white-box predictor correctly identifies compute-bound regimes (mma/mufu) but over-predicts memory/TMA dominance for several configurations that NCU measures as compute-bound.
- **Evidence question:** Why does the model predict `tma` for configs that NCU labels as `compute`/`mma`, and what concrete revision to the model would fix the misclassification without breaking the regimes it currently gets right?
- **Comparison target:** NCU SpeedOfLight coarse bottleneck (compute vs memory) on 12 saturation configs.
- **Stop condition:** We stop when we have (a) a quantified explanation of the TMA misclassification, (b) a tested model revision that raises coarse accuracy on the saturation matrix, and (c) a clear caveat about what the revision does not fix.

## Latest Context Snapshot
- **Research Topic:** flash-attention-4-whitebox-runtime-model
- **Topic Workspace:** <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model
- **Effective Topic Actor:** operator (ready)
- **Relevant records checked:**
  - `experiment-result-summary-bottleneck-sat-20260706` (ready)
  - `analysis-finding-bottleneck-sat-20260706` (ready)
  - `pipeline-terminal-report-bottleneck-sat-20260706` (ready)
- **Prompt context vs durable context:** Matches. The user asks for deeper analysis of the same saturation result.
- **Route:** Continue with `isomer-deepsci-analysis` focused slices.

## Resource Envelope
- **Device:** B200 GPU on cuda:0 (same as parent experiment).
- **Runtime:** Python 3.11 in topic Pixi env; `flash_attn.cute` and `ncu` available.
- **Wall-clock budget:** <30 min for all slices (no new NCU profiling; pure predictor diagnostics and counterfactuals).
- **Storage:** Outputs under the existing operation set.
- **Blockers:** None.
