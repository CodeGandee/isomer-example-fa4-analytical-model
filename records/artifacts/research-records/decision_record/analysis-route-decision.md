<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/decision/analysis-route-decision/v2
schema_ref: isomer:deepsci/record-format/schema/decision/analysis-route-decision/v2
payload_digest: sha256:07cb852af2226bdbbd09ac5bb2ff19e3e8cda52c306353f4f24e13ed4e19704e
-->
# Analysis route decision: targeted bottleneck-mapping experiment

Route to a narrow follow-up experiment that preserves the calibrated launch-overhead and MAPE gains while refining the white-box-to-NCU bottleneck mapping.


```json
{
  "metadata": {
    "recorded_at": "2026-07-04T21:01:22.593738Z"
  },
  "sections": {
    "alternative_reason": "If NCU profiling capacity is limited and MAPE/within-30% performance is sufficient for downstream use, the result can be finalized with a caveat that bottleneck labels are approximate.",
    "alternative_route": "finalize",
    "conditions_for_experiment": "Keep launch_fixed_us=60.0 and current MAPE calibration as the starting point. Profile additional configs (ideally all validation and a larger query sample) to stabilize bottleneck accuracy. Adjust MMA/MUFU vs HBM/L2/SMEM/TMA component weights or introduce a compute/memory binary mapping and re-evaluate NCU bottleneck accuracy. If bottleneck accuracy still falls short after the mapping fix, consider accepting the result with documented limitations.",
    "reason": "The improved predictor passes MAPE and within-30% thresholds but narrowly misses the ≥75% NCU bottleneck-accuracy threshold (60.0% validation, 74.3% query). The gap is systematic (predicted memory-bound vs NCU compute-bound) and small enough that a targeted calibration of compute-vs-memory component weights is likely to close it, without repeating the full B200 measurement sweep.",
    "route": "experiment"
  },
  "status": "ready",
  "summary": "Route to a narrow follow-up experiment that preserves the calibrated launch-overhead and MAPE gains while refining the white-box-to-NCU bottleneck mapping.",
  "title": "Analysis route decision: targeted bottleneck-mapping experiment"
}
```