<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/decision/idea-route-decision/v1
schema_ref: isomer:deepsci/record-format/schema/decision/idea-route-decision/v1
payload_digest: sha256:11301f6b226d03843aa8548b8d54c1756eacde4c412a0c3f08629f80bc539e1c
-->
# Idea Route Decision: isomer-deepsci-experiment

Route decision after idea selection: proceed to experiment.


```json
{
  "metadata": {
    "consumer": "any production DeepSci research skill",
    "placeholder": "\u003cIDEA_ROUTE_DECISION\u003e",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "conditions_for_revisiting_idea": [
      "Experiment shows the combined model cannot beat the baseline after two calibration rounds.",
      "New literature reveals a closer prior predictor for FA4 on B200.",
      "Operator changes the metric contract or useful-improvement threshold."
    ],
    "decision": "experiment",
    "evidence_basis": [
      "artifact-ACCEPTED_BASELINE_RECORD-e673ec2be9b4",
      "artifact-COMPARABILITY_CONTRACT-0c72c2c67a42",
      "artifact-EVALUATION_CONTRACT-7f255a5e6694",
      "artifact-LITERATURE_SCOUTING_REPORT-fc6d5ca8b4a3",
      "actors/operator/host-b200-spec.md"
    ],
    "next_stage": "isomer-deepsci-experiment",
    "ready_for_experiment": true,
    "reason": "The selected hypothesis (fa4-b200-whitebox-occupancy-tma-l2-precision-v1) is falsifiable, has a concrete code-level plan, and is a direct extension of the accepted baseline with explicit calibration/validation splits. The literature survey, limitations map, mechanism framing, candidate frontier, pre-idea draft, and selected hypothesis handoff are complete.",
    "rejected_alternatives": [
      {
        "reason": "The route is still at the mechanism-selection stage; we need an experiment to measure whether the combined model works before within-family optimization.",
        "route": "optimize"
      },
      {
        "reason": "Comparator, metric contract, and literature coverage are already sufficient.",
        "route": "scout"
      },
      {
        "reason": "No active blocker; all required inputs are available.",
        "route": "blocker"
      }
    ],
    "selected_hypothesis_id": "fa4-b200-whitebox-occupancy-tma-l2-precision-v1"
  },
  "status": "ready",
  "summary": "Route decision after idea selection: proceed to experiment.",
  "title": "Idea Route Decision: isomer-deepsci-experiment"
}
```