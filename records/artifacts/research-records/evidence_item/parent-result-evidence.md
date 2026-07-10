<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/parent-result-evidence/v2
schema_ref: isomer:deepsci/record-format/schema/evidence/parent-result-evidence/v2
payload_digest: sha256:ca8c7c008e1806814608b0f061b77dd9e91a3209330b6c629ca1759bef26001a
-->
# Real-hardware experiment result: improved FA4 white-box runtime predictor

The refuted experiment 'fa4-b200-improved-launch-overhead-ncu-calibration-v1' measured 540 configurations on NVIDIA B200 (bf16/fp16/fp8; fp4 skipped) and NCU-profiled 60. The improved predictor cut MAPE dramatically versus both the combined original model and the baseline, but it fell short of the ≥75% NCU bottleneck-accuracy threshold.


```json
{
  "metadata": {
    "experiment_output_directory": "isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/actors/operator/isomer-managed/worker-output/topic-actors/operator/sets/20260704-183342-dataset-design-a1b2c3d4/real-hardware-improved-run",
    "recorded_at": "2026-07-04T21:01:22.593738Z"
  },
  "sections": {
    "calibration_params": {
      "fp8_mma_boost": 1.5,
      "hbm_factor": 3.0,
      "l2_factor": 1.5,
      "launch_fixed_us": 60.0,
      "launch_per_tile_us": 0.0,
      "mma_efficiency": 1.75,
      "mufu_efficiency": 1.1,
      "small_overhead_us": 0.0,
      "small_seqlen_threshold": 2048,
      "smem_factor": 0.9,
      "tma_factor": 3.0
    },
    "caveats": "- fp4 precision is not supported by the installed FA4 build and was skipped.\n- Bottleneck accuracy uses NCU SpeedOfLight compute/memory labels on a profiled subset; unprofiled configs are excluded from that metric.",
    "config_counts": {
      "calibration": 105,
      "error": 0,
      "generated": 540,
      "ncu_error": 0,
      "ncu_ok": 60,
      "ncu_profiled": 60,
      "ok": 540,
      "ok_calibration": 105,
      "ok_query": 330,
      "ok_validation": 105,
      "oom": 0,
      "query": 330,
      "validation": 105
    },
    "environment": {
      "cuda_version": "13.0",
      "device_name": "NVIDIA B200",
      "torch_version": "2.12.1+cu130"
    },
    "hypothesis_id": "fa4-b200-improved-launch-overhead-ncu-calibration-v1",
    "precisions_skipped": "fp4",
    "precisions_tested": "bf16, fp16, fp8",
    "query_metrics": {
      "baseline_mape": 43.12323317406717,
      "bottleneck_accuracy": 0.0,
      "delta_mape_pp": 33.11512703917594,
      "improved_mape": 10.008106134891227,
      "max_ape": 59.913861813349186,
      "n_configs": 330,
      "ncu_bottleneck_accuracy": 74.28571428571429,
      "ncu_profiled_count": 35,
      "pct_within_30": 96.36363636363636,
      "per_model": {
        "baseline_fa4_roofline": {
          "bottleneck_accuracy": 0.0,
          "mape": 43.12323317406717,
          "max_ape": 281.39327129644573,
          "n_configs": 330,
          "pct_within_30": 52.72727272727273
        },
        "improved": {
          "bottleneck_accuracy": 0.0,
          "mape": 10.008106134891227,
          "max_ape": 59.913861813349186,
          "n_configs": 330,
          "ncu_bottleneck_accuracy": 74.28571428571429,
          "ncu_profiled_count": 35,
          "pct_within_30": 96.36363636363636
        }
      }
    },
    "status": {
      "reason": "Improved predictor fails at least one useful-improvement threshold.",
      "status": "refuted"
    },
    "validation_metrics": {
      "baseline_mape": 55.64357557358759,
      "bottleneck_accuracy": 0.0,
      "delta_mape_pp": 43.021915740855896,
      "improved_mape": 12.621659832731694,
      "max_ape": 74.92812013573487,
      "n_configs": 105,
      "ncu_bottleneck_accuracy": 60.0,
      "ncu_profiled_count": 10,
      "pct_within_30": 93.33333333333333,
      "per_model": {
        "baseline_fa4_roofline": {
          "bottleneck_accuracy": 0.0,
          "mape": 55.64357557358759,
          "max_ape": 364.8441999680641,
          "n_configs": 105,
          "pct_within_30": 46.666666666666664
        },
        "improved": {
          "bottleneck_accuracy": 0.0,
          "mape": 12.621659832731694,
          "max_ape": 74.92812013573487,
          "n_configs": 105,
          "ncu_bottleneck_accuracy": 60.0,
          "ncu_profiled_count": 10,
          "pct_within_30": 93.33333333333333
        }
      }
    }
  },
  "status": "ready",
  "summary": "The refuted experiment 'fa4-b200-improved-launch-overhead-ncu-calibration-v1' measured 540 configurations on NVIDIA B200 (bf16/fp16/fp8; fp4 skipped) and NCU-profiled 60. The improved predictor cut MAPE dramatically versus both the combined original model and the baseline, but it fell short of the ≥75% NCU bottleneck-accuracy threshold.",
  "title": "Real-hardware experiment result: improved FA4 white-box runtime predictor"
}
```