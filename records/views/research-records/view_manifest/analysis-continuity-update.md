<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/control/analysis-continuity-update/v1
schema_ref: isomer:deepsci/record-format/schema/control/analysis-continuity-update/v1
payload_digest: sha256:c8c6d27a05b9526ab03be7668cab229def1b0bdec096fceb4f64413f76429f7b
-->
# Analysis continuity update: preserve MAPE gains, refine bottleneck mapping

The next empirical iteration should start from the current calibration and focus narrowly on NCU bottleneck mapping.


```json
{
  "metadata": {
    "recorded_at": "2026-07-04T21:01:22.593738Z"
  },
  "sections": {
    "dependencies": "Access to the same NVIDIA B200 host and NCU tooling. The existing 540-config measurement set as the baseline comparison.",
    "last_completed_stage": "interpret (isomer-deepsci-analysis)",
    "next_action": "Run a targeted isomer-deepsci-experiment that adjusts white-box compute/memory component weights and re-profiles configs on B200.",
    "risks": "NCU profiling is time-consuming; prioritize the validation set and a stratified query subset. Bottleneck labels may remain noisy for small kernels due to launch-overhead dominance."
  },
  "status": "ready",
  "summary": "The next empirical iteration should start from the current calibration and focus narrowly on NCU bottleneck mapping.",
  "title": "Analysis continuity update: preserve MAPE gains, refine bottleneck mapping"
}
```