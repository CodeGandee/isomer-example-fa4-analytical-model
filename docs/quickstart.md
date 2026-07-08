# Quick Start

This repository contains a Pixi-managed Python environment and a small
FlashAttention-4 predictor package. You can run the models without a GPU for
the analytical prediction path; measuring real runtimes requires a CUDA-capable
NVIDIA Blackwell (B200) machine.

## 1. Clone and set up the workspace

```bash
git clone https://github.com/CodeGandee/isomer-example-fa4-analytical-model.git
cd isomer-example-fa4-analytical-model
git submodule update --init
pixi install
```

The actor submodule (`actors/operator`) is needed only if you want to rebuild
the paper or inspect the original operator workspace.

## 2. Run a smoke test

```bash
pixi run test
```

This imports the `fa4_b200_predictor` package and prints a short smoke-test
message.

## 3. Predict one configuration

```bash
pixi run python - <<'PY'
from fa4_b200_predictor.improved_predictor import default_improved_predictor
from fa4_b200_predictor.config_matrix import FA4Config

cfg = FA4Config(batch=4, heads=32, seqlen=4096, head_dim=128, causal=True, precision="bf16")
pred = default_improved_predictor().predict(cfg)
print(f"predicted runtime: {pred['predicted_runtime_ms']:.3f} ms")
print(f"predicted bottleneck: {pred['predicted_bottleneck']}")
PY
```

`default_improved_predictor()` is the uncalibrated version of the model; for
the calibrated parameters used in the paper, see
[Main predictor](main-predictor.md).

## 4. (Optional) Fetch upstream dependencies

If you want to run the real-hardware measurement harness or the simulator
experiments, fetch the exact upstream commits used in the original topic:

```bash
./scripts/setup-extern.sh
```

This clones `flash-attention` and `accel-sim-framework` into `repos/extern/`
without bloating the example repository.
