# Analysis Campaign Plan

## Route shape
Artifact-backed campaign: three small code-based slices that produce CSV/JSON evidence files and a final analysis-finding record.

## Slice plan

### Slice A: Diagnostic ratios
- **Class:** claim-critical contradiction check
- **Question:** How large is the predicted TMA advantage over MMA for the misclassified TMA configs versus the correctly classified regimes?
- **Intervention:** Compute `tma_time_us / mma_time_us`, `tma_time_us / mufu_time_us`, and `memory_time_us / compute_time_us` for all 12 saturation configs.
- **Fixed conditions:** Same configs, same combined predictor defaults as parent experiment.
- **Metric:** Ratio table and threshold crossing count.
- **Expected output:** `slice_a_diagnostic_ratios.csv`
- **Priority:** 1

### Slice B: Overlap counterfactual
- **Class:** failure-mode explanation / model revision probe
- **Question:** If TMA traffic is assumed to overlap with MMA work (rather than compete in a max() roofline), does the model flip the TMA configs to compute-bound?
- **Intervention:** Replace `runtime_ms = max(mma_t, mufu_t, mem_t)` with a simple overlap model: effective memory time = `mem_t * (1 - overlap_frac)` when compute is active, and label bottleneck by the max of compute and effective memory. Test overlap_frac = 0.0, 0.25, 0.50, 0.75.
- **Fixed conditions:** Same configs; only the overlap assumption changes.
- **Metric:** Coarse accuracy per overlap_frac.
- **Expected output:** `slice_b_overlap_counterfactual.csv`
- **Priority:** 2

### Slice C: Factor sensitivity / calibration sweep
- **Class:** robustness / sensitivity check
- **Question:** Is there a single-factor recalibration (tma_factor, mma_efficiency, or mufu_efficiency) that fixes TMA misclassification while preserving mma/mufu/hbm accuracy?
- **Intervention:** Grid-search `tma_factor` ∈ {0.2, 0.35, 0.5, 0.65, 0.8, 1.0} and `mma_efficiency` ∈ {0.5, 0.65, 0.75, 0.85, 0.95, 1.0} against the saturation matrix using predictor-only labels (no new NCU runs).
- **Fixed conditions:** Same configs; only the two factors vary.
- **Metric:** Coarse accuracy surface; best factor pair.
- **Expected output:** `slice_c_factor_sweep.csv`
- **Priority:** 3

## Stopping rule
Stop after Slice C if a clear revision emerges. If no revision fixes the misclassification, record a blocker for an experiment-level recalibration against measured per-stage hardware counters.
