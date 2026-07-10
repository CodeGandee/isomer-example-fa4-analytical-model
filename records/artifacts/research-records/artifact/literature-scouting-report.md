<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/report/literature-scouting-report/v2
schema_ref: isomer:deepsci/record-format/schema/report/literature-scouting-report/v2
payload_digest: sha256:6731543982e5bf8610a50d44a823c67e70f686163e9cad7dde0b0c4a32d2c491
-->
# Literature Scouting Report

External discovery summary for the Flash Attention 4 white-box runtime model scout pass.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-baseline, isomer-deepsci-idea, isomer-deepsci-decision, future scout passes",
    "placeholder": "<LITERATURE_SCOUTING_REPORT>",
    "producer": "isomer-deepsci-scout",
    "skill": "isomer-deepsci-scout"
  },
  "sections": {
    "discovery_scope": "Targeted confirmation of FA4 paper analysis, Blackwell hardware parameters, and absence of existing predictors.",
    "rejected_or_watchlist": [
      "cuDNN 9.13 / Triton Attention - watchlist only (indirect plausibility)",
      "SageAttention family - rejected (consumer GPU scope mismatch)"
    ],
    "retained_references": [
      "arXiv 2603.05451v1 - primary algorithm/hardware source and seed comparator",
      "arXiv 2512.02189v1 - SMEM 128 B/clock/SM and MUFU 16 ops/clock/SM",
      "arXiv 2605.04178v1 - white-box GPU modeling methodology",
      "Official flash-attention repo - implementation source and validation harness"
    ],
    "route_implications": {
      "baseline_shortlist": "FA4 paper roofline model is anchor; naive roofline sanity check; measured runtime is ground truth.",
      "evaluation_contract": "Runtime MAPE vs measured B200; NCU counter trend agreement; bottleneck identification.",
      "next_route": "isomer-deepsci-baseline"
    },
    "search_ledger": [
      {
        "result": "Retained",
        "search": "FlashAttention-4 paper",
        "surface": "arXiv 2603.05451v1"
      },
      {
        "result": "Retained",
        "search": "Blackwell microbenchmarks",
        "surface": "arXiv 2512.02189v1"
      },
      {
        "result": "Retained",
        "search": "Cross-GPU analytical modeling",
        "surface": "arXiv 2605.04178v1"
      },
      {
        "result": "None found",
        "search": "Local existing predictor",
        "surface": "repos/extern/flash-attention"
      }
    ]
  },
  "status": "ready",
  "summary": "External discovery summary for the Flash Attention 4 white-box runtime model scout pass.",
  "title": "Literature Scouting Report"
}
```