# Experiment Result: Inner-GPU Model Calibration

## Design
- **Hardware:** NVIDIA B200 (`cuda:0`), peak SM clock 1,965 MHz.
- **Workload:** `flash_attn_func` from `flash_attn.cute`, forward pass.
- **Calibration set:** 16 configs (batch=2, heads=16, seqlen ∈ {1024, 4096, 8192}, head_dim ∈ {64, 128}, causal ∈ {True, False}, precision ∈ {fp16, fp8}).
- **Validation set:** 8 configs from the same matrix, stratified random split.
- **Metric:** mean absolute percentage error (MAPE) of predicted runtime vs measured median runtime.

## Raw result

| Predictor | Calibration MAPE | Validation MAPE |
|---|---|---|
| Inner-GPU model (refined) | 18.26 % | 21.39 % |
| Baseline white-box | — | 56.23 % |
| Improved white-box | — | 14.89 % |

## Fitted parameters

```json
{
  "mma_throughput_per_sm_per_clock_fp16": 3172.84,
  "mma_throughput_per_sm_per_clock_fp8": 6345.69,
  "operand_collector_efficiency": 0.9437,
  "l1_miss_rate": 0.0926,
  "l2_miss_rate": 0.3072,
  "hbm_row_buffer_hit_rate": 0.65
}
```

## Status
`inconclusive / partially-supported`. The inner-GPU model beats the coarse baseline but does not yet outperform the existing improved predictor. The decomposition is mechanistically sound and identifies the tensor-core bottleneck correctly; the remaining error is dominated by missing launch/tile overhead and coarse causal scaling.

## Files
- `measurements.csv` — per-config measured runtimes.
- `predictions.csv` — per-config predictions for inner, baseline, and improved models.
- `inner_model_spec.json` — fitted hardware parameters.
- `summary.json` — numeric summary.
