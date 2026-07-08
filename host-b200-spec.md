# Host B200 Baseline Specification

Baseline GPU configuration captured from the host on which the model will be validated.

## Capture command

```bash
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap,clocks.current.graphics,clocks.current.sm,clocks.current.memory --format=csv,noheader
```

## Baseline values

| Attribute | Value |
| --- | --- |
| GPU name | NVIDIA B200 |
| Driver version | 590.48.01 |
| CUDA version (runtime) | 13.1 |
| Compute capability | 10.0 |
| Total HBM | 183,359 MiB (~179 GiB per GPU) |
| Current Graphics clock | 120 MHz |
| Current SM clock | 120 MHz |
| Current Memory clock | 3,996 MHz |
| Maximum Graphics/SM clock | 1,965 MHz |
| Maximum Memory clock | 3,996 MHz |

## Notes

- The host has 8 × NVIDIA B200 GPUs.
- `ncu` 2025.4.1.0 is available at `<NCU_PATH>`.
- The current SM clock is reported at the idle/minimum p-state; peak modeling should use the maximum SM clock (1,965 MHz) unless a fixed sustained clock is agreed.
- Memory bandwidth must be derived from memory clock and bus width; record the agreed sustained HBM bandwidth separately once measured or sourced.
- These values are inputs to the white-box model, not outputs of it.
