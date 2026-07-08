# Analysis Campaign Summary: FA4 B200 White-Box Runtime Model (Revision-Pass Update)

## Status

Supported with revision.

## Route decision

`write` — route to `isomer-deepsci-write` to update the draft, render figures, and resolve citations. No new experiment is required.

## Claim update

The combined white-box predictor is supported. The calibration claim is narrowed: the combined model searches four factors (hbm_factor, mma_efficiency, mufu_efficiency, launch_overhead_us) while l2_factor, tma_factor, and smem_factor are fixed at defaults (0.70, 0.65, 0.90). The TMA/L2 ablation separately calibrates l2_factor=0.45 and tma_factor=0.70.

## Corrected calibration factors

Combined model searched factors (from `calibration_params.json`):

```json
{
  "hbm_factor": 0.85,
  "mma_efficiency": 0.85,
  "mufu_efficiency": 0.85,
  "launch_overhead_us": 0.5
}
```

Fixed defaults in the combined model:

```json
{
  "l2_factor": 0.7,
  "tma_factor": 0.65,
  "smem_factor": 0.9
}
```

TMA/L2 ablation calibrated factors:

```json
{
  "hbm_factor": 0.85,
  "l2_factor": 0.45,
  "tma_factor": 0.7
}
```

## Figure generation plan

- **Figure 1**: Predicted vs measured runtime scatter for the combined model on the 160-config validation set, with identity line and 30% error bands. Source: combined_predictions.csv.
- **Figure 2**: Residual distribution by predicted bottleneck (TMA, HBM, MMA, MUFU) for the combined model. Source: combined_predictions.csv.
- **Figure 3**: Predictor pipeline diagram: input configuration -> algorithm quantities -> baseline roofline -> occupancy / effective bandwidth / precision corrections -> calibration -> predicted runtime and bottleneck label. Source: predictor.py and calibrate.py logic.

## Citation resolution plan

- FlashAttention-4 paper (Zadouri et al., arXiv:2603.05451v1)
- FlashAttention-3 paper (Shah et al., NeurIPS 2024 / arXiv:2407.08608)
- FlashAttention-2 paper (Dao, arXiv:2307.08691)
- FlashAttention-1 paper (Dao et al., NeurIPS 2022 / arXiv:2205.14135)
- Blackwell microbenchmarks (Jarmusch & Chandrasekaran, arXiv:2512.02189v3)
- Roofline model (Williams, Waterman & Patterson, CACM 2009)
- Hierarchical Roofline for GPUs (Yang, Kurth & Williams, Concurrency and Computation 2019)
- Microbenchmark-driven analytical GPU modeling (Jarmusch & Chandrasekaran, arXiv:2605.04178v1)

Output: A references.bib file with complete BibTeX entries and inline LaTeX/Markdown citations in Related Work.

## Next actions

1. Update the draft with the corrected calibration description in Sections 3.3, 3.4, and 5.6.
2. Render Figures 1-3 from combined_predictions.csv and embed them in the revised draft.
3. Resolve Related Work citation placeholders and attach a complete references.bib.
4. Run manuscript validation and route to finalize if all checks pass.
