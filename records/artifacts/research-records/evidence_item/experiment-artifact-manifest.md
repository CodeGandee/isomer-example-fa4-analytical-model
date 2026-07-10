<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/experiment-artifact-manifest/v2
schema_ref: isomer:deepsci/record-format/schema/evidence/experiment-artifact-manifest/v2
payload_digest: sha256:7cee73739a57c1fef94c3ac1288ee360a67f150af6bb1f2686c5496747b530c0
-->
# Experiment Artifact Manifest: FA4 B200 Combined Predictor

Inventory of durable artifacts produced by the experiment run.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-analysis, decision, optimize, finalize",
    "placeholder": "<EXPERIMENT_ARTIFACT_MANIFEST>",
    "producer": "isomer-deepsci-experiment",
    "skill": "isomer-deepsci-experiment"
  },
  "sections": {
    "artifact_list": [
      {
        "description": "Per-model validation metrics including MAPE, max APE, within-30% coverage, and bottleneck accuracy.",
        "path": "validation_metrics.json"
      },
      {
        "description": "CSV rendering of validation_metrics.json.",
        "path": "validation_metrics.csv"
      },
      {
        "description": "Per-configuration predicted and measured runtimes and bottleneck labels for the combined model.",
        "path": "combined_predictions.csv"
      },
      {
        "description": "Calibrated bounded correction factors for combined and ablation models.",
        "path": "calibration_params.json"
      },
      {
        "description": "Calibration split configuration matrix.",
        "path": "configs/calibration_configs.json"
      },
      {
        "description": "Held-out validation split configuration matrix.",
        "path": "configs/validation_configs.json"
      },
      {
        "description": "Disjoint prediction-query configuration matrix.",
        "path": "configs/query_configs.json"
      },
      {
        "description": "Emulator-based ground-truth measurements for the calibration split.",
        "path": "calibration_measurements.json"
      },
      {
        "description": "Emulator-based ground-truth measurements for the validation split.",
        "path": "validation_measurements.json"
      },
      {
        "description": "Experiment status and primary metrics produced by the runner.",
        "path": "experiment_result.json"
      }
    ],
    "code_artifacts": [
      "repos/topic-main/src/fa4_b200_predictor/constants.py",
      "repos/topic-main/src/fa4_b200_predictor/predictor.py",
      "repos/topic-main/src/fa4_b200_predictor/emulator.py",
      "repos/topic-main/src/fa4_b200_predictor/config_matrix.py",
      "repos/topic-main/src/fa4_b200_predictor/calibrate.py",
      "repos/topic-main/src/fa4_b200_predictor/evaluate.py",
      "repos/topic-main/src/fa4_b200_predictor/run_experiment.py"
    ],
    "provenance": {
      "baseline": "artifact-ACCEPTED_BASELINE_RECORD-e673ec2be9b4",
      "comparability": "artifact-COMPARABILITY_CONTRACT-0c72c2c67a42",
      "evaluation": "artifact-EVALUATION_CONTRACT-7f255a5e6694",
      "hypothesis": "artifact-SELECTED_HYPOTHESIS-bab659036a3c",
      "route": "decision_record-IDEA_ROUTE_DECISION-67d409112cbb"
    }
  },
  "status": "ready",
  "summary": "Inventory of durable artifacts produced by the experiment run.",
  "title": "Experiment Artifact Manifest: FA4 B200 Combined Predictor"
}
```