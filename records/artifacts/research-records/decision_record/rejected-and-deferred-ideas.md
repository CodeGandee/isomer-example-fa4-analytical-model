<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/decision/rejected-and-deferred-ideas/v1
schema_ref: isomer:deepsci/record-format/schema/decision/rejected-and-deferred-ideas/v1
payload_digest: sha256:427ca8b6b2c8af0a88958449deabadebf90a879733ac9f8f239d2f362424db33
-->
# Rejected and Deferred Ideas: FlashAttention-4 B200 Runtime Model Idea Pass

Rejected and deferred ideas for the FlashAttention-4 B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "future idea passes and decision records",
    "placeholder": "\u003cREJECTED_AND_DEFERRED_IDEAS\u003e",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "deferred": [
      {
        "family": "model",
        "id": "R5",
        "one_liner": "Symbolic regression over white-box features.",
        "reason": "Useful fallback if pure analytical terms fail, but risks non-interpretable terms that violate the white-box constraint; defer until after C1 ablations."
      },
      {
        "family": "infrastructure",
        "id": "R8",
        "one_liner": "Synthetic B200 microbenchmark suite for constant calibration.",
        "reason": "High value for future reproducibility but not needed for the first falsifiable hypothesis; can be built in parallel during experiment."
      }
    ],
    "folded": [
      {
        "family": "measurement",
        "id": "R6",
        "one_liner": "NCU counter trend collection and bottleneck classifier.",
        "reason": "Folded into C1 as validation instrumentation; not a separate route."
      }
    ],
    "rejected": [
      {
        "family": "objective",
        "id": "R7",
        "one_liner": "Change primary metric from MAPE to log-MAE.",
        "reason": "Evaluation contract and comparability contract fix the primary metric as held_out_mape_predicted_runtime_ms; changing it would break comparability."
      }
    ]
  },
  "status": "ready",
  "summary": "Rejected and deferred ideas for the FlashAttention-4 B200 runtime model idea pass.",
  "title": "Rejected and Deferred Ideas: FlashAttention-4 B200 Runtime Model Idea Pass"
}
```