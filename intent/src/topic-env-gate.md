# Topic Environment Gate: Flash Attention 4 White-Box Runtime Model

This gate captures what the Topic Workspace must be able to run or reference before modeling work proceeds. Because the goal is a hardware-grounded white-box model, the environment is primarily analytical and documentation-driven, not kernel-execution-driven.

## Runnable Requirements

- A Python environment capable of symbolic/numeric modeling (NumPy, SymPy, SciPy, or equivalent) for prototyping the runtime equations, probabilistic sub-models, and the Python predictor.
- The NVIDIA B200 GPU specification and microbenchmark literature (memory bandwidth, TMEM, TMA, shared-memory bandwidth per SM, Tensor Core throughput per SM, SM count, clock frequency, warp size, occupancy limits), with the baseline clock/mem/driver/CUDA configuration derived from this host.
- A local checkout or read-only reference of the official Flash Attention repository for the forward-pass algorithm and tile/warp scheduling details.
- Access to the FlashAttention-4 paper for B200-specific pipeline details.
- Access to the host NVIDIA B200 GPUs and Nsight Compute (`ncu`) for collecting SM/cache-level counters to validate the model.

## Expected Repositories

- `topic.repos.main` (already created) for the model document, derivations, Python predictor, and validation plan.
- A local mirror or read-only reference of `https://github.com/Dao-AILab/flash-attention` for algorithm details.
- Optional: a local mirror or read-only reference of `https://github.com/NVIDIA/cutlass` for GPU kernel cost-model patterns.

## Datasets

- No dataset is required for the white-box model itself.
- Optional calibration/validation data: published Flash Attention 4 benchmark tables or Nsight Compute (`ncu`) profiles collected on the host B200 for specific input shapes and precisions, used to compare predicted runtime and predicted NCU counter trends against measurements.

## Libraries and Tools

- Python 3.11+ with NumPy, SymPy, SciPy, and a Markdown renderer (or small alternatives) for closed-form and probabilistic modeling.
- Git for acquiring the Flash Attention source repository.
- Nsight Compute (`ncu`) on the host B200 for collecting SM, cache, and memory-counter traces to validate the white-box model; predictions must still be derivable without these measurements.

## Runtime Assumptions

- The primary target GPU is the NVIDIA B200; the model should be parameterizable so it can be retargeted.
- The baseline B200 configuration (clock, memory bandwidth, driver/CUDA version) will be derived from this host.
- The model covers the Flash Attention 4 forward pass only on a single GPU; backward-pass and multi-GPU modeling are explicitly out of scope.
- The model supports BF16, FP16, FP8, and FP4 precisions.
- Stochastic behaviors modeled probabilistically include cache hit/miss, shared-memory bank conflicts, occupancy jitter, and TMA latency variance.
- The host B200 GPUs are available for NCU validation runs; predictions must not require executing Flash Attention 4 on them.
- NCU runs are treated as validation/calibration evidence, not as inputs the prediction formula requires.
- The workspace will store derivations, assumptions, the Python predictor, and predicted runtime formulas under `topic.repos.main`.

## Unavailable Resources

- A dedicated Flash Attention 4 hardware test harness is not assumed.
- Measured kernel traces for every input shape are not assumed; any measurements used will be explicit calibration/validation points.

## Success Criteria

- The Topic Workspace contains a readable white-box runtime model that maps input shapes, precision, and B200 parameters to `predicted_runtime_ms`.
- Each term in the model traces to a hardware limit or instruction-level bound.
- The B200 system architecture and execution flow relevant to Flash Attention 4 forward pass are documented.
- Closed-form formulas are provided for each modeled subsystem/stage.
- Probabilistic sub-models are provided for the specified stochastic behaviors.
- A runnable Python predictor produces `predicted_runtime_ms` and predicted NCU counter trends from input configuration and precision.
- A measured-vs-predicted runtime comparison and a measured-vs-predicted NCU counter trend comparison are documented.
- A bottleneck identification procedure is documented.
- Assumptions and limitations are listed explicitly.

## Open Setup Questions

- Resolved: use the official Flash Attention repository as the algorithm source.
- Resolved: implement a runnable Python predictor plus a structured Markdown derivation.
- Resolved: derive the B200 baseline clock/mem/driver/CUDA configuration from this host.
- Resolved: model cache hit/miss, shared-memory bank conflicts, occupancy jitter, and TMA latency variance probabilistically.
- Resolved: support BF16, FP16, FP8, and FP4 precisions.
- Resolved: target single-GPU execution only.

## Source Material

- User-supplied topic statement: develop a white-box math model of Flash Attention 4 runtime that predicts kernel runtime in milliseconds from input configuration, following the GPU's internal execution model, without fitting a black-box function to measurements, and with the purpose of identifying bottlenecks without running the kernel on actual hardware.
- `topic.intent.overview` in this Topic Workspace for scope, Do's, and Don'ts.
