<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/control/pipeline-run-record/v1
schema_ref: isomer:deepsci/record-format/schema/control/pipeline-run-record/v1
payload_digest: sha256:42ac96999ca85bbfb9902cb1298cc2af1e4258123f17ef2e21def7c0f478fda5
-->
# Pipeline Run Record: hypothesis-pass

Pipeline run record for the hypothesis-pass real-hardware validation of the FA4 B200 predictor.


```json
{
  "metadata": {
    "consumer": "External controller, future resume logic",
    "placeholder": "pipeline-run-record",
    "producer": "isomer-deepsci-pipeline",
    "skill": "isomer-deepsci-pipeline"
  },
  "sections": {
    "artifact_handoffs": {
      "artifact-SELECTED_HYPOTHESIS-80aa602f908c": "evidence_item-EXPERIMENT_RESULT_SUMMARY-0e6af52b5f23",
      "artifact-SELECTED_HYPOTHESIS-bab659036a3c": "artifact-SELECTED_HYPOTHESIS-80aa602f908c",
      "evidence_item-EXPERIMENT_RESULT_SUMMARY-0e6af52b5f23": "artifact-ANALYSIS_CAMPAIGN_SUMMARY-9932a6e83b29"
    },
    "block_events": [],
    "pause_events": [],
    "pipeline_id": "hypothesis-pass",
    "recipe_id": "hypothesis-pass",
    "run_completed_at": "2026-07-04T18:59:04Z",
    "run_started_at": "2026-07-04T18:41:39Z",
    "stage_sequence": [
      "ideate",
      "run",
      "interpret"
    ],
    "stages": [
      {
        "artifacts_in": [
          "artifact-SELECTED_HYPOTHESIS-bab659036a3c"
        ],
        "artifacts_out": [
          "artifact-SELECTED_HYPOTHESIS-80aa602f908c"
        ],
        "notes": "Refined the selected hypothesis for real-hardware validation on B200; set ready_for_experiment=true.",
        "route_decision": "experiment",
        "skill": "isomer-deepsci-idea",
        "stage_id": "ideate",
        "status": "complete"
      },
      {
        "artifacts_in": [
          "artifact-SELECTED_HYPOTHESIS-80aa602f908c"
        ],
        "artifacts_out": [
          "evidence_item-EXPERIMENT_RESULT_SUMMARY-0e6af52b5f23",
          "run-MAIN_RUN_RECORD-cc19cf5c010a",
          "decision_record-EXPERIMENT_ROUTE_DECISION-882b4b189d19",
          "artifact-IMPLEMENTATION_CHANGE_MAP-757b165cc2a7"
        ],
        "notes": "Real B200 benchmark of 864 configs (bf16/fp16/fp8) completed in 222s. Hypothesis refuted: combined MAPE 62.1% vs baseline 42.1%.",
        "route_decision": "analysis",
        "skill": "isomer-deepsci-experiment",
        "stage_id": "run",
        "status": "complete"
      },
      {
        "artifacts_in": [
          "evidence_item-EXPERIMENT_RESULT_SUMMARY-0e6af52b5f23"
        ],
        "artifacts_out": [
          "evidence_item-ANALYSIS_CONTEXT_BRIEF-daed8feb7775",
          "artifact-ANALYSIS_CAMPAIGN_SUMMARY-9932a6e83b29",
          "decision_record-ANALYSIS_ROUTE_DECISION-b7e5994bbb9b"
        ],
        "notes": "Identified launch-overhead small-config latency and misspecified efficiency factors as transfer gaps.",
        "route_decision": "experiment",
        "skill": "isomer-deepsci-analysis",
        "stage_id": "interpret",
        "status": "complete"
      }
    ]
  },
  "status": "ready",
  "summary": "Pipeline run record for the hypothesis-pass real-hardware validation of the FA4 B200 predictor.",
  "title": "Pipeline Run Record: hypothesis-pass"
}
```