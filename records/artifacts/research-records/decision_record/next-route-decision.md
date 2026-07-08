<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/decision/next-route-decision/v1
schema_ref: isomer:deepsci/record-format/schema/decision/next-route-decision/v1
payload_digest: sha256:5afb988f35886a6cb13e30a8b70fbe0d1a8f6c0eee2c0fe0fc6467706bbfd37e
-->
# Next Route Decision: isomer-deepsci-baseline

Proceed to the baseline stage for the Flash Attention 4 white-box runtime model on NVIDIA B200.


```json
{
  "metadata": {
    "consumer": "Any production DeepSci research skill selected as the next route.",
    "placeholder": "\u003cNEXT_ROUTE_DECISION\u003e",
    "producer": "isomer-deepsci-scout or isomer-deepsci-decision",
    "skill": "isomer-deepsci-scout"
  },
  "sections": {
    "conditions_for_revisiting_scout": [
      "Operator rejects proposed MAPE threshold or calibration/validation split.",
      "FA4 tile/occupancy details cannot be sourced or measured.",
      "A published white-box FA4 predictor is discovered."
    ],
    "decision": "isomer-deepsci-baseline",
    "evidence_basis": [
      "intent/src/topic-overview.md",
      "intent/src/topic-env-gate.md",
      "actors/operator/host-b200-spec.md",
      "repos/extern/flash-attention",
      "arXiv 2603.05451v1 (FlashAttention-4)",
      "arXiv 2512.02189v1 (Blackwell microbenchmarks)"
    ],
    "rejected_alternatives": [
      "isomer-deepsci-idea",
      "isomer-deepsci-decision",
      "blocker"
    ],
    "topic": "flash-attention-4-whitebox-runtime-model",
    "topic_actor": "operator"
  },
  "status": "ready",
  "summary": "Proceed to the baseline stage for the Flash Attention 4 white-box runtime model on NVIDIA B200.",
  "title": "Next Route Decision: isomer-deepsci-baseline"
}
```