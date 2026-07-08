# Isomer Example: FlashAttention-4 White-Box Analytical Model

This repository is a sanitized, reproducible example of an Isomer Labs research
topic workspace. It contains the source code, analytical models, experiments,
records, and paper drafts for a FlashAttention-4 white-box runtime model
targeting NVIDIA Blackwell GPUs.

> **Note:** Host-specific identifiers have been replaced with placeholders:
> `<USER>`, `<GPU_HOST>`, `<PROJECT_ROOT>`, `<NCU_PATH>`. Update them in your
> local copy before running hardware-dependent experiments.

## Paper

The final compiled paper is available at:
[`records/artifacts/research-records/evidence_item/final-three-round-paper-update.pdf`](records/artifacts/research-records/evidence_item/final-three-round-paper-update.pdf)

LaTeX sources and intermediate revisions live in the operator actor workspace
under `actors/operator/isomer-managed/worker-output/...`.

## Research Chatlogs

Sanitized, high-level analysis summaries from the original research sessions are
hosted in `chatlogs/`. The recommended entry point is the merged timeline:

- [`chatlogs/analysis/merged-timeline.md`](chatlogs/analysis/merged-timeline.md)

Individual session summaries are in [`chatlogs/analysis/`](chatlogs/analysis/).
The chatlogs are also published as a GitHub Pages site (see `mkdocs.yml`).

## The Analytical Model

This workspace contains several white-box models of FlashAttention-4 forward
attention on NVIDIA B200. The **main proposed model** is the refined
real-hardware predictor implemented in
`repos/topic-main/src/fa4_b200_predictor/improved_predictor.py`. It is the model
used for the 540-configuration evaluation and is the one we recommend using.

### Inputs and algorithm quantities

The predictor takes a configuration tuple

\[
(b, h, s, d, 	ext{causal}, p)
\]

where \(b\) is batch size, \(h\) is number of heads, \(s\) is sequence length,
\(d\) is head dimension, `causal` is a boolean mask flag, and \(p\) is the
precision (bf16, fp16, fp8). From this input the code computes the algorithm
quantities in `predictor.py`:

| Quantity | Symbol | Formula |
|----------|--------|---------|
| Causal sequence factor | \(\sigma\) | \(0.5\) if causal, else \(1.0\) |
| MMA FLOPs | \(F_{	ext{MMA}}\) | \(4 \cdot b \cdot h \cdot s^2 \cdot d \cdot \sigma\) |
| Softmax ops | \(E\) | \(2 \cdot b \cdot h \cdot s^2 \cdot \sigma\) |
| HBM bytes | \(B_{	ext{HBM}}\) | \(	ext{bpe}(p) \cdot b \cdot h \cdot s \cdot d \cdot 4\) |
| L2 bytes | \(B_{	ext{L2}}\) | \(	ext{bpe}(p) \cdot b \cdot h \cdot s \cdot d \cdot 6 \cdot \sigma\) |
| SMEM bytes | \(B_{	ext{SMEM}}\) | \(b \cdot h \cdot s \cdot d \cdot 8 \cdot \sigma\) |
| TMA bytes | \(B_{	ext{TMA}}\) | \(	ext{bpe}(p) \cdot b \cdot h \cdot s \cdot d \cdot 2.5 \cdot \sigma\) |

### Roofline core

The baseline roofline is the maximum of the dominant-domain times:

\[
T_{	ext{base}} = \max\left(
rac{F_{	ext{MMA}}}{R_{	ext{MMA}}},
rac{E}{R_{	ext{MUFU}}},
rac{B_{	ext{HBM}}}{eta_{	ext{HBM}}},
rac{B_{	ext{L2}}}{eta_{	ext{L2}}},
rac{B_{	ext{SMEM}}}{eta_{	ext{SMEM}}},
rac{B_{	ext{TMA}}}{eta_{	ext{TMA}}}
ight)
\]

where \(R_{	ext{MMA}}\) and \(R_{	ext{MUFU}}\) are device-level peak Tensor
Core and special-function throughputs and the \(eta\) terms are effective
bandwidths.

### Bounded corrections

The refined model adds three physically scoped corrections that are calibrated
on the calibration split only:

1. **Occupancy factor.** With output tiles
   \(
   N_{	ext{tiles}} = b \cdot h \cdot \lceil s / B_M ceil \cdot \lceil s / B_N ceil
   \)
   and active-warp fraction \(ho\), the occupancy efficiency is
   \(
   \eta_{	ext{occ}} = \min(1.0,\; 0.05 + 0.95 \sqrt{ho})
   \).

2. **Transfer-size-dependent bandwidth.** Effective HBM, L2, and TMA bandwidths
   are functions of the total transfer size; the exact curves and multiplicative
   calibration factors are in `predictor.py` and `improved_predictor.py`.

3. **Precision-specific throughput.** Per-precision MMA and MUFU rate tables
   are stored in `constants.py` and scaled by \(\eta_{	ext{occ}}\) and bounded
   efficiency factors.

### Launch-overhead term

The dominant correction when moving from emulator to real B200 silicon is a
fixed kernel dispatch latency:

\[
T_{	ext{launch}} = 	au_{	ext{fixed}} + 	au_{	ext{per-tile}} \cdot N_{	ext{tiles}}
\]

Calibration recovers \(	au_{	ext{fixed}} = 60\,\mu	ext{s}\) and
\(	au_{	ext{per-tile}} = 0\,\mu	ext{s}\). The final runtime is
\(T_{	ext{pred}} = T_{	ext{base}} + T_{	ext{launch}}\).

### Bottleneck label with NCU slack

The model labels the bottleneck as the domain with the largest individual time.
Because NCU SpeedOfLight reports every profiled FA4 config as compute-bound even
when the raw white-box memory time is comparable, we add an NCU-guided slack
\(\gamma = 3.0\): if the dominant memory time is within a factor
\((1 + \gamma)\) of the dominant compute time, the config is labelled
compute-bound. This slack changes only the label, not the predicted runtime.

### Accuracy

On 540 real B200 configurations (20% calibration, 20% validation, 60% query):

| Metric | Value |
|--------|-------|
| Validation MAPE | 12.62% |
| Query MAPE | 10.01% |
| Validation within 30% | 93.3% |
| Query within 30% | 96.4% |
| NCU bottleneck accuracy | 100% on both splits |

### Alternative execution-flow models

The paper also documents three progressively more detailed execution-flow
models that expose *which* hardware unit saturates and *which* execution path
blocks. They are implemented in
`repos/topic-main/src/fa4_b200_predictor/detailed_node_model.py` and are kept as
alternatives rather than the main proposed predictor:

- **Node-saturation / per-SM reservation model** (Round 1) names the saturating
  unit (Tensor Core, SFU, FP pipe, TMA) and reaches 16.69% validation MAPE on a
  small 16/8 split.
- **Sub-core partition scheduling model** (Round 2) models each SM as four
  independent partitions and reaches 16.41% validation MAPE.
- **SASS-level RAW critical-path model** (Round 3) traces instruction
  dependencies and reaches 21.16% validation MAPE.

These models are useful for diagnosis; the refined roofline + launch-overhead
predictor is the recommended model for runtime prediction.

## Repository Layout

```
.
├── repos/
│   ├── topic-main/             # Main development repository
│   │   ├── src/fa4_b200_predictor/
│   │   └── isomer-managed/
│   └── extern/                 # Upstream deps (fetched on demand)
│       ├── flash-attention/
│       └── accel-sim-framework/
├── actors/
│   └── operator/               # Operator actor workspace (submodule)
├── records/                    # Research records and evidence
├── intent/                     # Topic intent and environment gates
├── chatlogs/                   # Sanitized analysis summaries
├── scripts/
│   └── setup-extern.sh         # Clone upstream simulator dependencies
├── pixi.toml / pixi.lock       # Reproducible Python environment
└── README.md                   # This file
```

## Quick Start

1. Clone the repository and initialize the actor submodule:

   ```bash
   git clone https://github.com/CodeGandee/isomer-example-fa4-analytical-model.git
   cd isomer-example-fa4-analytical-model
   git submodule update --init
   ```

2. Fetch upstream simulator dependencies:

   ```bash
   ./scripts/setup-extern.sh
   ```

3. Install the Pixi environment:

   ```bash
   pixi install
   ```

4. Run tests:

   ```bash
   pixi run test
   ```

5. Build the paper (requires a working LaTeX installation):

   ```bash
   cd actors/operator/isomer-managed/worker-output/topic-actors/operator/sets/20260706-round1-paper-update-055958
   latexmk -pdf revised-draft.tex
   ```

## Submodules and External Dependencies

- `actors/operator` is a Git submodule pointing to this same repository on the
  `actor-operator` branch, preserving the original Isomer actor-worktree
  topology.
- `repos/extern/flash-attention` and `repos/extern/accel-sim-framework` are
  *not* submodules. They are cloned on demand by `scripts/setup-extern.sh` at
  the exact commits used in the original topic, keeping the example repo small.

To update the actor submodule:

```bash
git submodule update --init --remote
```

## License

See [LICENSE](LICENSE).
