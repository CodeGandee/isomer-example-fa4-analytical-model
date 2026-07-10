<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/run/main-run-record/v2
schema_ref: isomer:deepsci/record-format/schema/run/main-run-record/v2
payload_digest: sha256:1f1433f26cbe645664b2bfd17477d26eefe28f037fd78a010af906b6255a4ea1
-->
# Main Run Record: Real-Hardware FA4 B200 Benchmark

Main real-hardware measurement run for the FA4 B200 predictor hypothesis pass.


```json
{
  "metadata": {
    "consumer": "analysis, decision, optimize, finalize",
    "placeholder": "<MAIN_RUN_RECORD>",
    "producer": "isomer-deepsci-experiment",
    "skill": "isomer-deepsci-experiment"
  },
  "sections": {
    "command": "PYTHONPATH=<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/src CUDA_VISIBLE_DEVICES=0 <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/.pixi/envs/default/bin/python fa4_b200_predictor/real_hardware_benchmark.py --output-dir <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/actors/operator/isomer-managed/worker-output/topic-actors/operator/sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark",
    "config": {
      "calibration_frac": 0.2,
      "calibration_rounds": 2,
      "device": "cuda:0",
      "seed": 20260704,
      "skip_unsupported_precisions": true,
      "timed_runs": 10,
      "validation_frac": 0.2,
      "warmup_runs": 3
    },
    "environment": {
      "cuda_version": "13.0",
      "device_name": "NVIDIA B200",
      "flash_attn_version": "0.0.1.dev1+g002cce0a1",
      "torch_version": "2.12.1+cu130"
    },
    "outputs": [
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/experiment_result.json",
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/all_measurements.json",
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/all_measurements.csv",
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/calibration_params.json",
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/validation_metrics/validation_metrics.json",
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/validation_metrics/validation_metrics.csv",
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/query_metrics/query_metrics.json",
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/query_metrics/query_metrics.csv",
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/combined_validation_predictions.csv",
      "sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/combined_query_predictions.csv"
    ],
    "run_id": "real-hardware-benchmark-20260704-184139",
    "runtime_seconds": 222.0,
    "seed": 20260704,
    "status": "completed",
    "summary": "Real B200 measurement run for 864 FlashAttention-4 configs (bf16/fp16/fp8). All configs completed without OOM or error. Calibration and evaluation completed.",
    "wall_clock_end": "2026-07-04T18:45:21Z",
    "wall_clock_start": "2026-07-04T18:41:39Z"
  },
  "status": "ready",
  "summary": "Main real-hardware measurement run for the FA4 B200 predictor hypothesis pass.",
  "title": "Main Run Record: Real-Hardware FA4 B200 Benchmark"
}
```