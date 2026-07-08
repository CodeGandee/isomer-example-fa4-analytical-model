# Scout Context Brief

## Research Topic

`flash-attention-4-whitebox-runtime-model` — Flash Attention 4 White-Box Runtime Model.

## Task Frame

Build a white-box, hardware-grounded predictor that estimates Flash Attention 4 **forward-pass** kernel runtime in milliseconds from an input configuration, without executing the kernel for the queried input. The predictor must trace every latency term to a concrete NVIDIA Blackwell B200 hardware limit or instruction-level bound.

Scope from the Topic Workspace:

- **GPU target**: NVIDIA B200, single GPU.
- **Precisions**: BF16, FP16, FP8, FP4.
- **Input configuration space**: batch size, number of heads, sequence length, head dimension, causal/non-causal mask, precision.
- **Excluded**: backward pass, multi-GPU/tensor-parallel configurations.
- **Allowed validation**: Nsight Compute (`ncu`) and measured kernel runs on the host B200, but only as calibration/validation evidence, not as a prediction input.

## Current Comparator Status

No existing white-box Flash Attention 4 runtime predictor is present in the Topic Workspace or in the cloned official repository. The FlashAttention-4 paper provides a simplified forward-pass roofline analysis (MMA, shared-memory traffic, exponential unit) that can serve as the seed comparator. The host B200 can supply measured ground-truth runtimes and NCU counter traces for calibration and validation.

## Evidence Already Available

- `intent/src/topic-overview.md`: scope, do's/don'ts, expected outcomes.
- `intent/src/topic-env-gate.md`: environment requirements and success criteria.
- `actors/operator/host-b200-spec.md`: host B200 driver, clocks, compute capability, `ncu` version.
- `repos/extern/flash-attention`: official Flash Attention repository for algorithm and tile/warp scheduling details.
- `repos/extern/flash-attention/flash_attn/cute/`: CuTe-DSL FA4 implementation area.
- arXiv 2603.05451v1, *FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling*: forward-pass roofline formulas, B200 throughput numbers, TMEM/TMA/2-CTA details, exponential emulation, conditional softmax rescaling.
- arXiv 2512.02189v1, *Microbenchmarking NVIDIA's Blackwell Architecture*: measured shared-memory bandwidth (128 bytes/clock/SM) and MUFU throughput (16 ops/clock/SM) on Blackwell.
- arXiv 2605.04178v1, *Microbenchmark-Driven Analytical Performance Modeling Across Modern GPU Architectures*: methodology for white-box GPU analytical models.

## Blockers

None for routing to `isomer-deepsci-baseline`. Residual unknowns about exact B200 sustained bandwidth, FA4 tile defaults per precision, and the numeric accuracy target remain, but they affect baseline model construction rather than the route decision.
