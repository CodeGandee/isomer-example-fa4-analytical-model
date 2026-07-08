# Final Limitations Report — FlashAttention-4 White-Box Runtime Model

## Data limitations
- Ground-truth runtimes are emulator-generated, not real B200 silicon measurements.
- Synthetic matrix covers only batch, heads, sequence length, head dimension, causal mask, and precision.

## Metric limitations
- MAPE floor includes 3% residual noise injected by the emulator.
- Max APE is sensitive to very small runtimes.

## Implementation limitations
- Tile sizes and occupancy assumptions are derived from the FlashAttention-4 paper and microbenchmarks, not measured on a target binary.
- The predictor code and configuration matrix are not yet in a public repository.

## Resource limitations
- Full silicon matrix was outside the experiment time budget.

## Literature limitations
- Positioning against the FlashAttention-4 roofline is clear; broader GPU kernel modeling comparators are not deeply benchmarked.

## Reproducibility
- Reproduction requires the emulator or eventual silicon measurements, the synthetic matrix, and the predictor code. All are author-controlled at this stage.

## Unsupported claims
- Real silicon accuracy is not claimed; Section 6 explicitly marks it as future work.
- Generalization to custom launch parameters and production workloads is unverified.
