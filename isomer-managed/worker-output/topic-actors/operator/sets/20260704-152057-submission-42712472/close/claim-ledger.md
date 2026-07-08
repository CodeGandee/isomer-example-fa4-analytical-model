# Claim Ledger — FlashAttention-4 White-Box Runtime Model

| Claim | Status | Evidence | Caveats |
| --- | --- | --- | --- |
| Combined model improves MAPE from 22.22% to 4.50% | supported | Table 2, held-out validation | Emulator ground truth, synthetic matrix |
| Combined model keeps all 160 configs within 30% APE | supported | Table 2 | Same as above |
| Bottleneck-label accuracy is 100% | supported | Table 2, Section 5.2 | Same as above |
| TMA/L2 effective-bandwidth correction is dominant improvement | supported | Ablation Table 2 | Calibrated on emulator |
| Model generalizes to real B200 silicon | unsupported | No silicon data | Explicit limitation in Section 6 |
| Model generalizes beyond studied matrix (custom tile sizes, num_splits, fused variants) | unsupported | Matrix omits these | Explicit limitation in Section 6 |
| White-box predictor is useful for kernel design | partially supported | Interpretable bottleneck labels | Utility not tested on real design loop |
