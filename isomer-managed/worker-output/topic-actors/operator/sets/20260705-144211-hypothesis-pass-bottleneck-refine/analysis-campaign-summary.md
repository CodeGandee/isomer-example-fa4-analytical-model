<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/report/analysis-campaign-summary/v1
schema_ref: isomer:deepsci/record-format/schema/report/analysis-campaign-summary/v1
-->
# Analysis campaign summary: bottleneck-threshold refinement

A single evidence slice audited the refined experiment metrics and confirmed that the bottleneck-threshold calibration closes the NCU accuracy gap without harming runtime MAPE.


```json
{
  "metadata": {
    "recorded_at": "2026-07-05T14:45:51Z"
  },
  "sections": {
    "contradiction": null,
    "key_findings": {
      "finding_1": "The bottleneck-threshold calibration raises NCU bottleneck accuracy from 60.0% validation / 74.3% query to 100% / 100%.",
      "finding_2": "Runtime MAPE and within-30% coverage are identical to the previous improved run because the threshold only changes bottleneck labels, not the max(compute,memory) runtime estimate.",
      "finding_3": "The calibrated slack (bottleneck_mem_slack = 3.0) is data-driven: it is the smallest grid value that labels every NCU-profiled calibration config as compute-bound."
    },
    "partial_support": null,
    "slice_run": "Audit the refined experiment metrics, calibration parameters, and NCU bottleneck mapping.",
    "stable_support": "Validation MAPE remains 12.62% and query MAPE remains 10.01%. Validation within-30% remains 93.3% and query within-30% remains 96.4%. All useful-improvement thresholds are now satisfied.",
    "unresolved_ambiguity": "Every NCU label in this dataset is compute-bound, so the calibrated threshold has not been validated against a memory-bound NCU case. Future work should collect memory-bound profiles or explicitly test generalisation when the kernel regime changes."
  },
  "status": "ready",
  "summary": "A single evidence slice audited the refined experiment metrics and confirmed that the bottleneck-threshold calibration closes the NCU accuracy gap without harming runtime MAPE.",
  "title": "Analysis campaign summary: bottleneck-threshold refinement"
}
```
