# Evaluation Contract

## Task

Build a white-box math model that predicts Flash Attention 4 **forward-pass** kernel runtime in milliseconds from an input configuration, for a single NVIDIA B200 GPU, across BF16/FP16/FP8/FP4 precisions. The model must follow the GPU's internal execution model and identify bottlenecks without executing the kernel for the queried input.

## Dataset / Benchmark

A synthetic configuration matrix drawn from the FlashAttention-4 paper and the official repository benchmark scripts:

- batch size ∈ {1, 2, 4, 8}
- number of heads ∈ {16, 32, 64}
- sequence length ∈ {1k, 2k, 4k, 8k, 16k, 32k, 64k, 128k}
- head dimension ∈ {64, 128}
- mask mode: causal and non-causal
- precision ∈ {BF16, FP16, FP8, FP4}

The matrix is split into:

- **Calibration set** (~20% of configurations): used to fit or confirm hardware constants (effective SMEM bandwidth, TMA latency, exponential-emulation fraction).
- **Held-out validation set** (~20% of configurations): used to report accuracy; must be disjoint from calibration.
- **Prediction-query inputs**: any configuration submitted after the model is locked; must not appear in calibration or validation.

## Official Evaluation Path

1. Generate `predicted_runtime_ms` for every held-out configuration from the white-box model alone.
2. Measure actual runtime on the host B200 using the official Flash Attention repository benchmark scripts.
3. Collect Nsight Compute (NCU) counter traces for a representative subset and compare predicted L2 transactions, shared-memory accesses, and Tensor Core utilization trends.
4. Identify the predicted dominant bottleneck per configuration and compare with NCU evidence.

## Primary Metric

**Mean Absolute Percentage Error (MAPE)** of `predicted_runtime_ms` on the held-out validation set.

```
MAPE = mean(|predicted - measured| / measured) * 100%
```

Direction: minimize.

## Secondary Metrics

- Max absolute percentage error on the validation set.
- Per-stage residual (MMA, SMEM, exponential, TMA/TMEM, storeback).
- Pearson correlation between predicted and measured NCU counter trends.
- Bottleneck-label accuracy: fraction of configurations where the predicted dominant stage matches NCU/perf-counter evidence.

## Fair-Comparison Rule

- No model may use the measured runtime of a target input to predict that input.
- Calibration constants must be derived only from the disjoint calibration set.
- NCU validation runs must occur after predictions are recorded, not before.
- All compared models use the same B200 clock assumption (peak SM clock 1,965 MHz unless a sustained-clock contract is recorded).
- A pure black-box regression is not an acceptable primary model, but may be used as a leakage-check or sanity comparator if its results are clearly separated.

## Useful-Improvement Threshold

A baseline white-box model is considered useful if:

- Held-out MAPE ≤ 25% over the validation matrix.
- At least 75% of validation configurations have an absolute percentage error ≤ 30%.
- The predicted dominant bottleneck matches NCU evidence in at least 75% of configurations where a clear bottleneck can be identified.

A subsequent improved model should reduce MAPE by at least 5 percentage points or improve bottleneck-label accuracy by at least 10 percentage points to justify a new experiment cycle.

## Evidence

- Topic Workspace: `intent/src/topic-overview.md`, `intent/src/topic-env-gate.md`, `actors/operator/host-b200-spec.md`.
- Literature: arXiv 2603.05451v1 (FlashAttention-4), arXiv 2512.02189v1 (Blackwell microbenchmarks), arXiv 2605.04178v1 (analytical GPU modeling).
- Repository: official Flash Attention clone at `repos/extern/flash-attention`.

## Known Ambiguities

1. **Exact B200 sustained HBM bandwidth and L2 transaction behavior** are not captured in the host spec. The baseline model must measure or assume values and document them.
2. **FA4 default tile sizes and occupancy per precision** are not fully stated in the paper. The baseline model must extract them from the local source or propose values.
3. **Numeric accuracy target** in this contract is a proposal; the operator can approve, tighten, or waive it.

## Decision Impact

This contract is sufficient to route to `isomer-deepsci-baseline`. If the operator rejects the proposed MAPE threshold or the calibration/validation split, the next route should be `isomer-deepsci-decision` before baseline construction begins.
