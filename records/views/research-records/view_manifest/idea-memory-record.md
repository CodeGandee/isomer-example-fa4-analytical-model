<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/control/idea-memory-record/v2
schema_ref: isomer:deepsci/record-format/schema/control/idea-memory-record/v2
payload_digest: sha256:7a2c391e624ea8ff9e775e18281360dae722ad157654c5359b142e2a060fa420
-->
# Idea Memory Record: FlashAttention-4 B200 Runtime Model Idea Pass

Memory record for the FlashAttention-4 B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "future idea, scout, experiment, or write routes",
    "placeholder": "<IDEA_MEMORY_RECORD>",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "deferred_for_later": [
      "Synthetic B200 microbenchmark suite for constant calibration (R8).",
      "Symbolic-regression fallback if analytical terms fail (R5)."
    ],
    "key_reasoning": [
      "The accepted FA4 paper roofline is the right comparator but explicitly omits occupancy, L2/HBM/TMA, and precision-specific throughput.",
      "The highest-value first experiment is a combined analytical predictor with modular ablations, not a black-box regression or metric change.",
      "Candidate C1 subsumes C2 (precision-only) and C3 (occupancy-only); run all three as ablations in experiment."
    ],
    "lineage": {
      "parent_route": "artifact-ACCEPTED_BASELINE_RECORD-e673ec2be9b4",
      "route_decision": "isomer-deepsci-experiment",
      "selected_hypothesis_id": "fa4-b200-whitebox-occupancy-tma-l2-precision-v1"
    },
    "records_created": [
      "<OBJECTIVE_CONTRACT>",
      "<CURRENT_BOARD_PACKET>",
      "<LITERATURE_SURVEY_REPORT>",
      "<LIMITATIONS_MAP>",
      "<MECHANISM_FRAMING>",
      "<RAW_IDEA_SLATE>",
      "<CANDIDATE_IDEA_FRONTIER>",
      "<REJECTED_AND_DEFERRED_IDEAS>",
      "<PRE_IDEA_DRAFT>",
      "<SELECTED_HYPOTHESIS>",
      "<SELECTED_IDEA_DRAFT>",
      "<IDEA_ROUTE_DECISION>"
    ],
    "rejected_lessons": [
      "Do not change the primary metric away from MAPE; the evaluation contract is fixed.",
      "Do not use symbolic regression before testing interpretable analytical terms; it risks violating the white-box constraint."
    ],
    "retrieval_hints": [
      "If experiment fails, revisit limitations-map and pre-idea-draft for C2/C3.",
      "If new FA4 source reveals different tile sizes, update mechanism-framing and re-calibrate."
    ]
  },
  "status": "ready",
  "summary": "Memory record for the FlashAttention-4 B200 runtime model idea pass.",
  "title": "Idea Memory Record: FlashAttention-4 B200 Runtime Model Idea Pass"
}
```