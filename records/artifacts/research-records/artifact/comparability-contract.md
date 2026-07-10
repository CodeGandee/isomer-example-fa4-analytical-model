<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/handoff/comparability-contract/v2
schema_ref: isomer:deepsci/record-format/schema/handoff/comparability-contract/v2
payload_digest: sha256:4aaf60597384e163f183e10966bf2f67aad65d7547906c105caa77d4c9a8c084
-->
# Comparability Contract: FlashAttention-4 Roofline Baseline for B200

Comparability contract for the FlashAttention-4 paper roofline model reproduced and extended for NVIDIA B200.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-idea, isomer-deepsci-experiment, isomer-deepsci-analysis, isomer-deepsci-decision",
    "placeholder": "<COMPARABILITY_CONTRACT>",
    "producer": "isomer-deepsci-baseline",
    "skill": "isomer-deepsci-baseline"
  },
  "sections": {
    "comparator_identity": {
      "baseline_id": "fa4-paper-roofline-b200",
      "baseline_variant_id": "default",
      "comparator_name": "FlashAttention-4 Paper Roofline Model reproduced and extended for NVIDIA B200",
      "local_repository_path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/extern/flash-attention",
      "provenance": "Seed model from FA4 paper roofline (MMA, shared-memory traffic, exponential unit); extended with B200 Blackwell parameters and calibration plan.",
      "source_commit": "002cce0",
      "source_paper": "arXiv 2603.05451v1 (FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling)",
      "source_repository": "https://github.com/Dao-AILab/flash-attention"
    },
    "deviations_and_caveats": [
      "The FA4 paper roofline is a seed model; B200-specific terms (L2/HBM bandwidth, TMA latency, occupancy, TMEM) will be added during reproduction/extension.",
      "Exact sustained HBM bandwidth and L2 transaction behavior on B200 are not yet measured; calibration constants will be derived from a disjoint calibration set.",
      "FA4 default tile sizes and occupancy per precision are assumptions until measured or read from the official repository source.",
      "The numeric accuracy target (MAPE <= 25%) is a proposed threshold pending operator approval.",
      "Backward pass and multi-GPU execution are explicitly out of scope."
    ],
    "handoff": {
      "downstream_use": "The accepted comparator and metric contract anchor all later model ideas, experiments, analyses, and decision gates.",
      "next_route": "isomer-deepsci-idea"
    },
    "metric_contract": {
      "primary_metric": {
        "derivation": "Mean Absolute Percentage Error of predicted_runtime_ms versus measured_runtime_ms on the held-out validation set.",
        "direction": "minimize",
        "metric_id": "held_out_mape_predicted_runtime_ms"
      },
      "required_metrics": [
        {
          "direction": "minimize",
          "metric_id": "held_out_mape_predicted_runtime_ms"
        },
        {
          "direction": "minimize",
          "metric_id": "max_absolute_percentage_error"
        },
        {
          "direction": "maximize",
          "metric_id": "pct_validation_configs_within_30_pct_abs_error"
        },
        {
          "direction": "maximize",
          "metric_id": "bottleneck_label_accuracy"
        }
      ],
      "supplementary_metrics": [
        "per-stage_residual",
        "ncu_counter_trend_correlation"
      ],
      "useful_improvement_threshold": "Held-out MAPE <= 25%; >= 75% of validation configs within 30% absolute error; >= 75% bottleneck-label accuracy. Subsequent models should reduce MAPE by >= 5 percentage points or improve bottleneck accuracy by >= 10 percentage points."
    },
    "task_and_data_contract": {
      "dataset": "Synthetic configuration matrix drawn from the FlashAttention-4 paper and official repository benchmark scripts: batch, heads, sequence length, head dimension, causal/non-causal mask, precision.",
      "direct_comparison_limits": "Measured runtime may only be used for calibration on the calibration split and for validation on the held-out split; it must never be an input to the prediction for a query input.",
      "evaluation_path": "Predicted runtime in milliseconds per input configuration; compare against measured B200 kernel runtime and NCU counter trends collected from disjoint validation inputs.",
      "expected_outputs": [
        "predicted_runtime_ms per (B, H, S, D, causal, precision)",
        "predicted dominant bottleneck label",
        "predicted NCU counter trends (Tensor Core utilization, L2 transactions, shared-memory accesses)"
      ],
      "split": "Calibration set (~20%) for hardware constants; held-out validation set (~20%) for accuracy; prediction-query inputs must be disjoint from both.",
      "task": "White-box forward-pass runtime predictor for Flash Attention 4 on a single NVIDIA B200 across BF16/FP16/FP8/FP4 precisions, without executing the queried kernel."
    },
    "verdict": "trusted with caveats"
  },
  "status": "ready",
  "summary": "Comparability contract for the FlashAttention-4 paper roofline model reproduced and extended for NVIDIA B200.",
  "title": "Comparability Contract: FlashAttention-4 Roofline Baseline for B200"
}
```