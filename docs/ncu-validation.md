# NCU Validation

The bottleneck labels from the white-box model can be validated against
NVIDIA Compute Profiler (NCU) SpeedOfLight counters. The repository contains a
small profiling harness and a component-saturation experiment.

## Profile a single configuration

```python
from fa4_b200_predictor.config_matrix import FA4Config
from fa4_b200_predictor.ncu_profile import profile_config

cfg = FA4Config(batch=4, heads=32, seqlen=4096, head_dim=128, causal=True, precision="bf16")
result = profile_config(cfg, ncu_path="ncu")
print(result["ncu_bottleneck"])
print(result["sm_throughput_pct"])
print(result["memory_throughput_pct"])
```

`ncu_profile.py` runs the FA4 kernel under NCU's `SpeedOfLight` section and
parses the reported compute and memory throughput percentages.

## Calibrate the NCU slack

```python
from fa4_b200_predictor.improved_predictor import (
    ImprovedPredictor, calibrate_bottleneck_threshold,
)

predictor = ImprovedPredictor(...)
slack = calibrate_bottleneck_threshold(predictor, configs, measurements)
print(f"calibrated slack: {slack}")
```

`calibrate_bottleneck_threshold` sets the smallest slack that makes every
NCU-labelled compute-bound calibration config be labelled compute-bound by the
white-box model. In the paper this recovers `γ = 3.0`.

## Component-saturation experiment

`component_saturate_experiment.py` selects input shapes intended to saturate
specific parts of the critical path (Tensor Core, SFU, TMA, L2/HBM) and
records both model predictions and NCU counters. The results are summarized in
`records/artifacts/research-records/evidence_item/`.

## Notes

- NCU requires a physical NVIDIA GPU and appropriate permissions.
- The measured configs in this dataset were all reported as compute-bound by
  NCU, so the memory-bound side of the slack calibration has not been
  independently validated.
