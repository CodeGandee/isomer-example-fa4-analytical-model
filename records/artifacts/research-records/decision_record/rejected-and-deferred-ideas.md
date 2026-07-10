<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/decision/rejected-and-deferred-ideas/v2
schema_ref: isomer:deepsci/record-format/schema/decision/rejected-and-deferred-ideas/v2
payload_digest: sha256:dfa19bfa7c984366c8a0f479c7e6b58fbb61dad17dfc3621e3e57ec68ede600c
-->
# Rejected and Deferred Ideas: FlashAttention-4 B200 Runtime Model Idea Pass

Rejected and deferred ideas for the FlashAttention-4 B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "future idea passes and decision records",
    "placeholder": "<REJECTED_AND_DEFERRED_IDEAS>",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "deferred": [
      {
        "family": "model",
        "id": "R5",
        "reason": "Useful fallback if pure analytical terms fail, but risks non-interpretable terms that violate the white-box constraint; defer until after C1 ablations.",
        "summary": "Symbolic regression over white-box features."
      },
      {
        "family": "infrastructure",
        "id": "R8",
        "reason": "High value for future reproducibility but not needed for the first falsifiable hypothesis; can be built in parallel during experiment.",
        "summary": "Synthetic B200 microbenchmark suite for constant calibration."
      }
    ],
    "folded": [
      {
        "family": "measurement",
        "id": "R6",
        "reason": "Folded into C1 as validation instrumentation; not a separate route.",
        "summary": "NCU counter trend collection and bottleneck classifier."
      }
    ],
    "rejected": [
      {
        "family": "objective",
        "id": "R7",
        "reason": "Evaluation contract and comparability contract fix the primary metric as held_out_mape_predicted_runtime_ms; changing it would break comparability.",
        "summary": "Change primary metric from MAPE to log-MAE."
      }
    ]
  },
  "status": "ready",
  "summary": "Rejected and deferred ideas for the FlashAttention-4 B200 runtime model idea pass.",
  "title": "Rejected and Deferred Ideas: FlashAttention-4 B200 Runtime Model Idea Pass"
}
```