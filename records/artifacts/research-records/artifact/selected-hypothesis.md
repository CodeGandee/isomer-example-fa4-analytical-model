# Selected Hypothesis: Bottleneck Saturation Predictability for FlashAttention-4 on B200

## Claim
A white-box FlashAttention-4 runtime predictor on NVIDIA B200 can predict **which hardware bottleneck will saturate** when input configurations are deliberately pushed toward the limits of compute, HBM bandwidth, L2 bandwidth, shared-memory bandwidth, TMA throughput, or MUFU throughput. The predictor's dominant-bottleneck label will agree with the component that NCU SpeedOfLight counters show as the actual limiting resource, with per-regime accuracy ≥ 75%.

## Mechanism sketch
The predictor's dominant bottleneck is the largest of six component times:
1. **Tensor Core MMA** — `F_MMA / (R_MMA(p) * occupancy)`.
2. **MUFU/SFU softmax** — `E / R_MUFU(p)`.
3. **HBM** — `B_HBM / β_HBM(B_HBM)`.
4. **L2** — `B_L2 / β_L2(B_L2)`.
5. **Shared memory** — `B_SMEM / β_SMEM(B_SMEM)`.
6. **TMA** — `B_TMA / β_TMA(B_TMA)`.

By choosing extreme configurations, each term can be made dominant:
- **MMA-saturating**: very long sequence, non-causal, fp8 or bf16, moderate batch/heads.
- **MUFU-saturating**: causal attention with large attention-score matrices where softmax work is high relative to MMA reuse.
- **HBM-saturating**: small sequence, large batch/head count, high precision (bf16/fp16), so byte traffic dominates over FLOPs.
- **L2-saturating**: medium sequence with repeated KV tile accesses that miss L1 but fit/reuse in L2.
- **SMEM-saturating**: tile shapes that force high shared-memory traffic for softmax reduction and operand staging.
- **TMA-saturating**: configurations that rely heavily on asynchronous copies for Q/K/V tiles with small transfer granularity.

The model already captures these terms; the test is whether the **label** they produce matches the **measured dominant counter** under deliberate saturation.

## Anti-win condition
If NCU shows the kernel is limited by an unmodeled mechanism (warp-specialization launch latency, TMA setup overhead, Blackwell FP4 scheduling, or occupancy collapse) for every pushed configuration, the six-term bottleneck model cannot claim saturation predictability.

## Minimal validation
1. Generate a small saturation matrix (~12–20 configurations) designed to make each of the six terms dominant in at least two configurations.
2. Run the white-box predictor to obtain the predicted dominant bottleneck for each configuration.
3. Run NCU `--section SpeedOfLight` on each configuration and label the actual bottleneck as compute-bound if `SM Throughput % ≥ Memory Throughput %`, else memory-bound; further classify compute into MMA/MUFU using the model's largest compute term, and memory into HBM/L2/SMEM/TMA using the largest memory term.
4. Compute per-regime and overall bottleneck-label accuracy.

## Abandonment condition
If fewer than four of the six bottleneck regimes can be realized on real B200, or if overall bottleneck accuracy is < 60%, the hypothesis is refuted and the model needs additional terms before claiming saturation predictability.

## Next route
Implement the saturation matrix, run the predictor + NCU experiment, and analyze whether the model's bottleneck labels survive deliberate resource pressure.
