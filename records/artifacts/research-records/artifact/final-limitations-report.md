<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/paper/final-limitations-report/v1
schema_ref: isomer:deepsci/record-format/schema/paper/final-limitations-report/v1
payload_digest: sha256:07e039039b49d4672d4cdfa6bfc6843bef6c466c1e4ef0fdf3d94547fdeee274
-->
# Final Limitations Report — FlashAttention-4 White-Box Runtime Model

Generated from a structured JSON payload.


```json
{
  "body": "# Final Limitations Report \u2014 FlashAttention-4 White-Box Runtime Model\n\n## Data limitations\n- Ground-truth runtimes are emulator-generated, not real B200 silicon measurements.\n- Synthetic matrix covers only batch, heads, sequence length, head dimension, causal mask, and precision.\n\n## Metric limitations\n- MAPE floor includes 3% residual noise injected by the emulator.\n- Max APE is sensitive to very small runtimes.\n\n## Implementation limitations\n- Tile sizes and occupancy assumptions are derived from the FlashAttention-4 paper and microbenchmarks, not measured on a target binary.\n- The predictor code and configuration matrix are not yet in a public repository.\n\n## Resource limitations\n- Full silicon matrix was outside the experiment time budget.\n\n## Literature limitations\n- Positioning against the FlashAttention-4 roofline is clear; broader GPU kernel modeling comparators are not deeply benchmarked.\n\n## Reproducibility\n- Reproduction requires the emulator or eventual silicon measurements, the synthetic matrix, and the predictor code. All are author-controlled at this stage.\n\n## Unsupported claims\n- Real silicon accuracy is not claimed; Section 6 explicitly marks it as future work.\n- Generalization to custom launch parameters and production workloads is unverified.\n",
  "title": "Final Limitations Report \u2014 FlashAttention-4 White-Box Runtime Model"
}
```