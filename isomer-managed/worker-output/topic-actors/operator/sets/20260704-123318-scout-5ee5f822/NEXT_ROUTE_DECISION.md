# Next Route Decision

## Decision

**Route to `isomer-deepsci-baseline`.**

## Evidence Basis

- The Topic Workspace intent (`intent/src/topic-overview.md`) and environment gates (`intent/src/topic-env-gate.md`, `intent/derived/actor-env-gates.md`) already define the task scope, hardware target (NVIDIA B200), precision set (BF16/FP16/FP8/FP4), and success criteria.
- The host B200 specification is captured (`actors/operator/host-b200-spec.md`) and `ncu` 2025.4.1 is available for validation.
- The official Flash Attention repository is present locally (`repos/extern/flash-attention`) for algorithm and benchmark details.
- The FlashAttention-4 paper (arXiv 2603.05451v1) provides a usable forward-pass roofline analysis that can be reproduced as the first white-box predictor.
- No existing white-box Flash Attention 4 runtime predictor was found in local records or the official repository, so baseline construction is the appropriate next step.
- Residual unknowns (exact B200 sustained bandwidth, FA4 tile/occupancy defaults per precision, numeric accuracy threshold) affect model construction but do not block routing.

## Rejected Alternatives

- `isomer-deepsci-idea`: premature because no durable baseline model or comparator exists yet.
- `isomer-deepsci-decision`: unnecessary unless the operator rejects the proposed evaluation contract; the current frame is clear enough for baseline work.
- Blocker: no blocker is justified; all required inputs for a baseline attempt are available.

## Conditions for Revisiting Scout

Re-enter scout if any of the following occurs during baseline work:

- The operator rejects the proposed MAPE threshold or calibration/validation split.
- The FA4 tile/occupancy details cannot be sourced from the local repository or measured, making the model structure unbounded.
- A published white-box FA4 predictor is discovered that would change the comparator strategy.

## Handoff

The baseline stage should use the evaluation contract and baseline shortlist in this directory as its starting frame.
