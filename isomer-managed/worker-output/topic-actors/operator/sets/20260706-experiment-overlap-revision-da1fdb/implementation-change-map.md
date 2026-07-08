# Implementation Change Map

## Changed file
- `repos/topic-main/src/fa4_b200_predictor/predictor.py`

## Mechanism
Added an `overlap_frac` parameter to the `Predictor` class and to the `combined_predictor` factory. The predictor now computes an effective memory time:

```python
mem_eff = mem_t * (1.0 - overlap_frac)
runtime_ms = (max(mma_t, mufu_t, mem_eff) + launch_overhead_us) / 1000.0
```

and scales per-stage memory times (`hbm`, `l2`, `smem`, `tma`) by `(1 - overlap_frac)` before selecting the bottleneck label.

## Why this change
The parent analysis (`analysis-finding-tma-overlap-revision-20260706`) showed that the pure `max(compute, memory)` roofline over-states memory dominance because async TMA copy traffic overlaps with MMA warps on B200.

## Risk and guard
- Default `overlap_frac=0.0` preserves backward compatibility with the existing combined predictor.
- Existing unit tests pass after the change.
- The parameter is bounded [0, 1] by construction (caller passes a float; values outside this range are not enforced but are semantically invalid).
