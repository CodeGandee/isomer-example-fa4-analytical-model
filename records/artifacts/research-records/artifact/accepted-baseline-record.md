<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/handoff/accepted-baseline-record/v1
schema_ref: isomer:deepsci/record-format/schema/handoff/accepted-baseline-record/v1
payload_digest: sha256:04aee43db465bca1dd833129310b39e1914b160538b58b6287240c426d49a5b0
-->
# Accepted Baseline Record: FlashAttention-4 Roofline Baseline for B200

Accepted baseline record for the FlashAttention-4 paper roofline model on NVIDIA B200.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-idea, isomer-deepsci-experiment, isomer-deepsci-analysis, isomer-deepsci-decision",
    "placeholder": "\u003cACCEPTED_BASELINE_RECORD\u003e",
    "producer": "isomer-deepsci-baseline",
    "skill": "isomer-deepsci-baseline"
  },
  "sections": {
    "acceptance": {
      "acceptance_target": "comparison-ready",
      "accepted": true,
      "accepted_at": "2026-07-04T12:41:52Z",
      "accepted_by": "isomer-deepsci-baseline",
      "reason": "The FlashAttention-4 paper roofline model is the recommended anchor comparator. Source identity (paper arXiv 2603.05451v1 and official repository commit 002cce0) and the B200 hardware context are verified. The evaluation contract and baseline shortlist provide a complete metric contract. Caveats are explicit and do not change comparison meaning.",
      "route": "reproduce / extend"
    },
    "baseline_identity": {
      "baseline_id": "fa4-paper-roofline-b200",
      "baseline_kind": "paper-roofline-reproduced-extended",
      "baseline_variant_id": "default",
      "comparator_name": "FlashAttention-4 Paper Roofline Model reproduced and extended for NVIDIA B200"
    },
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
    "dataset": "Synthetic configuration matrix drawn from the FlashAttention-4 paper and official repository benchmark scripts.",
    "default_variant_id": "default",
    "environment": {
      "compute_capability": "10.0",
      "cuda_runtime": "13.1",
      "driver_version": "590.48.01",
      "gpu": "NVIDIA B200",
      "host_path": "<NCU_PATH>",
      "memory_clock_mhz": 3996,
      "ncu_version": "2025.4.1.0",
      "peak_sm_clock_mhz": 1965
    },
    "metrics_summary": {
      "direction": "minimize",
      "primary": "held_out_mape_predicted_runtime_ms",
      "required_metrics": [
        "held_out_mape_predicted_runtime_ms",
        "max_absolute_percentage_error",
        "pct_validation_configs_within_30_pct_abs_error",
        "bottleneck_label_accuracy"
      ],
      "supplementary_metrics": [
        "per-stage_residual",
        "ncu_counter_trend_correlation"
      ],
      "threshold": "MAPE \u003c= 25%; \u003e= 75% of validation configs within 30% absolute error; \u003e= 75% bottleneck-label accuracy"
    },
    "primary_metric": "held_out_mape_predicted_runtime_ms (minimize)",
    "source": {
      "local_repository_path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/extern/flash-attention",
      "paper": "arXiv 2603.05451v1",
      "repository_commit": "002cce0",
      "repository_url": "https://github.com/Dao-AILab/flash-attention"
    },
    "summary": "Accepted baseline comparator for the Flash Attention 4 white-box B200 runtime model. The comparator is the FA4 paper roofline reproduced and extended for B200, with explicit calibration plan, acceptance criteria, and caveats.",
    "task": "White-box forward-pass runtime predictor for Flash Attention 4 on a single NVIDIA B200 across BF16/FP16/FP8/FP4 precisions, without executing the queried kernel.",
    "waiver_or_blocker": "none"
  },
  "status": "ready",
  "summary": "Accepted baseline record for the FlashAttention-4 paper roofline model on NVIDIA B200.",
  "title": "Accepted Baseline Record: FlashAttention-4 Roofline Baseline for B200"
}
```