# Analysis Slice Records

## Slice A: Diagnostic ratios

### Slice Identity
- **parent object:** Experiment Result Summary `experiment-result-summary-bottleneck-sat-20260706`
- **parent claim or gap:** The combined predictor over-predicts memory/TMA dominance for configs that NCU measures as compute-bound.
- **slice id:** slice-a-diagnostic-ratios
- **slice class:** claim-critical contradiction check
- **evidence question:** How large is the predicted TMA advantage over MMA for the misclassified TMA configs versus the correctly classified regimes?
- **why now:** We need a quantified failure signature before proposing a model revision.

### Execution and Evidence
- **intervention or inspection target:** Compute `tma_time_us / mma_time_us`, `tma_time_us / mufu_time_us`, and `memory_time_us / compute_time_us` for all 12 saturation configs using the combined predictor defaults.
- **fixed conditions:** Same 12 configs and same predictor calibration as the parent experiment.
- **changed conditions:** None (diagnostic only).
- **metric or observable:** Ratio table per config and mean ratios per regime.
- **comparison target:** NCU coarse labels from parent experiment.
- **evidence source:** `analysis_slices.py` run in topic Pixi env.
- **output pointers:** `slice_a_diagnostic_ratios.csv`
- **resource or execution caveats:** None.

### Interpretation
- **status:** completed
- **claim update:** The TMA misclassified configs are **not** extreme outliers: their predicted `tma_time / mma_time` is 1.2-2.4x, while correctly-classified MMA configs are 0.3-0.6x. The model is predicting memory-dominance in a regime where NCU still labels the kernel compute-bound.
- **comparability verdict:** Direct comparison; same configs and predictor as parent experiment.
- **caveat:** Ratios are model-internal; they do not isolate a physical cause.
- **next action:** Test whether adding compute/memory overlap flips the TMA configs without harming other regimes.

---

## Slice B: TMA/MMA overlap counterfactual

### Slice Identity
- **parent object:** Experiment Result Summary `experiment-result-summary-bottleneck-sat-20260706`
- **parent claim or gap:** The max() roofline may over-state memory dominance because real TMA traffic overlaps with MMA warps.
- **slice id:** slice-b-overlap-counterfactual
- **slice class:** failure-mode explanation / model revision probe
- **evidence question:** If TMA traffic is assumed to overlap with MMA work, does the model flip the TMA configs to compute-bound?
- **why now:** Slice A showed the misclassification lives in a moderate ratio band where overlap could change the dominant label.

### Execution and Evidence
- **intervention or inspection target:** Replace `max(compute, memory)` with `max(compute, memory * (1 - overlap_frac))` for overlap_frac ∈ {0.0, 0.25, 0.50, 0.75}.
- **fixed conditions:** Same 12 configs; same per-stage time formulas.
- **changed conditions:** Only the overlap assumption.
- **metric or observable:** Coarse accuracy per overlap_frac and per-regime accuracy.
- **comparison target:** NCU coarse labels from parent experiment.
- **evidence source:** `analysis_slices.py` run in topic Pixi env.
- **output pointers:** `slice_b_overlap_counterfactual.csv`
- **resource or execution caveats:** None.

### Interpretation
- **status:** completed
- **claim update:** Overlap_frac = 0.75 raises coarse accuracy from 66.7% to **91.7%** (11/12). All three TMA configs flip to compute-bound. The remaining misclassification is one HBM config (batch=32, heads=16, seqlen=512, head_dim=64) where NCU labels compute despite a large predicted memory time.
- **comparability verdict:** Direct counterfactual on the same saturation matrix; no new hardware measurements.
- **caveat:** 75% overlap is an upper-bound probe, not a calibrated physical value. The actual overlap fraction may vary with problem size and should be validated against measured per-stage counters or a larger matrix.
- **next action:** Compare the overlap probe against a factor-sensitivity sweep to see which revision is more parsimonious.

---

## Slice C: tma_factor × mma_efficiency calibration sweep

### Slice Identity
- **parent object:** Experiment Result Summary `experiment-result-summary-bottleneck-sat-20260706`
- **parent claim or gap:** A single-factor recalibration might fix the misclassification without adding overlap.
- **slice id:** slice-c-factor-sweep
- **slice class:** robustness / sensitivity check
- **evidence question:** Is there a single-factor recalibration (tma_factor, mma_efficiency) that fixes TMA misclassification while preserving mma/mufu/hbm accuracy?
- **why now:** We need to know whether the failure is better explained by a bandwidth/calibration error or by a structural overlap error.

### Execution and Evidence
- **intervention or inspection target:** Grid-search `tma_factor` ∈ {0.2, 0.35, 0.5, 0.65, 0.8, 1.0} and `mma_efficiency` ∈ {0.5, 0.65, 0.75, 0.85, 0.95, 1.0} on the saturation matrix.
- **fixed conditions:** Same 12 configs; all other factors held at combined predictor defaults.
- **changed conditions:** Only `tma_factor` and `mma_efficiency`.
- **metric or observable:** Coarse accuracy surface; best factor pair.
- **comparison target:** NCU coarse labels from parent experiment.
- **evidence source:** `analysis_slices.py` run in topic Pixi env.
- **output pointers:** `slice_c_factor_sweep.csv`
- **resource or execution caveats:** None.

### Interpretation
- **status:** completed
- **claim update:** The best factor pair is `tma_factor=1.0`, `mma_efficiency=0.5`, also reaching 91.7% coarse accuracy. However, `mma_efficiency=0.5` is outside the plausible physical range for B200 Tensor Cores and would harm runtime prediction accuracy. No realistic single-factor recalibration within the model's current calibration bounds reaches this accuracy.
- **comparability verdict:** Direct sensitivity sweep on the same saturation matrix.
- **caveat:** The sweep only covers two factors; joint tuning with other factors or a different functional form was not explored.
- **next action:** Prefer the overlap revision (Slice B) over the unrealistic efficiency reduction; overlap is the more physically grounded explanation.
