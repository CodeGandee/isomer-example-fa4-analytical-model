# Main Predictor

The main proposed model is `fa4_b200_predictor.improved_predictor.ImprovedPredictor`.
It combines a roofline workload breakdown with bounded corrections for
occupancy, transfer-size-dependent bandwidth, precision-specific throughput,
and a fixed launch-overhead term.

## Inputs

The predictor takes a `FA4Config`:

```python
from fa4_b200_predictor.config_matrix import FA4Config

cfg = FA4Config(
    batch=4,
    heads=32,
    seqlen=4096,
    head_dim=128,
    causal=True,
    precision="bf16",   # "bf16", "fp16", or "fp8"
)
```

## Run a prediction

```python
from fa4_b200_predictor.improved_predictor import default_improved_predictor

pred = default_improved_predictor().predict(cfg)
print(pred["predicted_runtime_ms"])
print(pred["predicted_bottleneck"])
```

The returned dictionary contains:

| Key | Meaning |
|-----|---------|
| `predicted_runtime_ms` | Estimated kernel runtime in milliseconds |
| `predicted_bottleneck` | Dominant stage label (`mma`, `mufu`, `hbm`, `l2`, `smem`, `tma`) |
| `mma_time_us` | Tensor Core compute time |
| `mufu_time_us` | SFU/softmax compute time |
| `hbm_time_us`, `l2_time_us`, `smem_time_us`, `tma_time_us` | Memory-domain times |
| `launch_overhead_us` | Fixed + per-tile overhead |
| `occupancy_fraction` | Active-warps fraction used for the occupancy correction |

## Calibrated parameters from the paper

The final refined predictor uses the parameters recovered by the bounded grid
search on the calibration split:

```python
from fa4_b200_predictor.improved_predictor import ImprovedPredictor

predictor = ImprovedPredictor(
    hbm_factor=3.0,
    l2_factor=1.5,
    smem_factor=0.9,
    tma_factor=3.0,
    mma_efficiency=1.75,
    mufu_efficiency=1.1,
    fp8_mma_boost=1.5,
    launch_fixed_us=60.0,
    launch_per_tile_us=0.0,
    bottleneck_mem_slack=3.0,
)
```

`bottleneck_mem_slack` changes only the label, not the runtime.

## Evaluate on a configuration matrix

```python
from fa4_b200_predictor.config_matrix import build_config_matrix
from fa4_b200_predictor.evaluate import evaluate_predictions

configs = build_config_matrix()
predictions = [predictor.predict(c)["predicted_runtime_ms"] for c in configs]
# compare with measured runtimes via evaluate_predictions(...)
```

See `repos/topic-main/src/fa4_b200_predictor/run_improved_experiment.py` for the
full calibration/evaluation loop used in the paper.

## Interpreting the bottleneck label

The raw bottleneck label is the stage with the largest individual time. Because
NCU SpeedOfLight reports every profiled FA4 config as compute-bound, the model
adds a calibrated slack: if the dominant memory time is within a factor
`(1 + bottleneck_mem_slack)` of the dominant compute time, the config is
labelled compute-bound. Set `bottleneck_mem_slack=0.0` to get the strict
white-box label.
