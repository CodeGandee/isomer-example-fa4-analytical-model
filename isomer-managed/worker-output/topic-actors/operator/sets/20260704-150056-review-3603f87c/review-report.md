# Review Report: A White-Box Analytical Model for FlashAttention-4 Runtime on NVIDIA B200

## Review mode

- review_followup_policy: single-round text correction, then re-review or finalize
- manuscript_edit_mode: targeted revision; no new experiments required
- source_compile_preference: Tectonic first; LaTeX engine fallback only when required or blocked
- manuscript_source_status: draft-section-set ready for revision; source is Markdown

## Summary

- paper / draft: `artifact-DRAFT_SECTION_SET-db586e5e0d48` — full manuscript draft sections for the FA4 B200 white-box runtime predictor
- overall judgment: **revise**. The draft is scientifically sound at the evidence level, but it misstates what was calibrated in the combined predictor. That error must be corrected before the paper can finalize.
- top 3 highest-risk issues:
  1. The Method and Results sections claim the combined model calibrates six bounded factors (`f_HBM`, `f_L2`, `f_TMA`, `e_MMA`, `e_MUFU`, `T_launch`), but `calibrate.py` and `calibration_params.json` show that the combined predictor only calibrates four (`hbm_factor`, `mma_efficiency`, `mufu_efficiency`, `launch_overhead_us`) while `l2_factor`, `tma_factor`, and `smem_factor` are fixed at defaults.
  2. Related Work contains unresolved citation placeholders (`[citation: FlashAttention-1/2]`, `[citations: roofline; GPU performance modeling]`, etc.) and the References section lists only arXiv IDs without full BibTeX.
  3. Figures 1–3 are described but not rendered; the paper bundle defers rendering to a later plotting stage.

## Strengths

- The manuscript structure follows the outline and covers all required sections (Abstract, Introduction, Related Work, Method, Experiments, Results, Limitations, Conclusion).
- The core numerical claims are traceable to `validation_metrics.json` and `combined_predictions.csv`: combined MAPE 4.50%, baseline MAPE 22.22%, 100% within 30% error, 100% bottleneck accuracy.
- The emulator caveat is stated early and repeated in Limitations, keeping the claim boundary explicit.
- The ablation design cleanly isolates occupancy, effective bandwidth, and precision effects.
- The predictor source code (`predictor.py`, `calibrate.py`, `constants.py`) is auditable and bounded, matching the white-box framing.

## Weaknesses

- **Calibration-factor misstatement.** Sections 3.3, 3.4, and 5.6 describe a six-factor calibration for the combined model, but the actual calibration routine (`calibrate_combined` in `calibrate.py`) only searches `hbm_factor`, `mma_efficiency`, `mufu_efficiency`, and `launch_overhead_us`. The values `f_L2 = 0.45` and `f_TMA = 0.70` reported in section 5.6 come from the `tma_l2_effective_bw` ablation, not from the combined model. This is a material misrepresentation of the method.
- **Citation placeholders remain in the prose.** Related Work uses bracket placeholders instead of real citations, and the References section is incomplete.
- **No rendered figures.** The paper cannot be considered camera-ready until Figures 1–3 are generated from the data.
- **No BibTeX.** Citation legitimacy was already marked partial by the write stage; the review confirms this remains a blocker for final submission.
- **References section delegates work.** The line "FlashAttention-1/2 and FlashAttention-3 citations as per the literature scouting report" is not a reference entry.

## Key Issues

### Issue 1 — Combined-model calibration factors are misstated

- why it matters: The manuscript's central claim is that the predictor is a *white-box, interpretable* model with bounded, calibrated corrections. If the reader is told six factors were calibrated but the code and artifact only calibrate four, the interpretability claim and the reported factor values become unreliable. A reviewer will check the calibration artifact and code.
- evidence anchor: `calibration_params.json` in operation set `20260704-130224-experiment-7f255a5e` shows `"combined": {"hbm_factor": 0.85, "mma_efficiency": 0.85, "mufu_efficiency": 0.85, "launch_overhead_us": 0.5}`; `calibrate.py` `calibrate_combined` grids only those four keys and hardcodes `l2_factor=0.70`, `tma_factor=0.65`, `smem_factor=0.90` in `build()`.
- risk level: high (scientific accuracy)
- likely route: revise text; no new experiment needed

### Issue 2 — Placeholder citations and incomplete reference list

- why it matters: Unresolved placeholders prevent the manuscript from being submission-ready. The Related Work section cannot be evaluated without real citations, and the current References section does not support the breadth of prior work discussed.
- evidence anchor: draft-section-set.md Related Work section lines 27–33 and References section lines 250–255.
- risk level: medium (submission readiness)
- likely route: finalize stage or a citation-polish pass

### Issue 3 — Figures 1–3 are described but not rendered

- why it matters: The manuscript references three figures that do not yet exist. While the descriptions are concrete, a final paper must include the actual plots.
- evidence anchor: paper-bundle-manifest outstanding_items and draft-section-set.md Figure 1/2/3 placeholders.
- risk level: medium (production readiness)
- likely route: `isomer-deepsci-paper-plot` or `isomer-deepsci-figure-polish`

## Actionable Suggestions

### Suggestion 1 — Correct the calibration description

- problem: Sections 3.3, 3.4, and 5.6 claim the combined model calibrates six factors, but only four are calibrated.
- cause: The ablation model `tma_l2_effective_bw` calibrates `l2_factor` and `tma_factor`; those values were copied into the combined-model description.
- actionable fix: Rewrite the Method and Results text to state that the combined model calibrates four factors (`hbm_factor`, `mma_efficiency`, `mufu_efficiency`, `launch_overhead_us`) and fixes `l2_factor=0.70`, `tma_factor=0.65`, `smem_factor=0.90` at their defaults. Report the ablation's `l2_factor=0.45` and `tma_factor=0.70` only in the ablation subsection.
- acceptance criterion: Every calibration claim in the manuscript matches `calibration_params.json` and `calibrate.py`.
- copy-ready revision text:
  - Section 3.4: "Calibration of the combined model is a bounded grid search over four interpretable factors — `hbm_factor`, `mma_efficiency`, `mufu_efficiency`, and `launch_overhead_us` — while `l2_factor`, `tma_factor`, and `smem_factor` are held at their default values (0.70, 0.65, 0.90)."
  - Section 5.6: "The calibrated bounded factors are `hbm_factor = 0.85`, `mma_efficiency = 0.85`, `mufu_efficiency = 0.85`, and `launch_overhead_us = 0.5 μs`. The `l2_factor` and `tma_factor` values reported for the TMA/L2 effective-bandwidth ablation are 0.45 and 0.70, respectively; the combined model keeps these factors fixed at 0.70 and 0.65."
- Tectonic-preferred LaTeX-ready revision text: same content, with `$\mu s$` for microseconds and math-mode factor symbols.

### Suggestion 2 — Resolve placeholder citations

- problem: Related Work placeholders are not real citations.
- cause: Write stage deferred full citation expansion.
- actionable fix: Replace placeholders with entries drawn from `artifact-LITERATURE_SCOUTING_REPORT-fc6d5ca8b4a3` and `artifact-LITERATURE_SURVEY_REPORT-1cf5125a64f8`. Add full BibTeX entries to the `.bib` file.
- acceptance criterion: No bracket-style placeholders remain; every cited work has a BibTeX entry.

### Suggestion 3 — Render deferred figures

- problem: Figures 1–3 are described but absent.
- cause: Deferred to a plotting stage.
- actionable fix: Generate the three figures from `combined_predictions.csv` and `validation_metrics.json` using the descriptions in the draft.
- acceptance criterion: Figure files exist and are referenced correctly in the LaTeX/Markdown source.

## Storyline Options + Writing Outlines

- current narrative weakness: The storyline is actually coherent; the weakness is execution (citations, figures, and the calibration misstatement).
- stronger storyline option: Keep the current structure. After the calibration correction, emphasize that even with only four free factors the combined model reaches 4.50% MAPE — a stronger argument for parsimony.
- outline change needed: None.

## Priority Revision Plan

1. Correct the combined-model calibration description in Method (Sections 3.3–3.4) and Results (Section 5.6). Verify against `calibration_params.json` and `calibrate.py`.
2. Resolve all Related Work placeholders and produce full BibTeX entries for FA4, Blackwell microbenchmarks, white-box methodology, FlashAttention-1/2, FlashAttention-3, roofline, and GPU performance modeling.
3. Render Figures 1–3 and integrate them into the manuscript.
4. Re-run manuscript validation (claim support, section coverage, language hygiene, citation legitimacy, figure readiness).
5. Route back to review or to finalize depending on validation outcome.

## Manuscript Revision Package

- section: Method / Results
- old wording / weakness: "Calibration is a bounded grid search over the six interpretable factors: `f_HBM`, `f_L2`, `f_TMA`, `e_MMA`, `e_MUFU`, and a small launch overhead." and "The calibrated bounded factors are `f_HBM = 0.85`, `f_L2 = 0.45`, `f_TMA = 0.70`, `e_MMA = 0.85`, `e_MUFU = 0.85`, and `T_launch = 0.5 μs`."
- new wording: "Calibration of the combined model searches four bounded factors (`hbm_factor`, `mma_efficiency`, `mufu_efficiency`, `launch_overhead_us`) while holding `l2_factor=0.70`, `tma_factor=0.65`, and `smem_factor=0.90` fixed. The combined-model factors are `hbm_factor=0.85`, `mma_efficiency=0.85`, `mufu_efficiency=0.85`, and `launch_overhead_us=0.5 μs`. The TMA/L2 ablation separately calibrates `l2_factor=0.45` and `tma_factor=0.70`."
- evidence basis: `calibration_params.json` and `calibrate.py` from operation set `20260704-130224-experiment-7f255a5e`.
- Tectonic-preferred LaTeX-ready replacement block: same text, with `$T_{\text{launch}} = 0.5~\mu s$`.

## Experiment Inventory & Research Experiment Plan

- what existing experiments already cover: The experiment stage already produced all required results: ablation metrics, combined metrics, per-precision/per-bottleneck breakdowns, calibration factors, and predictions CSV. No new measurement is needed.
- what still lacks evidence: None. The blocker is a text misstatement, not missing evidence.
- which gaps are text-only rather than experiment-only: The calibration-factor description, citation placeholders, and missing figure files are all text/production issues.

## Novelty Verification & Related-Work Matrix

### Taxonomy

```text
Root: FlashAttention-4 runtime prediction on NVIDIA B200
├── Baseline / first-order models
│   └── FlashAttention-4 paper roofline
├── White-box analytical extensions
│   └── This work (occupancy + effective bandwidth + precision-specific throughput)
├── Black-box / ML surrogates
│   └── Neural-network or gradient-boosted runtime predictors
└── Measurement infrastructure
    └── Emulator-based white-box ground truth
```

### Comparison Matrix

| Topic | This paper | Closest prior work | Overlap | Residual novelty / value |
| --- | --- | --- | --- | --- |
| FA4 forward attention modeling | White-box predictor with bounded corrections | FA4 paper roofline | Same algorithmic quantities | Adds occupancy, effective bandwidth, precision-specific throughput on B200 |
| B200 bandwidth modeling | Transfer-size-dependent HBM/L2/TMA curves | Blackwell microbenchmark studies | Hardware peak numbers | Embeds curves in an interpretable predictor |
| Bottleneck labeling | Dominant-domain label from white-box breakdown | Roofline bottleneck analysis | Domain names | 100% accuracy on held-out emulator configs |
| Ground truth | High-fidelity emulator | Real silicon measurements | None (emulator vs. silicon) | Emulator-validated only; silicon transfer is future work |

## References

- `artifact-DRAFT_SECTION_SET-db586e5e0d48`
- `view_manifest-MANUSCRIPT_VALIDATION_REPORT-de3a171ebf2d`
- `artifact-PAPER_BUNDLE_CHECKPOINT-a1f0b0ac3937`
- `artifact-ANALYSIS_CAMPAIGN_SUMMARY-6fc33c201154`
- `view_manifest-CLAIM_EVIDENCE_BOUNDARY-d5c04da9b675`
- `evidence_item-EXPERIMENT_RESULT_SUMMARY-7390c54fdef5`
- `evidence_item-CLAIM_VALIDATION_RECORD-087e55583673`
- `artifact-LITERATURE_SCOUTING_REPORT-fc6d5ca8b4a3`
- `artifact-LITERATURE_SURVEY_REPORT-1cf5125a64f8`
- Operation set `20260704-130224-experiment-7f255a5e` (`calibration_params.json`, `validation_metrics.json`, `combined_predictions.csv`)
- Source code: `repos/topic-main/src/fa4_b200_predictor/predictor.py`, `calibrate.py`, `constants.py`

## Optional Internal Score

- overall score: 6/10 — strong empirical result and clear writing, but the calibration misstatement and missing production artifacts prevent finalization.
- post-revision target: 8/10 after text correction, full citations, rendered figures, and BibTeX.
