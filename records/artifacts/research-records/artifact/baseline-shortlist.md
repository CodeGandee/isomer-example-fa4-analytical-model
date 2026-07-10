<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/handoff/baseline-shortlist/v2
schema_ref: isomer:deepsci/record-format/schema/handoff/baseline-shortlist/v2
payload_digest: sha256:e34eeee60b92b8bbb045bfe6e431e99494cf14d27e22adc446255a7a5b72c282
-->
# Baseline Shortlist

Comparator candidates for the Flash Attention 4 white-box runtime model on NVIDIA B200.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-baseline, isomer-deepsci-idea, isomer-deepsci-decision",
    "placeholder": "<BASELINE_SHORTLIST>",
    "producer": "isomer-deepsci-scout",
    "skill": "isomer-deepsci-scout"
  },
  "sections": {
    "anchor_comparator": {
      "downstream_value": "First credible white-box model and foundation for refinement.",
      "expected_cost": "Low-medium",
      "implementation": "Must be reproduced from paper into Python/SymPy predictor in repos/topic-main.",
      "main_risk": "Ignores L2/HBM, TMA latency, occupancy; needs calibration.",
      "metric_fit": "Direct forward-pass roofline on Blackwell (MMA, SMEM, exponential).",
      "name": "FlashAttention-4 Paper Roofline Model",
      "provenance": "arXiv 2603.05451v1",
      "route": "reproduce / extend"
    },
    "recommended_next_action": "Route to isomer-deepsci-baseline and reproduce the FA4 paper roofline model, then extend with B200 memory/occupancy terms and validate against measured B200 runtime.",
    "rejected": [
      {
        "name": "cuDNN 9.13 / Triton Attention",
        "reason": "Closed-source or different kernels; only indirect plausibility checks."
      },
      {
        "name": "SageAttention family",
        "reason": "Targets consumer GPUs and quantization outside B200 datacenter scope."
      }
    ],
    "sanity_checks": [
      {
        "downstream_value": "Shows improvement over crude bound.",
        "expected_cost": "Very low",
        "implementation": "Trivial Python implementation.",
        "main_risk": "Too weak for final comparator.",
        "metric_fit": "Lower-bound baseline the white-box model should beat.",
        "name": "Naive Max(Compute, Memory) Roofline",
        "provenance": "Standard GPU roofline",
        "route": "attach"
      },
      {
        "downstream_value": "Required for calibration and validation.",
        "expected_cost": "Medium",
        "implementation": "Build and run repo benchmark scripts; collect NCU.",
        "main_risk": "Direct measurement leakage if used for predictions.",
        "metric_fit": "Target variable, not a predictor.",
        "name": "Measured B200 Kernel Runtime",
        "provenance": "Host B200 + official flash-attention benchmarks",
        "route": "import as ground truth only"
      }
    ]
  },
  "status": "ready",
  "summary": "Comparator candidates for the Flash Attention 4 white-box runtime model on NVIDIA B200.",
  "title": "Baseline Shortlist"
}
```