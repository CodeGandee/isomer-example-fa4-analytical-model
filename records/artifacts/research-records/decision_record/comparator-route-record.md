<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/decision/comparator-route-record/v2
schema_ref: isomer:deepsci/record-format/schema/decision/comparator-route-record/v2
payload_digest: sha256:58e6487cf8977446d347b2e9c0e64a453f26c91947c16d54a962c55c2dda96b5
-->
# Comparator Route Record: FlashAttention-4 Roofline Baseline for B200

Comparator route record selecting reproduce/extend of the FlashAttention-4 paper roofline model for B200.


```json
{
  "metadata": {
    "consumer": "verification",
    "placeholder": "<COMPARATOR_ROUTE_RECORD>",
    "producer": "isomer-deepsci-baseline",
    "skill": "isomer-deepsci-baseline"
  },
  "sections": {
    "acceptance_boundary": {
      "blocker_condition": "No accessible source for FA4 algorithm or B200 hardware parameters, or operator rejects metric contract.",
      "evidence_required_to_accept": "Source identity, hardware context, metric contract, and explicit caveats must be durable and inspectable.",
      "fallback_or_route_switch": "If reproduction fails, route to repair, decision, or blocker; if a published predictor appears, revisit baseline.",
      "fastest_failure_signal": "Official repository or paper reference missing; evaluation contract metrics unclear; B200 host spec unavailable."
    },
    "baseline_contract": {
      "baseline_id": "fa4-paper-roofline-b200",
      "baseline_variant": "default",
      "chosen_route": "reproduce / extend",
      "comparator_identity": "FlashAttention-4 Paper Roofline Model reproduced and extended for NVIDIA B200",
      "dataset_and_split": "Synthetic configuration matrix; calibration ~20%, held-out validation ~20%, query inputs disjoint from both.",
      "known_deviations": [
        "B200-specific terms (L2/HBM, TMA latency, occupancy, TMEM) are extension items.",
        "Exact sustained HBM bandwidth and L2 behavior require calibration."
      ],
      "required_metric_ids_and_directions": [
        "held_out_mape_predicted_runtime_ms -> minimize",
        "max_absolute_percentage_error -> minimize",
        "pct_validation_configs_within_30_pct_abs_error -> maximize",
        "bottleneck_label_accuracy -> maximize"
      ],
      "source_paper_repository_or_package": "arXiv 2603.05451v1 + https://github.com/Dao-AILab/flash-attention @ 002cce0",
      "task": "White-box forward-pass runtime predictor for Flash Attention 4 on a single NVIDIA B200 across BF16/FP16/FP8/FP4 precisions, without executing the queried kernel."
    },
    "current_frontier": {
      "active_blocker": "none",
      "latest_evidence": "Host spec verified, repository clone at 002cce0 verified, evaluation contract and baseline shortlist reviewed.",
      "next_action": "Create durable comparability contract, accepted baseline record, and route decision to isomer-deepsci-idea.",
      "next_route_when_accepted": "isomer-deepsci-idea"
    },
    "execution_choice": {
      "command_or_trusted_output_path": "Paper equations reproduced as Python/SymPy predictor in topic.repos.main; validation against host B200 measured runtime and NCU counters.",
      "environment_route": "Pixi-managed Python 3.11 environment with NumPy/SymPy/SciPy; host B200 for NCU validation.",
      "expected_outputs": [
        "Python predictor producing predicted_runtime_ms and predicted NCU trends",
        "Measured-vs-predicted runtime comparison on held-out validation set",
        "Bottleneck identification procedure"
      ],
      "expected_runtime_or_cost": "Low-medium; reproduction and extension are bounded to the forward-pass roofline and B200 parameters.",
      "smoke_or_direct_run_decision": "Direct verification of source identity, host spec, and repository state; no smoke run required for the comparator contract itself.",
      "why_this_path_is_sufficient": "The FA4 paper roofline is the recommended anchor in the baseline shortlist. Lighter routes (attach/import existing predictors) are unavailable because no verified white-box FA4 predictor exists locally or in registries.",
      "working_location": "topic.repos.main + repos/extern/flash-attention"
    },
    "objective": {
      "acceptance_target": "comparison-ready",
      "node_objective": "Secure a trustworthy comparator and metric contract before hypotheses and experiments proceed.",
      "success_condition": "A durable comparability contract and accepted baseline record exist, with explicit source identity, metric contract, caveats, and next route.",
      "user_constraints_that_change_comparability": "No measured runtime of query inputs may be used as a predictor; calibration constants must come from a disjoint calibration set."
    }
  },
  "status": "ready",
  "summary": "Comparator route record selecting reproduce/extend of the FlashAttention-4 paper roofline model for B200.",
  "title": "Comparator Route Record: FlashAttention-4 Roofline Baseline for B200"
}
```