<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/decision/experiment-route-decision/v1
schema_ref: isomer:deepsci/record-format/schema/decision/experiment-route-decision/v1
payload_digest: sha256:e1eaa93f984cb09d94263d6ce5a3a117c2b68c75f1707635ca20679c86c45ecf
-->
# Experiment Route Decision: Analysis

Route to analysis after real-hardware experiment refuted the selected hypothesis.


```json
{
  "metadata": {
    "consumer": "analysis, optimize, decision, finalize, idea",
    "placeholder": "\u003cEXPERIMENT_ROUTE_DECISION\u003e",
    "producer": "isomer-deepsci-experiment",
    "skill": "isomer-deepsci-experiment"
  },
  "sections": {
    "decision": "analysis",
    "evidence_refs": [
      "evidence_item-EXPERIMENT_RESULT_SUMMARY-0e6af52b5f23",
      "run-MAIN_RUN_RECORD-cc19cf5c010a"
    ],
    "reason": "The real-hardware experiment refuted the hypothesis (combined MAPE 62.1% vs baseline 42.1%; delta -20.0 pp; only 47% within 30%). The next step is isomer-deepsci-analysis to identify transfer gaps, especially launch-overhead-dominated small configs and the mismatch between calibrated efficiency factors and real B200 scheduling.",
    "route": "analysis"
  },
  "status": "ready",
  "summary": "Route to analysis after real-hardware experiment refuted the selected hypothesis.",
  "title": "Experiment Route Decision: Analysis"
}
```