# Literature Scouting Report

## Why Discovery Was Limited

The topic intent and workspace gates already fix the algorithm source, hardware target, precision set, and success criteria. External discovery was therefore scoped to:

- confirming the FlashAttention-4 paper contains usable white-box forward-pass analysis;
- grounding B200 non-MMA hardware parameters with an independent microbenchmark source;
- confirming no existing white-box FA4 predictor removes the need for baseline construction.

## Search Ledger

| Search | Surface | Result |
| --- | --- | --- |
| FlashAttention-4 paper | arXiv 2603.05451v1 | Retained. Provides forward-pass roofline formulas, pipeline design, and B200 throughput numbers. |
| Blackwell microbenchmarks | arXiv 2512.02189v1 | Retained. Confirms SMEM 128 B/clock/SM and MUFU 16 ops/clock/SM. |
| Cross-GPU analytical modeling | arXiv 2605.04178v1 | Retained. Provides methodology reference. |
| Local repo search for existing predictor/cost model | `repos/extern/flash-attention` | No existing white-box runtime predictor found. |

## Retained References

1. **arXiv 2603.05451v1** — *FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling*.
   - Role: primary algorithm/hardware source and seed comparator.
   - Key takeaways:
     - B200 has 148 SMs and 8192 BF16 MMA ops/clock/SM (derived from 2.25 PFLOPS / 1.85 GHz / 148 SMs).
     - Forward pass is bounded by MMA compute (`4MNd / 8192` cycles), shared-memory traffic (`3MNd / 8192` cycles for M,N,d multiples of 128), and exponential unit time (`MN / 16` cycles).
     - Blackwell TMEM (256 KB/SM), 128×128 MMA tiles, fully asynchronous MMA, 2-CTA mode, and TMA are central to the kernel.
     - Partial exponential emulation and conditional softmax rescaling reduce non-MMA time.

2. **arXiv 2512.02189v1** — *Microbenchmarking NVIDIA's Blackwell Architecture*.
   - Role: independent hardware-parameter ground truth.
   - Key takeaways: shared-memory read throughput = 128 bytes/clock/SM; MUFU throughput = 16 ops/clock/SM on B200/GB200.

3. **arXiv 2605.04178v1** — *Microbenchmark-Driven Analytical Performance Modeling Across Modern GPU Architectures*.
   - Role: methodology reference.
   - Key takeaways: instruction-throughput and memory-hierarchy models can be built from microbenchmarks and validated against hardware counters without black-box regression.

4. **Official Flash Attention repository** (`Dao-AILab/flash-attention`, local clone).
   - Role: implementation source and validation harness.
   - Key takeaways: FA4 is implemented in `flash_attn/cute/`; benchmark scripts in `benchmarks/` can generate measured ground truth and NCU traces.

## Rejected / Watchlist References

- **cuDNN 9.13 / Triton attention**: watchlist only. Useful as indirect performance plausibility checks, but not direct white-box comparators.
- **SageAttention/INT4/FP8 quantization papers**: rejected for this topic because they target consumer GPUs and fall outside the B200 single-GPU scope.

## Route Implications

- **Evaluation contract**: the primary metric is runtime-prediction error against host B200 measurements; secondary metrics are NCU counter trend agreement and bottleneck identification.
- **Baseline shortlist**: the FA4 paper roofline model is the anchor comparator to reproduce/extend; a naive max(compute,memory) roofline is a sanity check; measured B200 runtimes are the evaluation target.
- **Next route**: `isomer-deepsci-baseline` is appropriate because the frame is clear, the literature provides a seed model, and no existing predictor removes the research task.
