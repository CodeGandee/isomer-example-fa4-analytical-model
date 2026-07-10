<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/experiment-result-summary/v2
schema_ref: isomer:deepsci/record-format/schema/evidence/experiment-result-summary/v2
payload_digest: sha256:fa0955dba87128d21c9aa036a41032a1703b935346183ac9dabce0565de0428c
-->
# Experiment Result Summary: Real-Hardware Validation of the FA4 B200 Predictor

Real B200 measurements refute the selected hypothesis: the combined predictor fails the useful-improvement threshold.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-analysis, decision, optimize, finalize",
    "placeholder": "<EXPERIMENT_RESULT_SUMMARY>",
    "producer": "isomer-deepsci-experiment",
    "skill": "isomer-deepsci-experiment"
  },
  "sections": {
    "ablations_summary": {
      "baseline_fa4_roofline": {
        "bottleneck_accuracy": 89.44,
        "mape": 42.1,
        "pct_within_30": 51.67
      },
      "combined": {
        "bottleneck_accuracy": 89.44,
        "mape": 62.14,
        "pct_within_30": 47.22
      },
      "occupancy_only": {
        "bottleneck_accuracy": 100.0,
        "mape": 42.1,
        "pct_within_30": 51.67
      },
      "precision_only": {
        "bottleneck_accuracy": 100.0,
        "mape": 42.1,
        "pct_within_30": 51.67
      },
      "tma_l2_effective_bw": {
        "bottleneck_accuracy": 89.44,
        "mape": 52.03,
        "pct_within_30": 52.22
      }
    },
    "baseline_relation": "worse",
    "caveats": [
      "Real B200 kernel launches expose launch overhead and small-kernel latency that the white-box predictor does not model, inflating error on configs below ~0.2 ms measured runtime.",
      "measured_bottleneck is a white-box proxy from the uncalibrated baseline predictor because hardware counters were not collected.",
      "fp4 precision is not supported by the installed FA4 build (flash-attn-4==0.0.1.dev1+g002cce0a1) and was skipped; coverage is reduced to bf16/fp16/fp8.",
      "The combined model was calibrated only on hbm_factor, mma_efficiency, mufu_efficiency, and launch_overhead_us; l2_factor, tma_factor, and smem_factor were held at defaults."
    ],
    "claim_update": "The selected hypothesis is refuted on real B200 hardware: the combined predictor fails the useful-improvement threshold and performs worse than the uncalibrated baseline.",
    "claim_verdict": "refuted",
    "comparability": "Same configuration matrix and split recipe as the emulator-based experiment, but ground truth is now real B200 flash_attn_func median runtime rather than emulator output. Precision coverage is reduced from four formats to three because fp4 is unsupported.",
    "failure_mode": "The white-box model under-predicts runtime on small configs (launch-overhead dominated) and over-predicts on large configs, producing a combined MAPE of 62.1% versus 42.1% for the baseline.",
    "intervention": "Ran flash_attn_func from flash_attn.cute on cuda:0 for 864 configs (bf16/fp16/fp8), measured median wall-clock runtime with 3 warmup + 10 timed runs, and calibrated the existing combined predictor on the 20% calibration split only.",
    "metrics": {
      "baseline_mape": 42.100286872399245,
      "bottleneck_accuracy": 89.44444444444444,
      "combined_mape": 62.14468575323019,
      "delta_mape_pp": -20.044398880830947,
      "max_ape": 600.5116170863935,
      "n_validation_configs": 180,
      "pct_within_30": 47.22222222222222
    },
    "next_action": "Proceed to isomer-deepsci-analysis to identify the transfer gaps between emulator and real hardware and decide whether the predictor needs additional terms or a different calibration strategy.",
    "primary_metric": "held_out_mape_predicted_runtime_ms",
    "research_question": "Does the existing white-box predictor (fa4-b200-whitebox-occupancy-tma-l2-precision-v1) achieve the useful-improvement threshold when validated against real B200 FlashAttention-4 forward-pass measurements?",
    "selected_hypothesis_id": "fa4-b200-whitebox-occupancy-tma-l2-precision-v1-real-hardware",
    "takeaway": "Real B200 measurements refute the hypothesis. The combined predictor does not meet the useful-improvement threshold; its MAPE is 20 percentage points worse than the baseline, primarily because the model misses launch-overhead-dominated small-config behavior and its calibrated efficiency factors do not generalize to real kernel scheduling."
  },
  "status": "ready",
  "summary": "Real B200 measurements refute the selected hypothesis: the combined predictor fails the useful-improvement threshold.",
  "title": "Experiment Result Summary: Real-Hardware Validation of the FA4 B200 Predictor"
}
```