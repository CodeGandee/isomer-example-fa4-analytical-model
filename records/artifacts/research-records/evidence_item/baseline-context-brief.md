<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/baseline-context-brief/v2
schema_ref: isomer:deepsci/record-format/schema/evidence/baseline-context-brief/v2
payload_digest: sha256:e8f89035848ceff50a2e8d716867051443098c92d3c88f69b4627f2abfa7c1e0
-->
# Baseline Context Brief: FlashAttention-4 Roofline Baseline for B200

Baseline context brief for the FlashAttention-4 roofline comparator on NVIDIA B200.


```json
{
  "metadata": {
    "consumer": "route selection, verification",
    "placeholder": "<BASELINE_CONTEXT_BRIEF>",
    "producer": "isomer-deepsci-baseline",
    "skill": "isomer-deepsci-baseline"
  },
  "sections": {
    "acceptance_target": "comparison-ready",
    "active_uncertainty": "Exact B200 sustained HBM bandwidth, L2 transaction behavior, FA4 default tile sizes/occupancy per precision, and operator approval of the 25% MAPE threshold remain to be resolved during idea/experiment stages.",
    "candidate_comparator": "FlashAttention-4 Paper Roofline Model reproduced and extended for NVIDIA B200",
    "key_evidence": [
      "artifact-EVALUATION_CONTRACT-7f255a5e6694",
      "artifact-BASELINE_SHORTLIST-911590d5b576",
      "artifact-LITERATURE_SCOUTING_REPORT-fc6d5ca8b4a3",
      "actors/operator/host-b200-spec.md",
      "repos/extern/flash-attention @ 002cce0"
    ],
    "lighters_routes_considered": [
      "attach: no verified reusable predictor exists locally",
      "import: no trustworthy published white-box FA4 predictor package found",
      "verify-local-existing: no existing local predictor to verify"
    ],
    "route_recommendation": "reproduce / extend",
    "trust_state": "comparison-ready with caveats"
  },
  "status": "ready",
  "summary": "Baseline context brief for the FlashAttention-4 roofline comparator on NVIDIA B200.",
  "title": "Baseline Context Brief: FlashAttention-4 Roofline Baseline for B200"
}
```