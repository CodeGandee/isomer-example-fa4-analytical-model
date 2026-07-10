<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/mechanism-framing/v2
schema_ref: isomer:deepsci/record-format/schema/evidence/mechanism-framing/v2
payload_digest: sha256:7a94b4282bcfc5b7111bc6c97837a97786cc1081a8ab2b357a6239a19e8a3628
-->
# Mechanism Framing: FlashAttention-4 B200 Runtime Model Idea Pass

Mechanism framing for the FlashAttention-4 B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "candidate generation and pre-idea draft",
    "placeholder": "<MECHANISM_FRAMING>",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "code_translation": {
      "inputs": "(B, H, S, D, causal, precision)",
      "key_functions": [
        "compute_mma_time(precision, sm_count, peak_sm_clock, tile_m, tile_n, tile_k)",
        "compute_smem_time(bytes, effective_smem_bw, occupancy)",
        "compute_hbm_l2_time(bytes, effective_hbm_bw, l2_efficiency, tma_latency)",
        "compute_exp_time(seq_len, head_dim, mufu_rate, occupancy)",
        "resolve_occupancy(tile_regs, tile_smem, tile_tmem, max_warps_per_sm, sm_count)"
      ],
      "module": "predictor.py in topic.repos.main",
      "outputs": "predicted_runtime_ms, predicted_bottleneck_label, predicted_ncu_trends"
    },
    "competing_hypotheses": [
      "Only occupancy matters; memory bandwidth is already saturated in the paper roofline.",
      "Only precision throughput matters; occupancy is already near peak for FA4 tile choices.",
      "A simple linear regression on FLOPs and bytes beats any white-box extension."
    ],
    "consequence": "Adding these terms as white-box corrections to the roofline should improve held-out MAPE and bottleneck-label accuracy on B200.",
    "lever_bucket": "model",
    "mechanism_hypothesis": "The omitted first-order terms are (1) tile-size-dependent occupancy, which limits the number of concurrent warps per SM and therefore latency hiding; (2) effective HBM/L2/TMA bandwidth, which depends on transfer size, stride, and causal mask pattern; and (3) precision-specific Tensor Core throughput and exponential emulation rate on Blackwell.",
    "symptom": "Reproduced FA4 paper roofline predicts runtime as max(MMA time, SMEM time, exponential time) but deviates from measured B200 runtime, especially for small sequence lengths and low-precision configs.",
    "why_now": "The baseline comparator is accepted and its explicit caveats name exactly these missing terms, so falsification is immediate by held-out validation."
  },
  "status": "ready",
  "summary": "Mechanism framing for the FlashAttention-4 B200 runtime model idea pass.",
  "title": "Mechanism Framing: FlashAttention-4 B200 Runtime Model Idea Pass"
}
```