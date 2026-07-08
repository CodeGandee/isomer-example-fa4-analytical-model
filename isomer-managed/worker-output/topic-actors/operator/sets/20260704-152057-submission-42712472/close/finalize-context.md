# Finalize Context Brief — FlashAttention-4 White-Box Runtime Model

- closure_recommendation: park
- current_stage: submission-pass close
- accepted_comparator: reproduced FlashAttention-4 roofline baseline
- strongest_supported_findings:
  - Combined white-box predictor achieves 4.50% MAPE and 14.36% max APE on 160 held-out synthetic configurations.
  - Every validation configuration lies within the 30% error envelope.
  - Bottleneck-label accuracy is 100% on the held-out set.
  - TMA/L2 effective-bandwidth correction is the largest single improvement.
- route_status: paused pending real-silicon validation and venue confirmation
- writing_state: revised draft, references, and figures are complete
- decisions: review route decision `finalize`; data availability statement produced (general)
- blockers: no hard blocker; reopen condition is silicon validation and venue selection
- package_status: paper bundle copied to submission-pass set; data-availability statement attached
