<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/draft/pre-idea-draft/v1
schema_ref: isomer:deepsci/record-format/schema/draft/pre-idea-draft/v1
payload_digest: sha256:27170416e3cf0fd056dbe64c93a0613cca483d8f169c443b7a98496df77ecedb
-->
# Pre-Idea Draft: Combined Occupancy/TMA-L2/Precision Analytical Predictor

Pre-idea draft for candidate C1.


```json
{
  "metadata": {
    "consumer": "selection gate",
    "placeholder": "\u003cPRE_IDEA_DRAFT\u003e",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "abandonment_condition": "After two calibration rounds, the combined model fails to beat baseline MAPE by \u003e= 5 percentage points or falls below the useful-improvement threshold (MAPE \u003c= 25%, \u003e= 75% within 30%, \u003e= 75% bottleneck accuracy).",
    "candidate_id": "C1",
    "closest_prior_work": "arXiv 2603.05451v1 (seed roofline), arXiv 2605.04178v1 (occupancy/memory corrections), arXiv 2512.02189v1 (Blackwell constants).",
    "falsification_path": "Implement the combined model and each single-term ablation; evaluate on held-out validation; if the combined model does not beat the baseline, the hypothesis is falsified.",
    "family": "model",
    "hidden_assumptions": [
      "FA4 source uses tile sizes and launch bounds that can be read or inferred from repos/extern/flash-attention.",
      "B200 sustained HBM bandwidth and L2 efficiency can be calibrated from a disjoint calibration split without leaking validation data.",
      "The dominant errors are additive white-box terms rather than implementation-specific scheduling noise."
    ],
    "hypothesis": "A combined analytical predictor with modular occupancy, TMA/L2 effective bandwidth, and precision throughput terms will achieve held-out MAPE \u003c= 25% and beat the FA4 paper roofline baseline by \u003e= 5 percentage points MAPE on the held-out validation set.",
    "local_optimum_risk": "Medium \u2014 the route is a natural extension of the accepted baseline, but it is also the most obvious one. The ablation design (C2, C3) guards against pretending a combined model works when only one term matters.",
    "minimal_experiment": "Build predictor.py in topic.repos.main with modular terms; calibrate constants on calibration split; evaluate MAPE, max APE, 30%-error coverage, and bottleneck-label accuracy on held-out validation; compare to baseline predictor.",
    "novelty_type": "incremental but valuable \u2014 first local B200/FA4 instantiation of known GPU-modeling corrections with explicit falsification.",
    "one_sentence_claim": "Adding tile-occupancy, TMA/L2 effective bandwidth, and precision-specific MMA/exponential terms to the FA4 paper roofline will reduce held-out MAPE below the baseline on B200.",
    "outside_family_alternative": "C2 (precision-only) and C3 (occupancy-only) isolate the terms; if C1 fails, one of these may still reveal the true bottleneck.",
    "strongest_rejection_case": "The FA4 kernel is already well-tuned for B200, so occupancy is near peak and memory bandwidth is saturated; adding these terms yields no improvement and the real error is scheduling/launch overhead that the white-box model cannot capture.",
    "targeted_bottleneck": "FA4 paper roofline overestimates utilization and underestimates runtime because it omits occupancy, memory-hierarchy bandwidth, and precision throughput effects.",
    "verdict": "promote",
    "why_now": "The accepted baseline explicitly lists these omissions as caveats, and the comparability contract defines the exact calibration constants needed to test them."
  },
  "status": "ready",
  "summary": "Pre-idea draft for candidate C1.",
  "title": "Pre-Idea Draft: Combined Occupancy/TMA-L2/Precision Analytical Predictor"
}
```