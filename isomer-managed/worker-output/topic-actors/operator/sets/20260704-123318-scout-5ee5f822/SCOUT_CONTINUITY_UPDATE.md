# Scout Continuity Update

## Route Outcome

Scout concluded with a clear route: **proceed to `isomer-deepsci-baseline`**.

## Reusable Conclusions

1. **Hardware target is fixed**: NVIDIA B200, single GPU, compute capability 10.0, peak SM clock 1,965 MHz, driver 590.48.01, `ncu` 2025.4.1. Do not re-derive the host GPU during baseline work.

2. **Algorithm source is fixed**: official Flash Attention repository (`repos/extern/flash-attention`) and the FlashAttention-4 paper (arXiv 2603.05451v1). The forward-pass roofline formulas in the paper are the starting point for the baseline model.

3. **No existing white-box predictor**: local records and the official repository contain no pre-built white-box FA4 runtime model. Baseline construction must start from the paper's formulas and the B200 host spec.

4. **Key hardware parameters from literature**:
   - BF16 MMA throughput: 8192 ops/clock/SM on B200 (derived from 2.25 PFLOPS / 1.85 GHz / 148 SMs).
   - Shared-memory read throughput: 128 bytes/clock/SM.
   - Exponential (MUFU) throughput: 16 ops/clock/SM on B200/GB200.
   - TMEM: 256 KB/SM; 128×128 MMA tiles; fully asynchronous MMA writes to TMEM.

5. **Evaluation contract proposal**: held-out MAPE ≤ 25%, ≥ 75% of configurations within 30% absolute error, and ≥ 75% bottleneck-label accuracy. Calibration and validation sets must be disjoint and disjoint from prediction-query inputs.

## Residual Lessons for Baseline

- The baseline model should first reproduce the paper's forward-pass cycle formulas (MMA, SMEM, exponential) and then add B200-specific terms for TMA latency, TMEM allocation, occupancy limits, and precision-specific scheduling.
- Exact tile sizes, warpgroup counts, and 2-CTA mode usage must be extracted from the local CuTe-DSL source or measured; the paper does not state them precisely enough for a full input-shape predictor.
- Probabilistic sub-models for cache hit/miss, shared-memory bank conflicts, occupancy jitter, and TMA latency variance are required by the topic intent and should be documented explicitly.

## Blockers to Watch

- If the operator rejects the proposed accuracy threshold or split, open a Decision Record before baseline construction continues.
- If source-archaeology fails to bound FA4 tile/occupancy defaults, return to scout or open a blocker gate.

## Files to Reuse

All scout outputs live in the operation set:

`<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/actors/operator/isomer-managed/worker-output/topic-actors/operator/sets/20260704-123318-scout-5ee5f822/`

- `SCOUT_CONTEXT_BRIEF.md`
- `SCOUT_MEMORY_REUSE_NOTE.md`
- `SCOUT_MINIMUM_UNKNOWNS.md`
- `SCOUT_DISCOVERY_LEDGER.md`
- `LITERATURE_SCOUTING_REPORT.md`
- `EVALUATION_CONTRACT.md`
- `BASELINE_SHORTLIST.md`
- `NEXT_ROUTE_DECISION.md`
- `SCOUT_CONTINUITY_UPDATE.md` (this file)
