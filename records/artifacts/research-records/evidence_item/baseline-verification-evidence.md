<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/baseline-verification-evidence/v1
schema_ref: isomer:deepsci/record-format/schema/evidence/baseline-verification-evidence/v1
payload_digest: sha256:b9a88e186b0648699d8b8f8c8e74a70e79728beb3a25a2874fe414cb86f17c2a
-->
# Baseline Verification Evidence: FlashAttention-4 Roofline Baseline for B200

Verification evidence for the accepted FlashAttention-4 roofline baseline comparator.


```json
{
  "metadata": {
    "consumer": "verification, accepted baseline, route decision",
    "placeholder": "\u003cBASELINE_VERIFICATION_EVIDENCE\u003e",
    "producer": "isomer-deepsci-baseline",
    "skill": "isomer-deepsci-baseline"
  },
  "sections": {
    "evidence": {
      "command_or_source": "Local inspection of host spec, repository clone, scout records, and paper/source references.",
      "dataset_and_split": "Synthetic configuration matrix; calibration ~20%, held-out validation ~20%, query inputs disjoint from both.",
      "deviations": [
        "B200-specific memory/occupancy/TMA terms must be added during reproduction/extension.",
        "Exact sustained HBM bandwidth and L2 transaction behavior require calibration measurements."
      ],
      "environment_facts": {
        "compute_capability": "10.0",
        "cuda_runtime": "13.1",
        "driver_version": "590.48.01",
        "gpu": "NVIDIA B200",
        "ncu_version": "2025.4.1.0",
        "peak_sm_clock_mhz": 1965
      },
      "metric_values": "No numeric runtime metrics exist yet; the comparator is a planned model. The metric contract, thresholds, and directions are inherited from artifact-EVALUATION_CONTRACT-7f255a5e6694.",
      "output_pointers": [
        "actors/operator/host-b200-spec.md",
        "repos/extern/flash-attention/README.md",
        "repos/extern/flash-attention/.git/HEAD (002cce0)",
        "records/artifacts/research-records/artifact/evaluation-contract.md",
        "records/artifacts/research-records/artifact/baseline-shortlist.md",
        "records/artifacts/research-records/artifact/literature-scouting-report.md"
      ],
      "required_metric_ids_and_directions": [
        "held_out_mape_predicted_runtime_ms -\u003e minimize",
        "max_absolute_percentage_error -\u003e minimize",
        "pct_validation_configs_within_30_pct_abs_error -\u003e maximize",
        "bottleneck_label_accuracy -\u003e maximize"
      ]
    },
    "route_and_comparator": {
      "acceptance_target": "comparison-ready",
      "baseline_id": "fa4-paper-roofline-b200",
      "baseline_variant": "default",
      "comparator_identity": "FlashAttention-4 Paper Roofline Model reproduced and extended for NVIDIA B200",
      "route": "reproduce / extend",
      "source_identity": "arXiv 2603.05451v1 + official flash-attention repository commit 002cce0"
    },
    "verdict": {
      "acceptance_or_route": "Accept the comparator contract and route to isomer-deepsci-idea.",
      "caveats": [
        "The model itself has not yet been implemented; only the source identity and metric contract are verified.",
        "Calibration data will be produced later and must be kept disjoint from validation and query inputs.",
        "MAPE threshold is proposed, not yet operator-approved."
      ],
      "next_action": "Proceed to isomer-deepsci-idea to implement and refine the white-box B200 runtime model against this comparator.",
      "verification_verdict": "trusted with caveats"
    }
  },
  "status": "ready",
  "summary": "Verification evidence for the accepted FlashAttention-4 roofline baseline comparator.",
  "title": "Baseline Verification Evidence: FlashAttention-4 Roofline Baseline for B200"
}
```