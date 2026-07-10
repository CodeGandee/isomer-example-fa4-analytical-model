<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/report/candidate-idea-frontier/v2
schema_ref: isomer:deepsci/record-format/schema/report/candidate-idea-frontier/v2
payload_digest: sha256:b6aeda3572eecf980aa47b06bc9f6f68aae54a7a6449fa3b60fec1a074ea1501
-->
# Candidate Idea Frontier: FlashAttention-4 B200 Runtime Model Idea Pass

Candidate idea frontier for the FlashAttention-4 B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "selection gate or optimize",
    "placeholder": "<CANDIDATE_IDEA_FRONTIER>",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "collapse_rationale": "C1 subsumes C2 and C3 as ablation terms, so the experiment can test all three hypotheses in one model while C2 and C3 provide orthogonal falsification.",
    "serious_candidates": [
      {
        "abandonment_condition": "Combined model fails to beat baseline MAPE by >= 5 percentage points or falls below useful-improvement threshold after two rounds of constant calibration.",
        "anti_win_condition": "Adding the terms does not reduce held-out MAPE because the dominant error source is elsewhere (e.g., implementation-specific scheduling).",
        "family": "model",
        "id": "C1",
        "minimal_validation": "Implement predictor with modular terms; ablate each term on held-out validation; report delta MAPE and bottleneck accuracy.",
        "novelty_label": "incremental but valuable",
        "prior_work_overlap": "Extends arXiv 2603.05451v1 roofline with methodology from arXiv 2605.04178v1 and constants from arXiv 2512.02189v1.",
        "status": "selected",
        "summary": "Baseline accepted with explicit caveats naming these exact terms; falsifiable by held-out validation.",
        "targeted_limitation": "FA4 paper roofline ignores occupancy, memory-hierarchy bandwidth, and precision throughput.",
        "title": "Combined occupancy-bandwidth-precision predictor",
        "why_now": "Baseline accepted with explicit caveats naming these exact terms; falsifiable by held-out validation."
      },
      {
        "abandonment_condition": "Precision-only variant does not improve MAPE on FP8/FP4 subset.",
        "anti_win_condition": "BF16/FP16 and FP8/FP4 runtimes scale with bytes and FLOPs already, so precision throughput is not the bottleneck.",
        "family": "model",
        "id": "C2",
        "minimal_validation": "Run precision-only variant on held-out validation across all four precisions.",
        "novelty_label": "incremental but valuable",
        "prior_work_overlap": "arXiv 2512.02189v1 Blackwell microbenchmarks.",
        "status": "serious_alternative",
        "summary": "Cheapest first ablation of C1; directly tests whether precision is the dominant missing term.",
        "targeted_limitation": "Roofline treats precision only through FLOP count.",
        "title": "Precision-only throughput correction",
        "why_now": "Cheapest first ablation of C1; directly tests whether precision is the dominant missing term."
      },
      {
        "abandonment_condition": "Occupancy-only variant does not improve MAPE on small-S configs.",
        "anti_win_condition": "FA4 tile choices already achieve near-peak occupancy on B200.",
        "family": "model",
        "id": "C3",
        "minimal_validation": "Run occupancy-only variant on held-out validation; compare to baseline and C1.",
        "novelty_label": "incremental but valuable",
        "prior_work_overlap": "arXiv 2605.04178v1 occupancy modeling.",
        "status": "serious_alternative",
        "summary": "Direct test of the occupancy hypothesis; can be implemented without memory bandwidth calibration.",
        "targeted_limitation": "Roofline assumes full SM utilization.",
        "title": "Occupancy-only correction",
        "why_now": "Direct test of the occupancy hypothesis; can be implemented without memory bandwidth calibration."
      }
    ]
  },
  "status": "ready",
  "summary": "Candidate idea frontier for the FlashAttention-4 B200 runtime model idea pass.",
  "title": "Candidate Idea Frontier: FlashAttention-4 B200 Runtime Model Idea Pass"
}
```