# Reproduce the Paper

The final paper is at
`records/artifacts/research-records/evidence_item/final-three-round-paper-update.pdf`.
The experiments that generated its numbers are implemented as Python scripts
under `repos/topic-main/src/fa4_b200_predictor/`.

## 1. Generate the configuration matrix

```python
from fa4_b200_predictor.config_matrix import build_config_matrix

configs = build_config_matrix()
print(len(configs))   # 540 in the reported matrix
```

The matrix covers batch sizes `{1, 4, 8}`, head counts `{16, 32, 64}`,
sequence lengths `{1024, 2048, 4096, 8192, 16384}`, head dimensions `{64, 128}`,
causal/non-causal masks, and precisions `bf16`, `fp16`, and `fp8`.

## 2. Measure real B200 runtimes

```bash
cd repos/topic-main
pixi run python -m fa4_b200_predictor.real_hardware_benchmark
```

This script allocates Q/K/V tensors, runs warmup launches, and records median
runtimes. It requires a B200 and the `flash_attn.cute` build.

## 3. Run the improved experiment

```bash
cd repos/topic-main
pixi run python -m fa4_b200_predictor.run_improved_experiment
```

This calibrates `ImprovedPredictor` on the calibration split and reports
validation/query MAPE, within-30% coverage, and bottleneck accuracy.

## 4. Run the bottleneck-refinement experiment

```bash
pixi run python -m fa4_b200_predictor.run_bottleneck_refinement_experiment
```

This calibrates the NCU-guided slack on the profiled subset and reports the
final 100% NCU bottleneck accuracy.

## 5. Run the alternative-model experiments

```bash
cd repos/topic-main
pixi run python -m fa4_b200_predictor.component_saturate_experiment
```

This produces the Round 1/2/3 validation numbers documented in the paper.

## 6. Build the paper PDF

LaTeX sources are in the operator actor workspace. From the submodule:

```bash
cd actors/operator/isomer-managed/worker-output/topic-actors/operator/sets/20260706-round1-paper-update-055958
latexmk -pdf revised-draft.tex
```

A working LaTeX installation with the IEEEtran/PAMI class is required.
