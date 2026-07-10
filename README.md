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

The research-record bundle also includes the cited reference PDFs used during scouting and analysis. The FlashAttention-4 paper and banner remain part of the pinned upstream checkout fetched by `scripts/setup-extern.sh`.

## Research Chatlogs

Sanitized, high-level analysis summaries from the original research sessions are
hosted in `chatlogs/`. The recommended entry point is the merged timeline,
rendered on GitHub Pages here:

- **Live site:** https://codegandee.github.io/isomer-example-fa4-analytical-model/chatlogs/analysis/merged-timeline/
- **Source:** [`chatlogs/analysis/merged-timeline.md`](chatlogs/analysis/merged-timeline.md)

Individual session summaries are in [`chatlogs/analysis/`](chatlogs/analysis/).

## The Analytical Model

This workspace contains several white-box models of FlashAttention-4 forward
attention on NVIDIA B200. The **main proposed model** is the **SASS-level RAW
critical-path model** (Round 3). It models the forward pass of one FA4 tile
block as a read-after-write (RAW) instruction dependency graph whose nodes are
SASS instruction classes:

- TMA loads for Q, K, V tiles,
- `tcgen05.mma` for the $QK^T$ and $PV$ Tensor Core contractions,
- SFU `exp` for the online softmax,
- FP32 scale/update instructions for the running $O$ accumulator,
- the TMA store of the final $O$ tile.

Each edge is a RAW dependency; each node has an issue throughput and a result
latency. The critical path is the throughput-limited schedule across the DAG
plus the longest latency chain. Per-iteration time is scaled across all KV
iterations, with the memory path overlapped using a stage-overlap factor. The
model therefore predicts not only runtime but *which* instruction class and
*which* dependency chain saturates for a given input.

The final calibrated SASS model reaches 21.16% validation MAPE on the small
16/8 B200 split. The paper argues that this level of detail is the right
abstraction for diagnosing which hardware component and execution path will be
the bottleneck.

### Runnable approximation: node-saturation model

The current code provides a concrete, runnable approximation of the SASS
abstraction in `DetailedNodeModel`
(`repos/topic-main/src/fa4_b200_predictor/detailed_node_model.py`). It treats
the forward pass as a sequence of hardware-node executions (TMA load, Tensor
Core MMA, SFU `exp`, FP32 FMA update, TMA store) and reports the predicted
saturated component and blocking path. On the small split it reaches 16.69%
validation MAPE and agrees with NCU component-saturation evidence (see
`component_saturate_experiment.py`).

### Sub-core partition scheduling model

Round 2 refines the per-SM reservation model by modelling each Blackwell SM as
four independent sub-core partitions. Warps are distributed across partitions,
and the SM makespan is the busiest partition's instruction schedule. It
reaches 16.41% validation MAPE on the small split and is useful for studying
intra-SM scheduler bottlenecks.

### Fast calibrated runtime predictor

For broad configuration matrices where the full instruction dependency graph is
not required, the repository also includes a fast roofline + launch-overhead
predictor (`repos/topic-main/src/fa4_b200_predictor/improved_predictor.py`).
This is the model used for the 540-configuration B200 evaluation and is the one
to reach for when you need a runtime estimate quickly.

#### Inputs and algorithm quantities

The predictor takes a configuration tuple

$$
(b, h, s, d, \text{causal}, p)
$$

where $b$ is batch size, $h$ is number of heads, $s$ is sequence length,
$d$ is head dimension, `causal` is a boolean mask flag, and $p$ is the
precision (bf16, fp16, fp8). From this input the code computes the algorithm
quantities in `predictor.py`:

| Quantity | Symbol | Formula |
|----------|--------|---------|
| Causal sequence factor | $\sigma$ | $0.5$ if causal, else $1.0$ |
| MMA FLOPs | $F_{\text{MMA}}$ | $4 \cdot b \cdot h \cdot s^2 \cdot d \cdot \sigma$ |
| Softmax ops | $E$ | $2 \cdot b \cdot h \cdot s^2 \cdot \sigma$ |
| HBM bytes | $B_{\text{HBM}}$ | $\text{bpe}(p) \cdot b \cdot h \cdot s \cdot d \cdot 4$ |
| L2 bytes | $B_{\text{L2}}$ | $\text{bpe}(p) \cdot b \cdot h \cdot s \cdot d \cdot 6 \cdot \sigma$ |
| SMEM bytes | $B_{\text{SMEM}}$ | $b \cdot h \cdot s \cdot d \cdot 8 \cdot \sigma$ |
| TMA bytes | $B_{\text{TMA}}$ | $\text{bpe}(p) \cdot b \cdot h \cdot s \cdot d \cdot 2.5 \cdot \sigma$ |

#### Roofline core

The baseline roofline is the maximum of the dominant-domain times:

$$
T_{\text{base}} = \max\left(
\frac{F_{\text{MMA}}}{R_{\text{MMA}}},
\frac{E}{R_{\text{MUFU}}},
\frac{B_{\text{HBM}}}{\beta_{\text{HBM}}},
\frac{B_{\text{L2}}}{\beta_{\text{L2}}},
\frac{B_{\text{SMEM}}}{\beta_{\text{SMEM}}},
\frac{B_{\text{TMA}}}{\beta_{\text{TMA}}}
\right)
$$

where $R_{\text{MMA}}$ and $R_{\text{MUFU}}$ are device-level peak Tensor
Core and special-function throughputs and the $\beta$ terms are effective
bandwidths.

#### Bounded corrections

The refined model adds three physically scoped corrections that are calibrated
on the calibration split only:

1. **Occupancy factor.** With output tiles $N_{\text{tiles}} = b \cdot h \cdot \lceil s / B_M \rceil \cdot \lceil s / B_N \rceil$ and active-warp fraction $\rho$, the occupancy efficiency is $\eta_{\text{occ}} = \min(1.0, 0.05 + 0.95 \sqrt{\rho})$.

2. **Transfer-size-dependent bandwidth.** Effective HBM, L2, and TMA bandwidths
   are functions of the total transfer size; the exact curves and multiplicative
   calibration factors are in `predictor.py` and `improved_predictor.py`.

3. **Precision-specific throughput.** Per-precision MMA and MUFU rate tables
   are stored in `constants.py` and scaled by $\eta_{\text{occ}}$ and bounded
   efficiency factors.

#### Launch-overhead term

The dominant correction when moving from emulator to real B200 silicon is a
fixed kernel dispatch latency:

$$
T_{\text{launch}} = \tau_{\text{fixed}} + \tau_{\text{per-tile}} \cdot N_{\text{tiles}}
$$

Calibration recovers $\tau_{\text{fixed}} = 60 \mu\text{s}$ and
$\tau_{\text{per-tile}} = 0 \mu\text{s}$. The final runtime is
$T_{\text{pred}} = T_{\text{base}} + T_{\text{launch}}$.

#### Bottleneck label with NCU slack

The model labels the bottleneck as the domain with the largest individual time.
Because NCU SpeedOfLight reports every profiled FA4 config as compute-bound even
when the raw white-box memory time is comparable, we add an NCU-guided slack
$\gamma = 3.0$: if the dominant memory time is within a factor
$(1 + \gamma)$ of the dominant compute time, the config is labelled
compute-bound. This slack changes only the label, not the predicted runtime.

#### Accuracy

On 540 real B200 configurations (20% calibration, 20% validation, 60% query):

| Metric | Value |
|--------|-------|
| Validation MAPE | 12.62% |
| Query MAPE | 10.01% |
| Validation within 30% | 93.3% |
| Query within 30% | 96.4% |
| NCU bottleneck accuracy | 100% on both splits |

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
├── skillset/toolboxes/         # Active GPU analytical-modeling Toolbox
├── chatlogs/                   # Sanitized analysis summaries
├── scripts/
│   ├── setup-extern.sh         # Clone upstream simulator dependencies
│   └── update-sanitized-export.py # Refresh safe workspace content
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

## Sanitized Export Maintenance

Maintainers can refresh the public records, source package, workspace metadata, and active project-local Toolbox from a local Topic Workspace with `scripts/update-sanitized-export.py <source-workspace>`. The script excludes runtime databases and generated caches, replaces host-specific paths with placeholders, and recomputes structured-record payload digests after sanitization. The actor workspace remains a separate branch and must be reviewed and updated independently before advancing the submodule pointer.

## License

See [LICENSE](LICENSE).
