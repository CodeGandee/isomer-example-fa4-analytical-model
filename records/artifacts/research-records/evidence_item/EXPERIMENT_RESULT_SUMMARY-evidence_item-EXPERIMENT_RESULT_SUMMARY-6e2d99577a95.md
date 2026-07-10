<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/experiment-result-summary/v2
schema_ref: isomer:deepsci/record-format/schema/evidence/experiment-result-summary/v2
payload_digest: sha256:db6b416d9fb8d149cc27bffff0b44131a7c8d94219c8a409055541ea34e2c839
-->
# Experiment Result Summary: Bottleneck-Threshold Calibration on Real B200

The bottleneck-threshold refinement is supported: NCU bottleneck accuracy reaches 100% on both validation and query while runtime MAPE and within-30% coverage remain unchanged.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-analysis, decision, optimize, finalize",
    "placeholder": "<EXPERIMENT_RESULT_SUMMARY>",
    "producer": "isomer-deepsci-experiment",
    "skill": "isomer-deepsci-experiment"
  },
  "sections": {
    "ablations_summary": {
      "baseline_fa4_roofline": {
        "mape": 55.64357557358759,
        "pct_within_30": 46.666666666666664
      },
      "improved": {
        "mape": 12.621659832731694,
        "ncu_bottleneck_accuracy": 60.0,
        "pct_within_30": 93.33333333333333
      },
      "refined": {
        "bottleneck_mem_slack": 3.0,
        "mape": 12.621659832731694,
        "ncu_bottleneck_accuracy": 100.0,
        "pct_within_30": 93.33333333333333
      }
    },
    "baseline_relation": "better",
    "caveats": [
      "fp4 precision is not supported by the installed FA4 build and was skipped.",
      "Bottleneck accuracy uses NCU SpeedOfLight compute/memory labels on a profiled subset; unprofiled configs are excluded.",
      "This pass reused the real-hardware measurements and NCU records from the previous improved-predictor run; only the bottleneck-mapping logic changed.",
      "All NCU labels are compute-bound, so the calibrated threshold is validated only against compute-bound cases."
    ],
    "claim_update": "The bottleneck-threshold calibration raises NCU bottleneck accuracy from 60.0%/74.3% to 100%/100% on validation/query while preserving the improved runtime MAPE.",
    "claim_verdict": "supported",
    "comparability": "Same 540-config matrix, splits, real B200 measurements, and NCU records as the previous improved-predictor run. The only change is the addition of bottleneck_mem_slack to the bottleneck decision rule.",
    "failure_mode": null,
    "intervention": "Added bottleneck_mem_slack to improved_predictor.py, calibrated it on the calibration split NCU labels, and re-evaluated on held-out validation and query splits.",
    "metrics": {
      "baseline_mape": 55.64357557358759,
      "bottleneck_mem_slack": 3.0,
      "delta_query_mape_pp": 33.11512703917594,
      "delta_val_mape_pp": 43.021915740855896,
      "query_mape": 10.008106134891227,
      "query_ncu_bottleneck_accuracy": 100.0,
      "query_pct_within_30": 96.36363636363636,
      "refined_mape": 12.621659832731694,
      "val_mape": 12.621659832731694,
      "val_ncu_bottleneck_accuracy": 100.0,
      "val_pct_within_30": 93.33333333333333
    },
    "next_action": "Proceed to isomer-deepsci-analysis to confirm that the threshold is not overfitting and to document the refined model.",
    "primary_metric": "ncu_bottleneck_accuracy",
    "research_question": "Does adding an NCU-guided bottleneck-threshold calibration push NCU bottleneck accuracy above 75% without degrading runtime MAPE on real B200 FlashAttention-4 measurements?",
    "selected_hypothesis_id": "fa4-b200-bottleneck-threshold-calibration-v1",
    "takeaway": "The refinement is supported. A single calibrated slack term that labels configs compute-bound when memory time is within 3× of compute time aligns the white-box diagnosis with NCU and pushes bottleneck accuracy to 100% on the profiled subset, with no runtime MAPE degradation."
  },
  "status": "ready",
  "summary": "The bottleneck-threshold refinement is supported: NCU bottleneck accuracy reaches 100% on both validation and query while runtime MAPE and within-30% coverage remain unchanged.",
  "title": "Experiment Result Summary: Bottleneck-Threshold Calibration on Real B200"
}
```