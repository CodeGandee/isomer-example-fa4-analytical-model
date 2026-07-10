<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/paper/final-limitations-report/v2
schema_ref: isomer:deepsci/record-format/schema/paper/final-limitations-report/v2
payload_digest: sha256:62f2af8bd75f108a00a2bbed0cae2178e9a5b58999085b699c95b29c2c4a6e5a
-->
# Final Limitations Report

Generated from a structured JSON payload.


```json
{
  "body": "# Final Limitations Report\n\n## Data limits\n- The validation matrix is synthetic and covers only batch, heads, sequence length, head dimension, causal mask, and bf16/fp16/fp8.\n- fp4 is unsupported by the installed FA4 build.\n- Sequence length 32768 was dropped to fit the wall-clock budget.\n\n## Metric limits\n- Worst-case APEs occur for small absolute runtimes; the largest validation APE is 74.9%.\n- Relative-error fairness can be questioned when launch latency dominates runtime.\n\n## Implementation limits\n- Calibrated factors are specific to the measured B200, driver stack (CUDA 13.0), and FA4 build.\n- The NCU bottleneck slack gamma=3.0 has not been validated on a memory-bound profile.\n\n## Literature limits\n- References should be verified before external submission.\n- No PDF/LaTeX toolchain; bundle is Markdown only.\n\n## Reproducibility limits\n- No public repository or persistent identifiers exist yet.\n- Code and data are currently available on request only.\n\n## Unsupported claims\n- Generalisation outside the studied matrix.\n- fp4 support.\n- Memory-bound bottleneck-label accuracy.\n",
  "summary": "Final limitations report for the FlashAttention-4 B200 runtime-model study, covering data scope, metric limits, hardware coverage, and claim boundaries.",
  "title": "Final Limitations Report"
}
```