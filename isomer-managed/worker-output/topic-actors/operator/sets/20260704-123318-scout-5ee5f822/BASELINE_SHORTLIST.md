# Baseline Shortlist

## Anchor Comparator

### 1. FlashAttention-4 Paper Roofline Model

- **Provenance**: arXiv 2603.05451v1, *FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling*.
- **Metric and split fit**: Directly targets the forward-pass runtime of Flash Attention 4 on Blackwell. Provides closed-form cycle counts for MMA, shared-memory traffic, and exponential operations as functions of tile dimensions and head dimension.
- **Implementation availability**: Not published as a standalone predictor; must be reproduced from the paper into a Python/SymPy predictor in `repos/topic-main`.
- **Expected cost**: Low to medium. The formulas are in the paper, but extending them to full input shapes, precisions, and latency-hiding/occupancy effects requires engineering effort.
- **Downstream value**: Serves as the first credible white-box model and the foundation for refinement experiments.
- **Main risk**: The paper's roofline ignores L2/HBM effects, TMA launch latency, occupancy jitter, and precision-specific scheduling. The model will need calibration to match real runtimes.
- **Route**: **Reproduce / extend**. Baseline construction should implement the paper's forward-pass formulas, parameterize them by input shape and precision, and add the missing memory/occupancy terms.

## Sanity Checks and Ground Truth

### 2. Naive Max(Compute, Memory) Roofline

- **Provenance**: Standard GPU roofline model.
- **Metric and split fit**: Provides a lower-bound baseline that the white-box model should beat.
- **Implementation availability**: Trivial to implement in Python.
- **Expected cost**: Very low.
- **Downstream value**: Shows how much the full model improves over a crude bound.
- **Main risk**: Too weak to be a final comparator; only useful as a sanity check.
- **Route**: **Attach** as a secondary comparator.

### 3. Measured B200 Kernel Runtime

- **Provenance**: Host B200 + official Flash Attention repository benchmark scripts.
- **Metric and split fit**: This is the target variable, not a predictor.
- **Implementation availability**: Benchmark scripts exist in `repos/extern/flash-attention/benchmarks/`; the kernel must build for B200.
- **Expected cost**: Medium (build time, NCU collection).
- **Downstream value**: Required for calibration and validation.
- **Main risk**: Direct measurement leakage if used to answer a prediction query.
- **Route**: **Import** as evaluation ground truth only.

## Rejected Candidates

### 4. cuDNN 9.13 Attention / Triton Attention

- **Reason**: Closed-source or different kernel implementations. The FA4 paper reports speedups over them, so they are useful only as indirect plausibility checks, not as white-box comparators for this modeling task.
- **Route**: **Reject**.

### 5. SageAttention Family

- **Reason**: Targets consumer GPUs and INT4/FP8/FP4 quantization schemes outside the B200 datacenter scope defined by the topic intent.
- **Route**: **Reject**.

## Recommended Next Action

Route to `isomer-deepsci-baseline` and begin by reproducing the FlashAttention-4 paper's forward-pass roofline model in `repos/topic-main`, then extend it with B200-specific memory/occupancy terms and validate against the measured B200 runtime ground truth.
