<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/claim-validation-record/v1
schema_ref: isomer:deepsci/record-format/schema/evidence/claim-validation-record/v1
payload_digest: sha256:c169fbbeeb58b3025d4027cc75c2eaa2745863b9a93d787bdfb376f42f57ec98
-->
# Claim Validation Record: FA4 B200 Combined Predictor

Claim-to-metric traceability for the selected hypothesis.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-analysis, write, decision, finalize",
    "placeholder": "\u003cCLAIM_VALIDATION_RECORD\u003e",
    "producer": "isomer-deepsci-experiment",
    "skill": "isomer-deepsci-experiment"
  },
  "sections": {
    "claims": [
      {
        "caveat": "Measured on emulator-based ground truth.",
        "claim": "held_out_mape_predicted_runtime_ms \u003c= 25%",
        "expected_direction": "\u003c=",
        "expected_value": 25.0,
        "metric_key": "held_out_mape_predicted_runtime_ms",
        "observed_value": 4.496608444017569,
        "verdict": "supported"
      },
      {
        "caveat": "",
        "claim": "pct_validation_configs_within_30_pct_abs_error \u003e= 75%",
        "expected_direction": "\u003e=",
        "expected_value": 75.0,
        "metric_key": "pct_validation_configs_within_30_pct_abs_error",
        "observed_value": 100.0,
        "verdict": "supported"
      },
      {
        "caveat": "",
        "claim": "bottleneck_label_accuracy \u003e= 75%",
        "expected_direction": "\u003e=",
        "expected_value": 75.0,
        "metric_key": "bottleneck_label_accuracy",
        "observed_value": 100.0,
        "verdict": "supported"
      },
      {
        "caveat": "Baseline MAPE was 22.22%; combined MAPE was 4.50%.",
        "claim": "Delta MAPE vs baseline \u003e= 5 percentage points improvement",
        "expected_direction": "\u003e=",
        "expected_value": 5.0,
        "metric_key": "delta_mape_pp",
        "observed_value": 17.719831614694343,
        "verdict": "supported"
      }
    ]
  },
  "status": "ready",
  "summary": "Claim-to-metric traceability for the selected hypothesis.",
  "title": "Claim Validation Record: FA4 B200 Combined Predictor"
}
```