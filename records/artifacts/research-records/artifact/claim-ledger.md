<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/paper/claim-ledger/v1
schema_ref: isomer:deepsci/record-format/schema/paper/claim-ledger/v1
payload_digest: sha256:5bf1bda49160a8a4a504da9972b77bb9e1a3a7dd5a76297219931152f9e4704b
-->
# Claim Ledger — FlashAttention-4 White-Box Runtime Model

Generated from a structured JSON payload.


```json
{
  "body": "# Claim Ledger \u2014 FlashAttention-4 White-Box Runtime Model\n\n| Claim | Status | Evidence | Caveats |\n| --- | --- | --- | --- |\n| Combined model improves MAPE from 22.22% to 4.50% | supported | Table 2, held-out validation | Emulator ground truth, synthetic matrix |\n| Combined model keeps all 160 configs within 30% APE | supported | Table 2 | Same as above |\n| Bottleneck-label accuracy is 100% | supported | Table 2, Section 5.2 | Same as above |\n| TMA/L2 effective-bandwidth correction is dominant improvement | supported | Ablation Table 2 | Calibrated on emulator |\n| Model generalizes to real B200 silicon | unsupported | No silicon data | Explicit limitation in Section 6 |\n| Model generalizes beyond studied matrix (custom tile sizes, num_splits, fused variants) | unsupported | Matrix omits these | Explicit limitation in Section 6 |\n| White-box predictor is useful for kernel design | partially supported | Interpretable bottleneck labels | Utility not tested on real design loop |\n",
  "title": "Claim Ledger \u2014 FlashAttention-4 White-Box Runtime Model"
}
```