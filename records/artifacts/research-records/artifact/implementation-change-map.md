<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/code/implementation-change-map/v1
schema_ref: isomer:deepsci/record-format/schema/code/implementation-change-map/v1
payload_digest: sha256:cce9d470c4f1ff81e87f7d4be796567e4470c27ef09e314aae2e182dac646228
-->
# Implementation Change Map: Real-Hardware Benchmark Harness

Implementation change map for the real-hardware benchmark harness.


```json
{
  "metadata": {
    "consumer": "execution",
    "placeholder": "\u003cIMPLEMENTATION_CHANGE_MAP\u003e",
    "producer": "isomer-deepsci-experiment",
    "skill": "isomer-deepsci-experiment"
  },
  "sections": {
    "changes": [
      {
        "description": "Added a real-hardware benchmark harness that generates the dataset-design matrix, launches flash_attn_func on cuda:0, measures median runtime, splits calibration/validation/query, calibrates the combined predictor on calibration data only, and reports validation/query metrics.",
        "files_added": [
          "isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/src/fa4_b200_predictor/real_hardware_benchmark.py"
        ],
        "files_modified": [],
        "motivation": "The previous empirical pass used an emulator because torch and flash-attn were not installed. The environment is now ready, so real B200 kernel launches are required to validate the predictor.",
        "risk": "fp4 precision is unsupported by the installed FA4 build; the harness falls back to bf16/fp16/fp8. Tiny configs are dominated by launch overhead not modeled by the predictor."
      }
    ],
    "comparator_read_only": true,
    "summary": "Single-file addition of a real-hardware benchmark harness; no changes to existing predictor, calibrate, or evaluate modules."
  },
  "status": "ready",
  "summary": "Implementation change map for the real-hardware benchmark harness.",
  "title": "Implementation Change Map: Real-Hardware Benchmark Harness"
}
```