<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/handoff/objective-contract/v1
schema_ref: isomer:deepsci/record-format/schema/handoff/objective-contract/v1
payload_digest: sha256:3494aeefd6535a3f0a1e7c1a4b5e59930668f52ed43edd5db7be2b981f3b6ca4
-->
# Objective Contract: FlashAttention-4 White-Box B200 Runtime Model Idea Pass

Objective contract for the Flash Attention 4 white-box B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "candidate generation and selection",
    "placeholder": "\u003cOBJECTIVE_CONTRACT\u003e",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "contribution_frame": "Analytical-model contribution: identify which omitted white-box terms (tile occupancy, TMA/L2 effective bandwidth, precision-specific MMA throughput, exponential emulation) are the dominant correction to the FA4 paper roofline on B200.",
    "exit_rule": "Promote to experiment when one falsifiable hypothesis has a concrete code-level plan, falsification experiment, abandonment condition, and expected metric boundary; otherwise record a blocker or route back to baseline/scout.",
    "false_progress_signals": [
      "Improving calibration-set fit while held-out validation MAPE stagnates (overfitting constants to calibration).",
      "Reducing MAPE on a narrow precision or sequence-length slice while overall held-out MAPE worsens.",
      "Better bottleneck-label accuracy on synthetic labels that do not match measured NCU counters.",
      "Lower residual on configurations already dominated by the baseline; no improvement on the error-dominated regime."
    ],
    "hard_constraints": [
      "No measured runtime of a query input may enter the predictor; calibration constants must come from a disjoint calibration split.",
      "Predictions must be produced without executing the queried kernel.",
      "Scope is single-GPU forward pass only; backward pass and multi-GPU are out of scope.",
      "Comparator is the accepted FA4 paper roofline baseline reproduced and extended for B200; a new route must improve it by \u003e= 5 percentage points MAPE or \u003e= 10 percentage points bottleneck accuracy.",
      "All constants must remain white-box interpretable; black-box curve fitting of query inputs is prohibited."
    ],
    "real_objective": "Build a white-box forward-pass runtime predictor for Flash Attention 4 on a single NVIDIA B200 across BF16/FP16/FP8/FP4 precisions that beats the reproduced FlashAttention-4 paper roofline baseline on held-out MAPE of predicted_runtime_ms without executing the queried kernel.",
    "scoreboard_metric": {
      "derivation": "Mean Absolute Percentage Error of predicted_runtime_ms versus measured_runtime_ms on the held-out validation set.",
      "direction": "minimize",
      "metric_id": "held_out_mape_predicted_runtime_ms"
    },
    "trusted_proxy_metrics": [
      {
        "direction": "maximize",
        "metric_id": "pct_validation_configs_within_30_pct_abs_error",
        "why_trusted": "Directly tied to user-facing reliability of the predictor; threshold is \u003e= 75%."
      },
      {
        "direction": "maximize",
        "metric_id": "bottleneck_label_accuracy",
        "why_trusted": "Forces the model to encode the right dominant hardware bottleneck, not just curve fit."
      },
      {
        "direction": "minimize",
        "metric_id": "max_absolute_percentage_error",
        "why_trusted": "Captures worst-case failure modes that MAPE can hide."
      }
    ]
  },
  "status": "ready",
  "summary": "Objective contract for the Flash Attention 4 white-box B200 runtime model idea pass.",
  "title": "Objective Contract: FlashAttention-4 White-Box B200 Runtime Model Idea Pass"
}
```