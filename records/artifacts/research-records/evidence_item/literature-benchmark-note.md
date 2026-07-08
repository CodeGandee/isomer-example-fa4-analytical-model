<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/review/literature-benchmark-note/v1
schema_ref: isomer:deepsci/record-format/schema/review/literature-benchmark-note/v1
payload_digest: sha256:0f59b8a6931ec6abb9646d361fe9f26d28a11ff9b089e2626060e850f6006ca0
-->
# Literature Benchmark Note — FlashAttention-4 White-Box Runtime Model

Generated from a structured JSON payload.


```json
{
  "body": "# Literature Benchmark Note \u2014 FlashAttention-4 White-Box Runtime Model\n\n## Target venue\nUnspecified at submission-pass entry; no exact journal policy was checked.\n\n## Strong nearby comparators\n- **Zadouri et al., 2026** \u2014 FlashAttention-4 roofline model, algorithm quantities, and Blackwell kernel design. This paper takes the roofline as its baseline.\n- **Jarmusch \u0026 Chandrasekaran, 2025/2026** \u2014 Blackwell microbenchmarks providing HBM/L2/TMA and Tensor Core rate assumptions.\n- **Williams et al., 2009; Yang et al., 2019** \u2014 Roofline and hierarchical roofline framing for GPUs.\n\n## Positioning vs. comparators\nThe draft does not claim a new attention algorithm; it claims a more accurate white-box predictor of an existing algorithm\u0027s runtime on a specific architecture. That residual positioning is narrow but defensible.\n\n## Citation coverage\n- Core FA family (Dao et al. 2022; Dao 2023; Shah et al. 2024; Zadouri et al. 2026) is cited.\n- GPU modeling and Blackwell microbenchmarks are cited.\n- No additional comparator papers surfaced during this audit.\n\n## Risk\nThe paper\u0027s novelty claim rests on accuracy improvement and interpretability, not on a new kernel. A venue expecting algorithmic novelty may ask for stronger positioning; a venue expecting modeling work should find the framing acceptable.\n",
  "title": "Literature Benchmark Note \u2014 FlashAttention-4 White-Box Runtime Model"
}
```