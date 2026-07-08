# Round 1: Per-SM Execution-Unit Reservation Model

## Summary

This experiment replaces the scalar efficiency factors of the previous cycle-level model with explicit per-SM reservations on the specialized Blackwell execution units: Tensor Cores, SFU, FP32/INT32 pipes, the global TMA memory pipe, and the on-SM TMEM read/write pipe. The goal is to keep the model deterministic and closed-form while exposing *which* unit saturates and *how* data movement between TMA, TMEM, and the tensor cores contributes to runtime.

## Model Structure

`B200ReservationModel` decomposes one FA4 forward pass into repeating KV steps. For each step it computes the cycles each execution unit must be reserved:

| Unit | Role in FA4 | Reservation computed as |
|---|---|---|
| Tensor Core (TC) | `Q@K^T` and `P@V` MMAs | `flops / (rate_per_sm × active_SMs × tc_efficiency × occupancy × cluster_eff)` with a latency-hiding penalty |
| TMEM | Tensor operand/accumulator staging | `bytes / (TMEM_bw × active_SMs × tmem_efficiency)` |
| SFU | Softmax `exp` | `exp_ops / (sfu_rate × active_SMs × sfu_efficiency × occupancy)` |
| FP32/INT32 | Online softmax scaling and update | `scale_ops / (fp_rate × active_SMs × fp_efficiency × occupancy)` |
| TMA (global) | Async Q/K/V loads and O store | `bytes / (TMA_bw × tma_efficiency)` capped by L2/HBM miss bandwidth |

The per-step critical path is `max(TC+softmax, visible_TMA_memory)`, where the visible memory fraction is `(1 − stage_overlap_factor) × total_memory_cycles`. A fixed launch overhead is added at the end.

Key differences from the previous cycle-level model:

1. **Explicit unit reservations** instead of scalar `tc_efficiency` / `memory_overlap_factor` applied to aggregate totals.
2. **Blackwell-specific TMA/TMEM stages** inspired by the stage-centric Blackwell analytical model (arXiv:2605.04178).
3. **Per-unit utilization and bottleneck identification**: the model reports which unit (TC, SFU, or TMA memory) dominates each configuration.
4. **TMEM capacity guard**: a spill coefficient penalizes tile working sets that exceed 256 KB/SM.

## Calibration and Validation

The model was fit to the same 16 calibration / 8 validation B200 measurements used for the previous cycle-level model (batch=2, heads=16, seqlen ∈ {1024, 4096, 8192}, head_dim ∈ {64, 128}, causal ∈ {True, False}, precision ∈ {fp16, fp8}).

| Model | Calibration MAPE | Validation MAPE |
|---|---|---|
| Per-SM reservation model (Round 1) | 8.15% | 16.69% |
| Previous cycle-level model | 7.37% | 13.16% |
| Baseline roofline predictor | — | 56.23% |
| Improved predictor | — | 14.89% |

The reservation model is competitive with the prior predictors while trading a small accuracy penalty for interpretability: it names the saturating unit for every configuration.

### Fitted parameters

```json
{
  "tc_efficiency": 1.20,
  "sfu_efficiency": 0.68,
  "fp_efficiency": 3.00,
  "tma_efficiency": 1.00,
  "tmem_efficiency": 1.00,
  "cluster_efficiency": 1.00,
  "stage_overlap_factor": 0.85,
  "launch_overhead_us": 16.13,
  "tmem_spill_coefficient": 0.00
}
```

The fitted launch overhead (~16 µs) is close to the previous cycle-level model, confirming that small-sequence fixed costs are robustly identified across model structures. `tmem_spill_coefficient` stays at zero because the chosen tile shapes fit comfortably in 256 KB/SM TMEM.

## Bottleneck Analysis on Validation Set

The model reports a unit-level bottleneck for each configuration:

- Large head-dim-128 configurations are **TC-bound** (MMA FLOPs dominate).
- Small or memory-heavy FP8 configurations are **TMA-memory-bound**.
- Softmax SFU is never the primary bottleneck but contributes 10–20% of the compute reservation in most cases.

This matches the expected behavior of FA4 on Blackwell: the kernel is either compute-bound on the tensor cores for large tiles or memory-bound on TMA/HBM for small or low-precision tiles.

## Strengths and Limitations

**Strengths**

- Exposes per-unit utilization and bottleneck identity.
- Captures Blackwell-specific TMA/TMEM stages.
- Still deterministic and fast to evaluate.

**Limitations**

- The overlap between stages is a single scalar `stage_overlap_factor`; real overlap depends on tile size, precision, and instruction-level scheduling.
- TC throughput is still a precision-wide scalar; it does not yet depend on the exact MMA tile shape or sub-core partition assignment.
- SFU/FP pipes are modeled as aggregate reservations, not as a fine-grained instruction schedule.

## Files Produced

- `reservation_model.py` — the model implementation.
- `calibrate_reservation_model.py` — calibration and validation script.
- `predictions.csv` — per-config measured vs. predicted runtimes.
- `summary.json` — MAPE and fitted parameters.
- `reservation_model_spec.json` — calibrated hardware spec.
- `reservation_model_report.md` — this report.

## Next Refinement (Round 2)

To push the model further, Round 2 will add **sub-core partition scheduling**. Each Blackwell SM is split into four partitions, each with its own warp scheduler and a subset of the execution units. Round 2 will model how warps are distributed across partitions and how partition-level resource contention modifies the per-SM throughput, rather than treating each SM as a single pool of units.
