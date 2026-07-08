# Scout Memory Reuse Note

## Prior Knowledge Reused

The following durable workspace context was reused before any broad external discovery:

1. **Topic intent and gates**: `intent/src/topic-overview.md`, `intent/src/topic-env-gate.md`, `intent/src/actor-definitions.md`, and `intent/derived/actor-env-gates.md`. These fix the scope (forward pass, B200, BF16/FP16/FP8/FP4, single GPU), the environment readiness (Python 3.11, NumPy/SymPy/SciPy, `ncu` 2025.4.1, official Flash Attention repo), and the success criteria.

2. **Host hardware facts**: `actors/operator/host-b200-spec.md` and `repos/topic-main/host-b200-spec.md` capture the host B200 driver, CUDA/runtime version, compute capability 10.0, peak SM clock (1,965 MHz), and `ncu` availability.

3. **Workspace runtime state**: the topic reset checkpoint and workspace summary confirm the topic is active, the operator actor is materialized, and `repos/extern/flash-attention` is present.

4. **No prior scout artifacts**: a record search for `<SCOUT_CONTEXT_BRIEF>`, `<EVALUATION_CONTRACT>`, and other scout placeholders returned no existing records for this topic, so no earlier scout conclusions are being overwritten.

## What External Discovery Was Needed

Only a small, targeted inspection was required to settle route-changing questions:

- Confirm that the official Flash Attention repository contains FA4-related CuTe-DSL code and benchmark scripts.
- Retrieve the FlashAttention-4 paper to extract the forward-pass roofline formulas and B200 hardware throughput numbers.
- Retrieve a Blackwell microbenchmark paper to ground the shared-memory and exponential-unit throughput claims.

No exhaustive literature survey was needed because the topic intent already defines the algorithm source, hardware target, and modeling philosophy.

## Reuse Implications

The next route can rely on the existing topic intent and gates. Baseline construction should not re-derive the high-level scope or re-discover the B200 host; it should focus on converting the FA4 paper's roofline analysis into a runnable Python predictor and defining the calibration/validation split.
