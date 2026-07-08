<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/report/analysis-campaign-summary/v1
schema_ref: isomer:deepsci/record-format/schema/report/analysis-campaign-summary/v1
payload_digest: sha256:3ca825716cd39baf3690a386a22454d2059b622b9fce056b4dacf54ba1f495ac
-->
# Analysis campaign summary: bottleneck-accuracy audit

A single evidence slice audited the experiment metrics, calibration parameters, and NCU bottleneck labels. The launch-overhead correction was the dominant improvement. The remaining error is concentrated in white-box-to-NCU bottleneck mapping: the model frequently predicts memory-bound behavior while NCU reports compute-bound.


```json
{
  "metadata": {
    "recorded_at": "2026-07-04T21:01:22.593738Z"
  },
  "sections": {
    "contradiction": "All NCU-profiled configs are labeled compute-bound, but the white-box model predicts memory-bound (hbm/tma) for a substantial share of them.",
    "key_findings": {
      "finding_1": "MAPE and within-30% thresholds are satisfied; bottleneck accuracy is the only failing gate.",
      "finding_2": "The bottleneck miss is systematic: predicted memory-bound vs NCU compute-bound.",
      "finding_3": "Remaining error sources include coarse white-box\u2192NCU bottleneck mapping and unmodeled scheduler/warp effects."
    },
    "partial_support": "NCU bottleneck accuracy is 60.0% on validation (10 profiled) and 74.3% on query (35 profiled), just below the 75% target.",
    "slice_run": "Audit experiment metrics, calibration gains, and NCU bottleneck mapping.",
    "stable_support": "The improved predictor reduced validation MAPE from 55.64% to 12.62% (\u0394 +43.02 pp) and query MAPE from 43.12% to 10.01% (\u0394 +33.12 pp). Validation within-30% improved to 93.3% and query within-30% to 96.4%. Launch-overhead correction (launch_fixed_us=60.0) was the dominant fix.",
    "unresolved_ambiguity": "The validation profiled subset is only 10 configs, so 60% may be noisy. It is unclear whether the gap is best fixed by raising compute-component costs or by a coarser compute/memory binary mapping."
  },
  "status": "ready",
  "summary": "A single evidence slice audited the experiment metrics, calibration parameters, and NCU bottleneck labels. The launch-overhead correction was the dominant improvement. The remaining error is concentrated in white-box-to-NCU bottleneck mapping: the model frequently predicts memory-bound behavior while NCU reports compute-bound.",
  "title": "Analysis campaign summary: bottleneck-accuracy audit"
}
```