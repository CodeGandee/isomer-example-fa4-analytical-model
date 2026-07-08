<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/report/limitations-map/v1
schema_ref: isomer:deepsci/record-format/schema/report/limitations-map/v1
payload_digest: sha256:a17ab7c3556a8e7dc05ecf511f06f94bd322f76eb369e711807cbcb0310a74e4
-->
# Limitations Map: FlashAttention-4 B200 Runtime Model Idea Pass

Limitations map for the FlashAttention-4 B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "candidate generation",
    "placeholder": "\u003cLIMITATIONS_MAP\u003e",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "limitation_cards": [
      {
        "conditions": "Small S (tile work too small to hide latency), FP8/FP4 (higher nominal throughput but same occupancy/memory pressure).",
        "metric_importance": "Directly increases held-out MAPE and can flip bottleneck labels from compute-bound to memory-bound.",
        "strongest_evidence": "Baseline shortlist notes the roofline ignores L2/HBM, TMA latency, occupancy, and TMEM; host B200 spec shows peak SM clock 1965 MHz and memory clock 3996 MHz, but sustained HBM bandwidth is unmeasured.",
        "symptom": "FA4 paper roofline over-predicts throughput for small sequence lengths and under-predicts runtime for low-precision kernels."
      },
      {
        "conditions": "Head dimension, tile size, and SMEM/TMEM usage change the number of resident thread blocks per SM.",
        "metric_importance": "Causes large runtime jumps at tile-size boundaries and mislabels the bottleneck.",
        "strongest_evidence": "arXiv 2605.04178v1 shows occupancy-aware white-box models reduce roofline error.",
        "symptom": "Roofline assumes all SMs are equally utilized and no occupancy cliff exists."
      },
      {
        "conditions": "BF16/FP16 vs FP8 vs FP4 on Blackwell Tensor Cores; causal masks add non-linear ops.",
        "metric_importance": "FP8/FP4 can change both compute-bound and memory-bound regimes because bytes per element change and numerical emulation may differ.",
        "strongest_evidence": "arXiv 2512.02189v1 gives per-SM throughput constants including MUFU 16 ops/clock/SM.",
        "symptom": "Precision is treated only through FLOP count, not through actual SM throughput and exponential emulation."
      }
    ],
    "priority_ranking": [
      "Occupancy and TMA/L2 effective bandwidth \u2014 likely highest impact because FA4 is designed to be memory/compute balanced and B200 has a deep hierarchy.",
      "Precision-specific MMA throughput \u2014 high impact for FP8/FP4 configs, lower for BF16/FP16.",
      "Exponential emulation correction \u2014 smaller but measurable impact for causal/non-causal and softmax scaling."
    ],
    "root_cause_hypotheses": [
      "The baseline omits a tile-occupancy term, so latency-hiding and SM utilization are overestimated.",
      "The baseline omits effective L2/HBM/TMA bandwidth, so memory-bound configurations are mis-scaled.",
      "The baseline uses a single FLOP throughput constant, so precision and exponential emulation are mispredicted."
    ]
  },
  "status": "ready",
  "summary": "Limitations map for the FlashAttention-4 B200 runtime model idea pass.",
  "title": "Limitations Map: FlashAttention-4 B200 Runtime Model Idea Pass"
}
```