<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/handoff/baseline-payload-record/v2
schema_ref: isomer:deepsci/record-format/schema/handoff/baseline-payload-record/v2
payload_digest: sha256:d51d3c8e6bd5f7ca95776aabb2adfd9decdff6bec5bc3ed0cccf3fa15c0f46d3
-->
# Baseline Payload Record: FlashAttention-4 Roofline Baseline for B200

Baseline payload record for the accepted FlashAttention-4 roofline comparator.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-idea, isomer-deepsci-experiment, isomer-deepsci-analysis, isomer-deepsci-decision",
    "placeholder": "<BASELINE_PAYLOAD_RECORD>",
    "producer": "isomer-deepsci-baseline",
    "skill": "isomer-deepsci-baseline"
  },
  "sections": {
    "baseline_id": "fa4-paper-roofline-b200",
    "baseline_kind": "paper-roofline-reproduced-extended",
    "baseline_variants": [
      {
        "status": "accepted",
        "variant_id": "default",
        "variant_name": "FA4 paper roofline extended with B200 memory/occupancy/TMA terms"
      },
      {
        "status": "attached sanity check",
        "variant_id": "naive-roofline",
        "variant_name": "Naive max(compute, memory) roofline sanity check"
      }
    ],
    "caveats": [
      "B200-specific terms (L2/HBM bandwidth, TMA latency, occupancy, TMEM) are extension items to be implemented in downstream stages.",
      "Calibration constants must be derived from a disjoint calibration set only.",
      "The 25% MAPE threshold is proposed pending operator approval."
    ],
    "dataset": "Synthetic configuration matrix drawn from the FlashAttention-4 paper and official repository benchmark scripts.",
    "default_variant_id": "default",
    "environment": {
      "compute_capability": "10.0",
      "cuda_runtime": "13.1",
      "driver_version": "590.48.01",
      "gpu": "NVIDIA B200",
      "memory_clock_mhz": 3996,
      "ncu_version": "2025.4.1.0",
      "peak_sm_clock_mhz": 1965
    },
    "kind": "accepted_baseline",
    "metrics_summary": {
      "direction": "minimize",
      "primary": "held_out_mape_predicted_runtime_ms",
      "required_metrics": [
        "held_out_mape_predicted_runtime_ms",
        "max_absolute_percentage_error",
        "pct_validation_configs_within_30_pct_abs_error",
        "bottleneck_label_accuracy"
      ],
      "threshold": "MAPE <= 25%; >= 75% of validation configs within 30% absolute error; >= 75% bottleneck-label accuracy"
    },
    "path_or_package_identity": "repos/extern/flash-attention @ 002cce0 + arXiv 2603.05451v1 + B200 host spec",
    "primary_metric": "held_out_mape_predicted_runtime_ms (minimize)",
    "source": {
      "paper": "arXiv 2603.05451v1",
      "repository_commit": "002cce0",
      "repository_url": "https://github.com/Dao-AILab/flash-attention"
    },
    "summary": "Handoff payload for the accepted baseline comparator and metric contract. Downstream stages must treat the FA4 paper roofline extended for B200 as the primary comparator and must not use measured runtime of query inputs as predictors.",
    "task": "White-box forward-pass runtime predictor for Flash Attention 4 on a single NVIDIA B200 across BF16/FP16/FP8/FP4 precisions, without executing the queried kernel."
  },
  "status": "ready",
  "summary": "Baseline payload record for the accepted FlashAttention-4 roofline comparator.",
  "title": "Baseline Payload Record: FlashAttention-4 Roofline Baseline for B200"
}
```