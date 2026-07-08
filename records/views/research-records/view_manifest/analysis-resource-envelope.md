<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/control/analysis-resource-envelope/v1
schema_ref: isomer:deepsci/record-format/schema/control/analysis-resource-envelope/v1
payload_digest: sha256:531236d27e6512d55fe1c6ecf0487ff05f67e59d15b15fdceda50dc1e4814261
-->
# Analysis Resource Envelope: FA4 B200 Read-Only Audit

Execution envelope for the analysis stage: a read-only audit of existing experiment outputs, run on the local workstation with no additional compute budget required.


```json
{
  "metadata": {
    "consumer": "campaign design and execution",
    "placeholder": "\u003cANALYSIS_RESOURCE_ENVELOPE\u003e",
    "producer": "isomer-deepsci-analysis",
    "skill": "isomer-deepsci-analysis"
  },
  "sections": {
    "blocked_slices": "none; no supplementary slices were needed because the existing experiment outputs already answer the evidence question.",
    "concurrency": "single-threaded audit",
    "cpu": "sufficient for CSV/JSON audit",
    "credentials": "none required",
    "dependencies": [
      "pixi-managed Python 3.11 environment",
      "isomer-cli"
    ],
    "device": "Local Linux workstation",
    "memory": "low (a few MB of predictions and metrics)",
    "runnable_now": [
      "read-only audit of validation_metrics.json, combined_predictions.csv, and calibration_params.json"
    ],
    "services": "none required",
    "storage": "worker output root on <PROJECT_ROOT>/isomer-content",
    "wall_clock": "analysis stage bounded to minutes (no new experiment launched)"
  },
  "status": "ready",
  "summary": "Execution envelope for the analysis stage: a read-only audit of existing experiment outputs, run on the local workstation with no additional compute budget required.",
  "title": "Analysis Resource Envelope: FA4 B200 Read-Only Audit"
}
```