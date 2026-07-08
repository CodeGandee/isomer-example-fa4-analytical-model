# Final Limitations Report

## Data limits
- The validation matrix is synthetic and covers only batch, heads, sequence length, head dimension, causal mask, and bf16/fp16/fp8.
- fp4 is unsupported by the installed FA4 build.
- Sequence length 32768 was dropped to fit the wall-clock budget.

## Metric limits
- Worst-case APEs occur for small absolute runtimes; the largest validation APE is 74.9%.
- Relative-error fairness can be questioned when launch latency dominates runtime.

## Implementation limits
- Calibrated factors are specific to the measured B200, driver stack (CUDA 13.0), and FA4 build.
- The NCU bottleneck slack gamma=3.0 has not been validated on a memory-bound profile.

## Literature limits
- References should be verified before external submission.
- No PDF/LaTeX toolchain; bundle is Markdown only.

## Reproducibility limits
- No public repository or persistent identifiers exist yet.
- Code and data are currently available on request only.

## Unsupported claims
- Generalisation outside the studied matrix.
- fp4 support.
- Memory-bound bottleneck-label accuracy.
