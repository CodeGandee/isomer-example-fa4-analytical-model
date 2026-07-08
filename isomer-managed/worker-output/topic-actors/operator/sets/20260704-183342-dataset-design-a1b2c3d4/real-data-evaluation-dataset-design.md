# Real-Data Evaluation Dataset Design

## Goal

Produce a concrete, measured dataset of FlashAttention-4 forward-pass runtimes on NVIDIA B200 hardware. The dataset must let us evaluate the white-box predictor's accuracy against **real kernel timings**, not emulator ground truth.

## Why the previous run failed

The previous empirical-pass subagent did not attempt real B200 kernel runs. The root cause was environment, not time:

- `torch` was not installed in the topic workspace Pixi environment.
- `flash-attn` / `flash-attn-4` was not installed.
- The subagent therefore fell back to a white-box emulator and reported that real launches were "infeasible within the ~25-minute budget."

The host has **8 NVIDIA B200 GPUs** (compute capability 10.0, CUDA 13.1, 180 GiB HBM each). A single FA4 forward pass on one config takes milliseconds; the entire matrix below can be measured in minutes, not hours.

## Measurement protocol

1. **Environment**: topic workspace Pixi env with PyTorch 2.7+ and `flash-attn-4` (CuTeDSL build for Blackwell).
2. **Device**: single B200 GPU (`cuda:0`), cleared cache between configs.
3. **Warm-up**: 3 untimed warmup runs for each config.
4. **Timing**: `torch.cuda.Event(enable_timing=True)`; 10 timed runs; report median.
5. **Precision formats**: BF16, FP16, FP8, FP4 (as supported by the installed `flash-attn-4` build).
6. **Input layout**: `(batch, seqlen, nheads, head_dim)` for `flash_attn_func`.
7. **Metric recorded per config**:
   - `measured_runtime_ms` (median of 10)
   - `measured_runtime_std_ms`
   - `predicted_runtime_ms` (from existing white-box predictor)
   - `predicted_bottleneck`
   - absolute percentage error

## Config matrix

The matrix is chosen to cover realistic training and inference shapes while staying within B200 HBM. All configs use Q, K, V of equal length (standard self-attention).

| Parameter | Values | Notes |
| --- | --- | --- |
| `batch` | 1, 2, 4, 8 | Inference / small-batch training |
| `heads` | 16, 32, 64 | Common MHA head counts |
| `seqlen` | 1024, 2048, 4096, 8192, 16384, 32768 | Core range; 65536 omitted for HBM safety |
| `head_dim` | 64, 128 | GPT/LLaMA family standards |
| `causal` | True, False | Both attention modes |
| `precision` | bf16, fp16, fp8, fp4 | FA4-supported formats |

Full Cartesian product: `4 × 3 × 6 × 2 × 2 × 4 = 1,152` configs.

### HBM budget check (worst case)

For `batch=8, heads=64, seqlen=32768, head_dim=128, bf16`:
- Q, K, V, O: `4 × 8 × 32768 × 64 × 128 × 2 bytes` ≈ 13.7 GiB
- Attention matrix (causal): `8 × 64 × 32768 × 32768 × 2 bytes / 2` ≈ 549 GiB if materialized, but FA4 is memory-efficient and does not materialize it.

FA4's memory-efficient algorithm keeps activation memory close to Q/K/V/O, so the above config fits in 180 GiB HBM. Very long sequences with large batch/head counts may OOM; those configs will be skipped and recorded as `oom`.

## Calibration / validation split

- **Calibration set**: 20% of configs, drawn stratified across seqlen and precision.
- **Held-out validation set**: 20% of configs, disjoint from calibration.
- **Query set**: remaining 60%, used for final accuracy reporting.

The predictor may use calibration-set measurements to fit bounded efficiency factors. It must **not** use validation or query measurements when predicting.

## Evaluation criteria

Same as the useful-improvement threshold already in the topic:

- Held-out MAPE of `predicted_runtime_ms` ≤ 25%
- ≥ 75% of validation configs within 30% absolute error
- ≥ 75% bottleneck-label accuracy
- Δ MAPE vs baseline ≥ 5 percentage points improvement

## Expected wall-clock time

With 10 timed runs per config and ~1,152 configs:
- ~11,520 kernel launches.
- At ~1 ms per launch median, raw kernel time ≈ 12 s.
- With warm-up, Python overhead, and OOM handling: **5–15 minutes** on one B200.

This is well inside the previous 25-minute budget; the original blocker was missing packages, not runtime.

## Blockers and mitigations

| Risk | Mitigation |
| --- | --- |
| `flash-attn-4` install fails on CUDA 13.1 | Use pre-release wheels (`--prerelease=allow`) or build from the local `repos/extern/flash-attention` clone with `MAX_JOBS=4`. |
| FP8/FP4 not supported by build | Fall back to BF16/FP16 only and document the reduced precision coverage. |
| OOM on large configs | Skip config, record `oom`, and report effective coverage. |
| Kernel launch overhead for tiny configs | Filter or separately report configs where predicted runtime < 0.1 ms. |

## Next step

Run a `hypothesis-pass` with the hypothesis: *"The existing white-box predictor (`fa4-b200-whitebox-occupancy-tma-l2-precision-v1`) achieves the useful-improvement threshold when validated against real B200 FlashAttention-4 measurements."*
