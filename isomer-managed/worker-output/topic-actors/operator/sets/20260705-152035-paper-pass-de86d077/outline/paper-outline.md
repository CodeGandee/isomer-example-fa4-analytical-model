# Paper Outline: White-Box FlashAttention-4 Runtime Prediction on NVIDIA B200

## One-sentence idea
A white-box analytical predictor for FlashAttention-4 forward runtime, calibrated only on real B200 silicon, achieves ≤13% validation MAPE and 100% NCU bottleneck accuracy after adding a fixed launch-overhead term and an NCU-guided bottleneck slack.

## Claim-evidence boundary

- **Measured facts (real B200):** 540 measured configs (bf16/fp16/fp8); 60 NCU-profiled; fp4 unsupported. First real-hardware pass refuted the emulator-tuned combined model (62.14% MAPE vs 42.10% baseline). Second pass with launch-overhead fix: validation 12.62% MAPE, query 10.01% MAPE, 93.3%/96.4% within 30%. Bottleneck-refinement pass added NCU slack 3.0 and raised NCU accuracy to 100% on validation and query while preserving MAPE.
- **Interpretation:** Launch/grid overhead is the dominant error source when moving from emulator to real hardware. The NCU-guided slack repairs the white-box→NCU bottleneck mapping without changing predicted runtimes.
- **Limitations:** All NCU labels in this dataset are compute-bound; memory-bound NCU validation is pending. Matrix excludes fp4 and custom tile sizes/num_splits. Calibration is specific to the measured B200 and driver stack.

## Paper view

### Sections

1. **Abstract** — Problem, method, real-hardware result, and limitation.
2. **Introduction** — Motivate white-box runtime prediction for FA4 on B200; state the shift from emulator-grounded preliminary result to real-silicon validation; enumerate three corrections (launch overhead, occupancy/bandwidth/precision efficiency, NCU bottleneck slack); summarize key numbers.
3. **Related Work** — FlashAttention family, GPU analytical models, Blackwell/B200 prior work, gap statement.
4. **Method** —
   - 4.1 Workload and baseline roofline.
   - 4.2 Bounded corrections: occupancy, effective HBM/L2/TMA bandwidth, precision-specific MMA/MUFU throughput.
   - 4.3 Launch-overhead term and calibration grid.
   - 4.4 NCU profiling methodology and bottleneck-label calibration.
5. **Experiments** —
   - 5.1 Config matrix and splits.
   - 5.2 Real B200 measurement protocol (flash_attn_func, median of 10, warmup 3).
   - 5.3 NCU subset selection and SpeedOfLight labeling.
   - 5.4 Metrics: MAPE, Max APE, within-30%, NCU bottleneck accuracy.
6. **Results** —
   - 6.1 Emulator vs real hardware: why the first pass failed.
   - 6.2 Improved model after launch-overhead fix.
   - 6.3 Bottleneck-refinement results (100% NCU accuracy).
   - 6.4 Per-precision breakdown.
   - 6.5 Worst-case and residual analysis.
7. **Limitations** — fp4 unsupported, all NCU labels compute-bound, synthetic matrix, driver/kernel-specific calibration.
8. **Conclusion** — Contributions and next steps.

### Required displays

- Table 1: White-box algorithm quantities.
- Table 2: Real-hardware results across passes (emulator preliminary, first real pass refuted, improved pass, refined pass).
- Table 3: Final per-precision accuracy on validation/query.
- Figure 1: Predicted vs measured runtime (real B200 refined model) with 30% bands.
- Figure 2: Residual distribution by predicted bottleneck.
- Figure 3: Predictor pipeline diagram.

## Evidence view

- **Source artifacts:** `artifact-ANALYSIS_CAMPAIGN_SUMMARY-320d852cdf6e` (bottleneck-accuracy audit), `artifact-ANALYSIS_CAMPAIGN_SUMMARY-e8fa897761c1` (threshold refinement), previous paper bundle `20260704-152057-submission-42712472`, code in `repos/topic-main/src/fa4_b200_predictor/`.
- **Run directories:**
  - First real pass: `sets/20260704-184139-hypothesis-pass-0aa46842/run/real-hardware-benchmark/`.
  - Improved pass: `sets/20260704-183342-dataset-design-a1b2c3d4/real-hardware-improved-run/`.
  - Bottleneck refinement: `sets/20260705-144211-hypothesis-pass-bottleneck-refine/real-hardware-bottleneck-refine-run/`.
- **Figures generated from:** `refined_validation_predictions.csv`, `refined_query_predictions.csv`.

## Outline validation

- Evidence check: every numerical claim maps to a metrics.json row or analysis summary.
- Route check: ready for `isomer-deepsci-write`.
- Placeholder check: outputs will use `<PAPER_VIEW>`, `<SECTION_WRITING_PLAN>`, `<OUTLINE_VALIDATION_REPORT>`.
- Paper-hygiene check: no operator/agent wording in planned manuscript.

## Section writing plan

| Section | Source inputs | Claim limits | Figures/tables | Priority |
|---|---|---|---|---|
| Abstract | analysis summaries, final metrics | no fp4 claims; note compute-bound NCU caveat | none | 1 |
| Introduction | previous draft, real-hardware narrative | distinguish emulator from silicon | none | 1 |
| Related Work | previous draft references | keep citations from verified refs | none | 2 |
| Method | code, previous draft | bounded factors only; report final params | Table 1, Fig. 3 | 1 |
| Experiments | code, metrics files | real protocol only; fp4 skipped | none | 1 |
| Results | metrics files, CSVs | all real B200; include refuted pass as ablation | Tables 2-3, Figs. 1-2 | 1 |
| Limitations | analysis summaries, code | explicit caveats | none | 1 |
| Conclusion | all above | no unsupported generalisation | none | 1 |
