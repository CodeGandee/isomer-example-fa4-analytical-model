<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/paper/dataset-inventory/v2
schema_ref: isomer:deepsci/record-format/schema/paper/dataset-inventory/v2
payload_digest: sha256:8fe7b018adeb487f1965a1da9e7ca850d3b9b3fd14bd28fbb3aad1ad6b6dc029
-->
# Dataset Inventory — FlashAttention-4 White-Box Runtime Model

Generated from a structured JSON payload.


```json
{
  "body": "# Dataset Inventory — FlashAttention-4 White-Box Runtime Model\n\n| Dataset / file | Type | Generated or reused | Supports which result | Current location | Availability route |\n| --- | --- | --- | --- | --- | --- |\n| Synthetic configuration matrix (batch, heads, seqlen, head_dim, causal, precision) | tabular | generated | Tables 2–4, Figures 1–2 | project workspace | available from authors on request; deposit before submission |\n| Emulator-generated runtimes for calibration split | tabular | generated | calibration factors, Section 4 | project workspace | available from authors on request |\n| Emulator-generated runtimes for validation split (160 configs) | tabular | generated | Tables 2–4, Figures 1–2 | project workspace | available from authors on request |\n| White-box predictor implementation | code | generated | Section 3, all predictions | project workspace | available from authors on request; intended public repository before submission |\n| Figure source data (PNG) | image | generated | Figures 1–3 | paper bundle `figures/` | included in bundle |\n| FlashAttention-4 paper roofline formulas | conceptual | reused | Section 3.2 | Zadouri et al. 2026 | cited arXiv preprint |\n| Blackwell microbenchmark rates | conceptual | reused | Section 3.3 | Jarmusch & Chandrasekaran 2025/2026 | cited arXiv preprints |\n\nNo human, sensitive, or third-party licensed data are used.\n",
  "summary": "Dataset inventory for the FlashAttention-4 B200 runtime-model study, mapping generated files to results and availability routes.",
  "title": "Dataset Inventory — FlashAttention-4 White-Box Runtime Model"
}
```