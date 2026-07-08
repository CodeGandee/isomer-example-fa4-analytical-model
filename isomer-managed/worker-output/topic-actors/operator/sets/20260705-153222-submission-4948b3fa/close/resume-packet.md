# Resume Packet — FlashAttention-4 White-Box Runtime Model

## Current state
- Objective: develop and validate a white-box analytical model for FlashAttention-4 runtime on NVIDIA B200.
- Current stage: submission-pass complete; topic paused with closure decision `park`.
- Final recommendation at pause time: `park`.

## Accepted baseline and strongest evidence
- Reproduced FA4 roofline baseline and the real-hardware failure of the emulator-tuned model.
- Final refined model: 12.62% validation MAPE, 10.01% query MAPE, 100% NCU bottleneck accuracy.
- Evidence records: `artifact-ANALYSIS_CAMPAIGN_SUMMARY-320d852cdf6e`, `artifact-ANALYSIS_CAMPAIGN_SUMMARY-e8fa897761c1`, `artifact-PAPER_BUNDLE_CHECKPOINT-3ea4159c97ba`.

## Open blockers
- No public repository or persistent identifiers.
- Target venue and data policy unspecified.
- Memory-bound NCU cases and fp4 not validated.

## Next action
Deposit code and data in a public repository, then re-run `isomer-deepsci-finalize` to move from `park` to `publish` or route to venue-specific polishing.

## Do-not-repeat notes
- Do not re-run the real-hardware measurement campaign; the 540-configuration dataset is accepted.
- Do not retrain the emulator-tuned model and expect it to transfer to B200 without launch-overhead correction.
- Do not treat the 100% NCU bottleneck accuracy as generalising to memory-bound regimes.

## Reopen conditions
- Public repository exists with code, data, and README.
- Target venue chosen.
- References verified.
