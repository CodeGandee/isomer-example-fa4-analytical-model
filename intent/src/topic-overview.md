# Research Topic: Flash Attention 4 White-Box Runtime and Bottleneck Model

How can we build a white-box, hardware-grounded model that, given a Flash Attention 4 **forward-pass** input configuration, predicts (1) kernel runtime in milliseconds, (2) the hardware component that will saturate, and (3) the execution path that will block progress, for the NVIDIA B200 GPU across BF16/FP16/FP8/FP4 precisions and single-GPU configurations, without executing the kernel?

## Motivation

- Flash Attention 4 kernel configuration choices are increasingly tied to GPU micro-architecture, and measuring every configuration is expensive.
- A white-box runtime model lets us identify, from the input shape, precision, and hardware parameters alone, **which hardware component saturates and which execution path blocks progress**, not just whether the kernel is "compute" or "memory" bound.
- The model should be explainable: every predicted latency term must trace back to a concrete B200 hardware limit or instruction throughput bound.
- Measurements, especially Nsight Compute (NCU) SM/cache-level profiles, should be reserved for calibration and validation, not for producing the prediction itself.
- The host has NVIDIA B200 GPUs available, so NCU validation can run locally.

## Topic Breakdown

Build a predictive runtime model from first GPU execution principles down to the B200 SM and cache level for the Flash Attention 4 forward pass on a single GPU. Decompose the B200 into subsystems (GPC/SM, Tensor Memory / TMEM, Tensor Memory Accelerator / TMA, 5th-generation Tensor Cores, L2 cache, HBM3e, NV-HBI, decompression engine) and decompose the forward pass into execution stages (TMA load, MMA, softmax, TMEM traffic, synchronization, storeback). For each stage and each precision (BF16, FP16, FP8, FP4), derive closed-form runtime contributions and key NCU counter trends as functions of input shape and hardware parameters. Treat inherently stochastic behaviors (cache hit/miss, shared-memory bank conflicts, occupancy jitter, TMA latency variance) with probabilistic sub-models. Aggregate stage contributions into `predicted_runtime_ms`, the `predicted_saturated_component`, and the `predicted_blocking_path`.

### Do's

- Start from the Flash Attention 4 forward-pass algorithm and tile/warp scheduling scheme, using the official Flash Attention repository as the algorithm source.
- Document the B200 system architecture and execution flow as it relates to Flash Attention 4 forward pass.
- Model at the level of warps, SMs, TMEM, TMA, Tensor Cores, L2/HBM transactions, and instruction issue.
- Decompose the forward pass into pipeline stages and derive closed-form formulas for each stage's runtime contribution, the hardware component that saturates in that stage, and the blocking execution path.
- Predict the saturated hardware component (e.g., Tensor Cores, SFU, FP/INT pipes, TMA, TMEM, L2, HBM) and the blocking execution path for each input configuration.
- Support BF16, FP16, FP8, and FP4 precisions.
- Target single-GPU execution.
- Use probabilistic cache / memory models for stochastic behaviors: cache hit/miss, shared-memory bank conflicts, occupancy jitter, and TMA latency variance.
- Account for HBM bandwidth, L2/cache effects, shared-memory capacity/bandwidth, and Tensor Core throughput.
- Include occupancy limits (registers per thread, shared memory per SM, TMEM per SM, warps per SM).
- Derive the baseline B200 clock, memory, and driver/CUDA configuration from this host.
- Produce both a documented derivation and a runnable Python predictor.
- Scope the model to the Flash Attention 4 forward pass; document which backward-pass effects are excluded.
- Express the final output as `predicted_runtime_ms`, `predicted_saturated_component`, and `predicted_blocking_path` for the NVIDIA B200 GPU, while keeping the model parameterizable so it can be retargeted.
- Record assumptions, simplifications, and open questions explicitly.
- Validate predictions against independent microbenchmarks, hardware specs, or published kernel profiles when possible.
- Use Nsight Compute (`ncu`) on the host B200 to validate SM-level and cache-level predictions, including per-unit active-cycle counters (Tensor Core, TMA, SFU, FP/INT) for component-level bottleneck validation.

### Don'ts

- Do not treat the GPU as a black box or fit a generic curve to measurements.
- Do not require actual Flash Attention 4 kernel execution to generate a prediction; NCU validation runs on the host B200 are allowed as explicit calibration/validation points.
- Do not model the Flash Attention 4 backward pass in this version.
- Do not target multi-GPU or tensor-parallel configurations in this version.
- Do not ignore memory hierarchy, TMEM/TMA, or occupancy constraints.
- Do not invent exact hardware parameters without citing the B200 spec or measurement.
- Do not produce timeline or budget sections.

## Expected Outcome

- A documented white-box runtime model for Flash Attention 4 forward pass on the NVIDIA B200 GPU.
- A B200 system-architecture and execution-flow section that explains which subsystems the model covers.
- Closed-form formulas for each modeled subsystem/stage of the forward pass, parameterized by input shape and precision.
- Predicted NCU counter trends for key forward-pass stages (e.g., L2 transactions, shared-memory accesses, Tensor Core utilization) and a comparison against measured NCU profiles.
- A runnable Python predictor that takes input configuration and precision and returns `predicted_runtime_ms`, `predicted_saturated_component`, and `predicted_blocking_path`.
- A component-level bottleneck validation that compares predicted saturating components against per-unit NCU active-cycle counters (e.g., Tensor Core, TMA, SFU, FP/INT) and reports component-level bottleneck accuracy.
- A path-level validation that compares the predicted blocking execution path against the SASS-level instruction critical path observed in NCU or disassembly.
- A list of assumptions and model limitations.
- A validation plan that specifies how to check predictions once measurements become available, including measured-vs-predicted runtime, measured-vs-predicted NCU counter trend, **measured-vs-predicted saturated component**, and **measured-vs-predicted blocking path** comparisons on the host B200 where feasible.

## Related Links

- Flash Attention GitHub repository: https://github.com/Dao-AILab/flash-attention
- FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling: https://arxiv.org/html/2603.05451v1
- Microbenchmark-Driven Analytical Performance Modeling Across Modern GPU Architectures: https://arxiv.org/html/2605.04178v1
- Microbenchmarking NVIDIA's Blackwell Architecture: https://arxiv.org/html/2512.02189v1
- Cache Modeling in Probabilistic Execution Time Analysis: https://www.comp.nus.edu.sg/~tulika/dac08-probability.pdf
- NVIDIA CUDA C++ Programming Guide: https://docs.nvidia.com/cuda/cuda-c-programming-guide/
- NVIDIA CUTLASS repository: https://github.com/NVIDIA/cutlass
- NVIDIA Nsight Compute documentation: https://docs.nvidia.com/nsight-compute/
