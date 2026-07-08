# Review Audit Plan — FlashAttention-4 White-Box Runtime Model

## Scope
Final pre-submission audit of the revised paper bundle (revised draft, references, figures) for `flash-attention-4-whitebox-runtime-model`.

## Claim set
1. The reproduced FlashAttention-4 roofline baseline achieves 22.22% MAPE / 42.07% max APE on the 160-config held-out validation set.
2. Adding three bounded corrections (occupancy, effective HBM/L2/TMA bandwidth, precision-specific throughput) reduces MAPE to 4.50% and max APE to 14.36%.
3. The combined model labels the dominant bottleneck correctly on 100% of validation configurations.
4. Ground-truth runtimes come from a high-fidelity emulator, not real B200 silicon.

## Strongest evidence
- Held-out ablation table (Table 2) with five predictor variants and four metrics.
- Per-precision (Table 3) and per-bottleneck (Table 4) residual breakdowns.
- Calibration/validation split protocol and bounded grid search.

## Weakest evidence / risks
- No real silicon measurements; generalization to B200 production kernels is unverified.
- Synthetic matrix omits custom tile sizes, `num_splits`, fused variants, and real workloads.
- Venue is unspecified; Nature-family data-statement requirements are not confirmed.

## Likely rejection routes
- Reviewer questions emulator-to-silicon transfer validity.
- Reviewer requests open-source predictor code or raw configuration matrix.
- Venue mismatch if submitted as systems paper without public artifacts.

## Comparator check
- FlashAttention-4 paper [Zadouri et al., 2026]: baseline roofline source.
- Jarmusch & Chandrasekaran Blackwell microbenchmarks: hardware rates source.
- No direct white-box B200 predictor in the cited literature.

## Language hygiene risks
- Low: citations match references.bib, figures are referenced, section labels are sequential.

## Route forecast
`finalize` — the bundle is internally consistent, metrics meet stated success criteria, and residual risks are already disclosed as limitations.
