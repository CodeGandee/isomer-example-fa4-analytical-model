<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/report/literature-survey-report/v1
schema_ref: isomer:deepsci/record-format/schema/report/literature-survey-report/v1
payload_digest: sha256:f35915b274566f77b4c6c04751858c9e6ec370e0dedb247559ffc0e617b95852
-->
# Literature Survey Report: FlashAttention-4 B200 Runtime Model Idea Pass

Literature survey report for the FlashAttention-4 B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "candidate selection and writing",
    "placeholder": "\u003cLITERATURE_SURVEY_REPORT\u003e",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "cheapest_falsification_paths": [
      "Compare precision-only variant vs baseline on held-out validation; if MAPE does not improve, the precision-throughput correction is not the dominant missing term.",
      "Compare occupancy-only variant vs baseline; if no improvement, occupancy is not the bottleneck."
    ],
    "citations_for_selected_idea_draft": [
      "arXiv 2603.05451v1",
      "arXiv 2605.04178v1",
      "arXiv 2512.02189v1"
    ],
    "closest_prior_work_table": [
      {
        "dataset": "Paper-derived configuration set.",
        "implication": "Our route adds the missing terms while preserving interpretability.",
        "mechanism": "Analytical roofline bound over MMA FLOPs, SMEM traffic, and exponential unit ops.",
        "metric": "Theoretical roofline bound.",
        "paper": "arXiv 2603.05451v1 FA4 roofline",
        "supported_claim": "MMA/SMEM/exponential are first-order terms.",
        "task": "Forward-pass FlashAttention runtime estimation.",
        "weakness": "Ignores occupancy, TMA/L2, precision throughput, and chip-specific sustained bandwidth."
      },
      {
        "dataset": "Multiple GPU kernels.",
        "implication": "Methodology justifies adding occupancy and effective bandwidth terms.",
        "mechanism": "Analytical model plus bounded calibration for cache, shared memory, and occupancy.",
        "metric": "Runtime/error vs measured.",
        "paper": "arXiv 2605.04178v1 white-box GPU modeling",
        "supported_claim": "Occupancy and memory-hierarchy corrections improve roofline accuracy.",
        "task": "General GPU kernel runtime prediction.",
        "weakness": "Not specific to FA4 or Blackwell B200."
      }
    ],
    "feasibility_blockers": [
      "Exact FA4 tile sizes and kernel launch parameters must be read from the official repo or measured with NCU on calibration split only."
    ],
    "implementation_levers": [
      "Tile-size-aware occupancy model (warps per SM, register/SMEM/TMEM limits).",
      "Effective HBM/L2 bandwidth per precision and access pattern.",
      "Precision-specific Tensor Core MMA throughput (BF16/FP16 vs FP8 vs FP4).",
      "Exponential emulation cost on Blackwell MUFU."
    ],
    "novelty_and_value_verdicts": {
      "reason": "The mechanism family (add occupancy/TMA/L2/precision terms to a roofline) is known in GPU modeling, but the concrete B200/FA4 instantiation and falsification are new locally.",
      "selected_route_label": "incremental but valuable"
    },
    "paper_buckets": {
      "adjacent_inspirations": [
        "arXiv 2512.02189v1 \u2014 Blackwell microbenchmarks; SMEM 128 B/clock/SM and MUFU 16 ops/clock/SM constants."
      ],
      "closest_competitors": [
        "arXiv 2605.04178v1 \u2014 white-box GPU performance modeling methodology; provides analytical correction for memory hierarchies and occupancy."
      ],
      "core_papers": [
        "arXiv 2603.05451v1 \u2014 FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling; primary algorithm and seed roofline model."
      ],
      "watchlist": [
        "cuDNN 9.13 / Triton Attention \u2014 indirect plausibility only; closed-source or different kernels.",
        "SageAttention family \u2014 consumer GPU scope mismatch."
      ]
    },
    "prior_evidence_reused": [
      "artifact-LITERATURE_SCOUTING_REPORT-fc6d5ca8b4a3",
      "artifact-EVALUATION_CONTRACT-7f255a5e6694",
      "artifact-ACCEPTED_BASELINE_RECORD-e673ec2be9b4",
      "artifact-COMPARABILITY_CONTRACT-0c72c2c67a42"
    ],
    "search_ledger": [
      {
        "newly_added": [],
        "reason": "Scout already identified core FA4 paper and Blackwell microbenchmark sources; no new broad search needed.",
        "reconfirmed": [
          "arXiv 2603.05451v1",
          "arXiv 2512.02189v1",
          "arXiv 2605.04178v1"
        ],
        "remaining_gap": "Need FA4 source-level tile sizes and occupancy defaults; will read repos/extern/flash-attention during experiment.",
        "search": "Reuse scout literature pass",
        "source": "artifact-LITERATURE_SCOUTING_REPORT-fc6d5ca8b4a3"
      }
    ],
    "survey_header": {
      "comparator_basis": "FlashAttention-4 Paper Roofline Model reproduced and extended for NVIDIA B200",
      "date": "2026-07-04",
      "metric_contract": "held_out_mape_predicted_runtime_ms minimize; max_absolute_percentage_error minimize; pct_validation_configs_within_30_pct_abs_error maximize; bottleneck_label_accuracy maximize.",
      "minimum_gate_status": "passed \u2014 prior scouting report reused and extended with mechanism-focused review.",
      "research_topic_id": "flash-attention-4-whitebox-runtime-model",
      "task": "White-box forward-pass runtime predictor for Flash Attention 4 on a single NVIDIA B200 across BF16/FP16/FP8/FP4 precisions."
    }
  },
  "status": "ready",
  "summary": "Literature survey report for the FlashAttention-4 B200 runtime model idea pass.",
  "title": "Literature Survey Report: FlashAttention-4 B200 Runtime Model Idea Pass"
}
```