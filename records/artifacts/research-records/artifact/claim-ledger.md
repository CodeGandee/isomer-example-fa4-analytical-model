<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/paper/claim-ledger/v2
schema_ref: isomer:deepsci/record-format/schema/paper/claim-ledger/v2
payload_digest: sha256:aa33dea1b1b99071803dd32fb00000521b6fe0f45b14c2f57713f3a4a134808d
-->
# Claim Ledger — FlashAttention-4 White-Box Runtime Model

Generated from a structured JSON payload.


```json
{
  "body": "# Claim Ledger — FlashAttention-4 White-Box Runtime Model\n\n| Claim | Status | Evidence | Caveats |\n| --- | --- | --- | --- |\n| Combined model improves MAPE from 22.22% to 4.50% | supported | Table 2, held-out validation | Emulator ground truth, synthetic matrix |\n| Combined model keeps all 160 configs within 30% APE | supported | Table 2 | Same as above |\n| Bottleneck-label accuracy is 100% | supported | Table 2, Section 5.2 | Same as above |\n| TMA/L2 effective-bandwidth correction is dominant improvement | supported | Ablation Table 2 | Calibrated on emulator |\n| Model generalizes to real B200 silicon | unsupported | No silicon data | Explicit limitation in Section 6 |\n| Model generalizes beyond studied matrix (custom tile sizes, num_splits, fused variants) | unsupported | Matrix omits these | Explicit limitation in Section 6 |\n| White-box predictor is useful for kernel design | partially supported | Interpretable bottleneck labels | Utility not tested on real design loop |\n",
  "summary": "Claim ledger for the FlashAttention-4 B200 runtime model, listing supported claims, evidence anchors, and caveats.",
  "title": "Claim Ledger — FlashAttention-4 White-Box Runtime Model"
}
```