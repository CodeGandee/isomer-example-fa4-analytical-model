<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/scout-discovery-ledger/v1
schema_ref: isomer:deepsci/record-format/schema/evidence/scout-discovery-ledger/v1
payload_digest: sha256:e76beccb5cf770134439e08d3be057010b1f89a073271e2528731683e35a5623
-->
# Scout Discovery Ledger

Compact record of targeted discovery for the Flash Attention 4 white-box runtime model scout pass.


```json
{
  "metadata": {
    "consumer": "\u003cLITERATURE_SCOUTING_REPORT\u003e, \u003cEVALUATION_CONTRACT\u003e, \u003cBASELINE_SHORTLIST\u003e, \u003cNEXT_ROUTE_DECISION\u003e",
    "placeholder": "\u003cSCOUT_DISCOVERY_LEDGER\u003e",
    "producer": "isomer-deepsci-scout through Literature Provider Binding, repository inspection, and compatibility artifact calls.",
    "skill": "isomer-deepsci-scout"
  },
  "sections": {
    "rejected_references": [
      "cuDNN 9.13 / Triton Attention - indirect plausibility only",
      "SageAttention family - consumer GPU scope mismatch"
    ],
    "retained_references": [
      "arXiv 2603.05451v1 - primary algorithm/hardware source",
      "arXiv 2512.02189v1 - independent Blackwell microbenchmarks",
      "arXiv 2605.04178v1 - analytical GPU modeling methodology",
      "repos/extern/flash-attention - implementation and validation harness"
    ],
    "search_passes": [
      {
        "query": "FA4 forward-pass roofline and B200 pipeline",
        "retained": "arXiv 2603.05451v1",
        "surface": "arXiv 2603.05451v1"
      },
      {
        "query": "Blackwell SMEM and MUFU throughput",
        "retained": "arXiv 2512.02189v1",
        "surface": "arXiv 2512.02189v1"
      },
      {
        "query": "Cross-GPU analytical modeling methodology",
        "retained": "arXiv 2605.04178v1",
        "surface": "arXiv 2605.04178v1"
      },
      {
        "query": "FA4 implementation and benchmarks",
        "retained": "Official Dao-AILab/flash-attention repo (local clone)",
        "surface": "repos/extern/flash-attention"
      },
      {
        "query": "Existing white-box FA4 predictor",
        "retained": "None found",
        "surface": "Local repo + project grep"
      }
    ],
    "unresolved_ambiguity": [
      "Exact FA4 tile/occupancy defaults per precision.",
      "Numeric accuracy target pending operator approval."
    ]
  },
  "status": "ready",
  "summary": "Compact record of targeted discovery for the Flash Attention 4 white-box runtime model scout pass.",
  "title": "Scout Discovery Ledger"
}
```