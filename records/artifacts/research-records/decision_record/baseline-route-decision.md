<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/decision/baseline-route-decision/v2
schema_ref: isomer:deepsci/record-format/schema/decision/baseline-route-decision/v2
payload_digest: sha256:daa754ccb9014b74e294d107169b504f592f9e583912d5089560043e2ea1b810
-->
# Baseline Route Decision: isomer-deepsci-idea

Route decision after baseline acceptance: proceed to isomer-deepsci-idea.


```json
{
  "metadata": {
    "consumer": "Any production DeepSci research skill",
    "placeholder": "<BASELINE_ROUTE_DECISION>",
    "producer": "isomer-deepsci-baseline",
    "skill": "isomer-deepsci-baseline"
  },
  "sections": {
    "conditions_for_revisiting_baseline": [
      "Operator rejects the proposed MAPE threshold or calibration/validation split.",
      "The FA4 paper roofline cannot be reproduced or extended to B200 within the accepted caveats.",
      "A published white-box FA4 predictor is discovered that supersedes this comparator."
    ],
    "decision": "isomer-deepsci-idea",
    "evidence_basis": [
      "artifact-EVALUATION_CONTRACT-7f255a5e6694",
      "artifact-BASELINE_SHORTLIST-911590d5b576",
      "artifact-LITERATURE_SCOUTING_REPORT-fc6d5ca8b4a3",
      "actors/operator/host-b200-spec.md",
      "repos/extern/flash-attention @ 002cce0"
    ],
    "reason": "The baseline comparator and metric contract are accepted. The next pipeline stage is idea generation and refinement of the white-box B200 runtime model, anchored on the accepted FA4 paper roofline comparator.",
    "rejected_alternatives": [
      "isomer-deepsci-experiment",
      "isomer-deepsci-decision",
      "baseline-blocker"
    ],
    "topic": "flash-attention-4-whitebox-runtime-model",
    "topic_actor": "operator"
  },
  "status": "ready",
  "summary": "Route decision after baseline acceptance: proceed to isomer-deepsci-idea.",
  "title": "Baseline Route Decision: isomer-deepsci-idea"
}
```