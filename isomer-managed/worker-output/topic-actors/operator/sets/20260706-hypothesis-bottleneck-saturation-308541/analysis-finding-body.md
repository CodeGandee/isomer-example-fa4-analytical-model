# Analysis Finding: Bottleneck-Saturation Diagnostic for the FA4 B200 Predictor

**Claim:** The FA4 B200 white-box predictor correctly identifies compute-bound regimes but over-predicts memory/TMA dominance for medium-size problems.

**Evidence:**
- 12 saturation configs were profiled with NCU SpeedOfLight; 12 returned valid compute/memory counters.
- Coarse accuracy (compute vs memory) was 66.7% overall: 100% for mma, 100% for mufu, 66.7% for hbm, and 0% for tma.
- The three TMA-targeted configs were predicted as memory/tma but measured as compute/mma by NCU (compute_pct 53-72%, memory_pct 12-26%).
- One HBM-targeted config (batch=32, heads=16, seqlen=512, head_dim=64) was predicted as memory/hbm but measured as compute/mma (compute_pct 32.6%, memory_pct 15.7%).

**Implications:**
- The predictor's TMA bandwidth model appears too low relative to effective compute overlap, making TMA time dominate when hardware is still compute-limited.
- The coarse compute/memory split is the most trustworthy comparison; fine labels for memory stages are derived from the model itself.
- L2 and SMEM labels cannot be independently validated because the workload model never makes them the dominant memory stage.

**Limitations:**
- NCU SpeedOfLight only resolves compute vs memory, not individual memory hierarchies.
- Single-GPU profiling ignores batching, multi-GPU, and concurrency effects.
- Only bf16 precision was tested.

**Next action:** Investigate whether TMA time should be overlapped with MMA rather than added to a max() roofline, or whether the TMA bandwidth constant needs recalibration.
