<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/experiment-result-summary/v2
schema_ref: isomer:deepsci/record-format/schema/evidence/experiment-result-summary/v2
payload_digest: sha256:97af4c7610dc2b66566606e39250b8db58bdbc631233f862c3f1ae7da673435f
-->
# Test Experiment Result Summary 001

Test experiment result summary for CLI verification.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-analysis, decision, optimize, finalize",
    "placeholder": "<EXPERIMENT_RESULT_SUMMARY>",
    "producer": "isomer-deepsci-experiment",
    "skill": "isomer-deepsci-experiment"
  },
  "sections": {
    "ablations_summary": {},
    "baseline_relation": "neutral",
    "caveats": [
      "This is a test record created to verify isomer-cli ext research records create with a structured payload."
    ],
    "claim_update": "Test claim update.",
    "claim_verdict": "test",
    "comparability": "Test comparability note.",
    "failure_mode": "None; this is a test.",
    "intervention": "Test intervention.",
    "metrics": {
      "baseline_mape": 0.0,
      "bottleneck_accuracy": 100.0,
      "combined_mape": 0.0,
      "delta_mape_pp": 0.0,
      "max_ape": 0.0,
      "n_validation_configs": 1,
      "pct_within_30": 100.0
    },
    "next_action": "None; this is a test record.",
    "primary_metric": "held_out_mape_predicted_runtime_ms",
    "research_question": "Test question for CLI record creation.",
    "selected_hypothesis_id": "test-hypothesis-001",
    "takeaway": "Test takeaway."
  },
  "status": "ready",
  "summary": "Test experiment result summary for CLI verification.",
  "title": "Test Experiment Result Summary 001"
}
```