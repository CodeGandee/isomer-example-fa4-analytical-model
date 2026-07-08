<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/report/raw-idea-slate/v1
schema_ref: isomer:deepsci/record-format/schema/report/raw-idea-slate/v1
payload_digest: sha256:806a0b177c89568d5778cb56af67c3733f8289acb92aa1918b1c41f5f30613bd
-->
# Raw Idea Slate: FlashAttention-4 B200 Runtime Model Idea Pass

Raw idea slate for the FlashAttention-4 B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "candidate frontier filtering",
    "placeholder": "\u003cRAW_IDEA_SLATE\u003e",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "filter_notes": [
      "R7 rejected: metric contract is fixed by evaluation contract and comparability contract.",
      "R8 deferred: useful but can be built in parallel; not the first falsifiable hypothesis.",
      "R5 deferred: symbolic regression risks black-box terms; keep as fallback if pure analytical terms fail.",
      "R6 folded into R4 as validation instrumentation."
    ],
    "raw_ideas": [
      {
        "family": "model",
        "id": "R1",
        "one_liner": "Add tile-size-dependent occupancy correction to the FA4 roofline."
      },
      {
        "family": "model",
        "id": "R2",
        "one_liner": "Add effective HBM/L2/TMA bandwidth model with transfer-size efficiency."
      },
      {
        "family": "model",
        "id": "R3",
        "one_liner": "Add precision-specific Tensor Core MMA throughput and exponential emulation terms."
      },
      {
        "family": "model",
        "id": "R4",
        "one_liner": "Combine occupancy, TMA/L2, and precision corrections into one analytical predictor."
      },
      {
        "family": "model",
        "id": "R5",
        "one_liner": "Use a small symbolic-regression fit over white-box features to discover interaction terms."
      },
      {
        "family": "measurement",
        "id": "R6",
        "one_liner": "Collect NCU counter trends on calibration split and train a bottleneck classifier as a side output."
      },
      {
        "family": "objective",
        "id": "R7",
        "one_liner": "Change primary metric from MAPE to log-MAE to reduce sensitivity to tiny-runtime configs."
      },
      {
        "family": "infrastructure",
        "id": "R8",
        "one_liner": "Build a synthetic kernel microbenchmark suite to calibrate B200 constants independently of FA4."
      }
    ]
  },
  "status": "ready",
  "summary": "Raw idea slate for the FlashAttention-4 B200 runtime model idea pass.",
  "title": "Raw Idea Slate: FlashAttention-4 B200 Runtime Model Idea Pass"
}
```