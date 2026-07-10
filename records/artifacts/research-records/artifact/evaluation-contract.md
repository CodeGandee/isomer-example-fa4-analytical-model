<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/handoff/evaluation-contract/v2
schema_ref: isomer:deepsci/record-format/schema/handoff/evaluation-contract/v2
payload_digest: sha256:e68a62316d465a4679c5106006e50c9a355269e1ec6610700bbe45586d4355e1
-->
# Evaluation Contract: Flash Attention 4 White-Box Runtime Model

Contract for predicting Flash Attention 4 forward-pass runtime on NVIDIA B200 without executing the queried kernel.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-baseline, isomer-deepsci-idea, isomer-deepsci-experiment, isomer-deepsci-analysis",
    "placeholder": "<EVALUATION_CONTRACT>",
    "producer": "isomer-deepsci-scout, later refined by isomer-deepsci-baseline or isomer-deepsci-experiment",
    "skill": "isomer-deepsci-scout"
  },
  "sections": {
    "ambiguities": [
      "Exact B200 sustained HBM bandwidth and L2 transaction behavior",
      "FA4 default tile sizes and occupancy per precision",
      "Numeric accuracy target is a proposal pending operator approval"
    ],
    "dataset": "Synthetic configuration matrix drawn from the FlashAttention-4 paper and official repository benchmark scripts: batch, heads, sequence length, head dimension, causal/non-causal mask, precision.",
    "evidence": [
      "intent/src/topic-overview.md",
      "intent/src/topic-env-gate.md",
      "actors/operator/host-b200-spec.md",
      "arXiv 2603.05451v1",
      "arXiv 2512.02189v1",
      "arXiv 2605.04178v1",
      "repos/extern/flash-attention"
    ],
    "fair_comparison_rule": "No model may use the measured runtime of a target input. Calibration constants from disjoint calibration set only. NCU validation after predictions. Same B200 clock assumptions unless updated.",
    "primary_metric": "Mean Absolute Percentage Error (MAPE) of predicted_runtime_ms on held-out validation set; minimize.",
    "secondary_metrics": [
      "Max absolute percentage error",
      "Per-stage residual",
      "NCU counter trend correlation",
      "Bottleneck-label accuracy"
    ],
    "split": "Calibration set (~20%) for hardware constants; held-out validation set (~20%) for accuracy; prediction-query inputs must be disjoint from both.",
    "task": "Build a white-box math model that predicts Flash Attention 4 forward-pass kernel runtime in milliseconds from an input configuration for a single NVIDIA B200 GPU across BF16/FP16/FP8/FP4 precisions.",
    "useful_improvement_threshold": "Held-out MAPE <= 25%; >= 75% of validation configs within 30% absolute error; >= 75% bottleneck-label accuracy. Subsequent models should reduce MAPE by >= 5 percentage points or improve bottleneck accuracy by >= 10 percentage points."
  },
  "status": "ready",
  "summary": "Contract for predicting Flash Attention 4 forward-pass runtime on NVIDIA B200 without executing the queried kernel.",
  "title": "Evaluation Contract: Flash Attention 4 White-Box Runtime Model"
}
```