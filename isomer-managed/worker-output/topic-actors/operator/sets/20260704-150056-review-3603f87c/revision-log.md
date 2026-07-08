# Revision Log: FA4 B200 White-Box Runtime Predictor Review

## Revision Summary

- current draft state: `artifact-DRAFT_SECTION_SET-db586e5e0d48` — complete draft sections, internally validated, with two production gaps (citations, figures) and one scientific-accuracy issue (calibration-factor description).
- review_followup_policy: single-round revision; re-route to review after fixes.
- manuscript_edit_mode: targeted text correction plus citation/figure production; no new experiments.
- source_compile_preference: Tectonic first; LaTeX engine fallback only when required or blocked.
- highest-priority fixes:
  1. Correct the combined-model calibration-factor description.
  2. Resolve Related Work citation placeholders and add full BibTeX.
  3. Render Figures 1–3.
- blockers: None that require new experiments; all blockers are text/production artifacts.

## Issue-by-issue log

### Issue REV-001

- source issue: Sections 3.3, 3.4, and 5.6 claim the combined model calibrates six bounded factors (`f_HBM`, `f_L2`, `f_TMA`, `e_MMA`, `e_MUFU`, `T_launch`). The evidence shows the combined model calibrates only four (`hbm_factor`, `mma_efficiency`, `mufu_efficiency`, `launch_overhead_us`) and hardcodes `l2_factor=0.70`, `tma_factor=0.65`, `smem_factor=0.90`.
- severity: high
- why it matters: Misrepresents the method and the interpretability claim; a reviewer checking `calibration_params.json` or `calibrate.py` will flag it.
- fix type:
  - text revision
  - claim downgrade (from "six calibrated factors" to "four calibrated factors plus fixed defaults")
- concrete change:
  - Section 3.3: revise the paragraph on multiplicative factors to distinguish calibrated (`hbm_factor`) and fixed (`l2_factor`, `tma_factor`) bandwidth factors.
  - Section 3.4: state that the combined calibration searches four factors, not six.
  - Section 5.6: report only the four calibrated combined factors; move `l2_factor=0.45` and `tma_factor=0.70` to the TMA/L2 ablation discussion.
- copy-ready revision text: "Calibration of the combined model is a bounded grid search over four interpretable factors — `hbm_factor`, `mma_efficiency`, `mufu_efficiency`, and `launch_overhead_us` — while `l2_factor`, `tma_factor`, and `smem_factor` are held at their default values (0.70, 0.65, 0.90)."
- Tectonic-preferred LaTeX-ready revision text: same, with `$f_{\text{HBM}} = 0.85$`, `$e_{\text{MMA}} = 0.85$`, `$e_{\text{MUFU}} = 0.85$`, `$T_{\text{launch}} = 0.5~\mu s$`.
- status: open
- blocks finalize: yes

### Issue REV-002

- source issue: Related Work contains placeholder citations (`[citation: FlashAttention-1/2]`, `[citation: FA3]`, `[citations: roofline; GPU performance modeling]`) and the References section lists only arXiv IDs.
- severity: medium
- why it matters: Submission-ready manuscripts require resolved citations and a complete bibliography.
- fix type:
  - text revision
  - literature positioning
- concrete change: Replace placeholders with real citations from `artifact-LITERATURE_SCOUTING_REPORT-fc6d5ca8b4a3` and `artifact-LITERATURE_SURVEY_REPORT-1cf5125a64f8`; generate `.bib` entries for all cited works.
- status: open
- blocks finalize: yes

### Issue REV-003

- source issue: Figures 1–3 are described but not rendered.
- severity: medium
- why it matters: A camera-ready paper must contain the actual figures.
- fix type:
  - figure / table regeneration
- concrete change: Generate scatter plot (Figure 1), residual distribution (Figure 2), and pipeline diagram (Figure 3) from `combined_predictions.csv`, `validation_metrics.json`, and the predictor code.
- status: open
- blocks finalize: yes

## Deferred / downgraded items

- item: Silicon transfer-validation experiment
- reason: Real B200 measurements are unavailable and were explicitly scoped out of this paper-pass.
- how the manuscript should reflect the limitation: Keep the existing Limitations paragraph that states the ground truth is emulator-based and that silicon validation is future work.
