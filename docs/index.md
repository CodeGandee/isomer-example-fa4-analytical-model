# Analytical Model Documentation

This documentation explains how to use the white-box FlashAttention-4 runtime
models that ship with this repository. The models are implemented in
`repos/topic-main/src/fa4_b200_predictor/`.

## Main proposed model

The **main proposed model** is the **SASS-level RAW critical-path model**
(Round 3). It traces read-after-write instruction dependencies among TMA
loads, Tensor Core MMAs (`tcgen05.mma`), SFU `exp` operations, FP32
scale/update instructions, and the TMA store for one FA4 tile block. The goal
is to predict both runtime and the exact hardware component / execution path
that saturates for a given input.

A runnable approximation of this abstraction is provided by the
[node-saturation model](alternative-models.md) (`DetailedNodeModel`).

## What is here

- [Quick start](quickstart.md) — install the environment and run your first
  prediction.
- [Main predictor](main-predictor.md) — the fast roofline + launch-overhead
  model used for the 540-configuration B200 evaluation.
- [Alternative models](alternative-models.md) — node-saturation, sub-core
  partition, and SASS-level critical-path models.
- [NCU validation](ncu-validation.md) — profile kernels and compare the model's
  bottleneck labels with NVIDIA Compute Profiler data.
- [Reproduce the paper](reproduce-paper.md) — run the experiments that generated
  the results in the PDF.

## Recommended reading order

If you are new to the project, start with [Quick start](quickstart.md) and
[Main predictor](main-predictor.md). The
[research chatlogs](chatlogs/analysis/merged-timeline.md) provide the
narrative behind the design decisions.
