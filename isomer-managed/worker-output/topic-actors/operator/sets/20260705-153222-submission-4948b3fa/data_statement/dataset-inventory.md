# Dataset Inventory

| Dataset | Kind | Form | Supports |
|---|---|---|---|
| Real B200 runtime measurements | generated | `refined_validation_predictions.csv`, `refined_query_predictions.csv` | Tables 2–3, Figures 1–2, all accuracy claims |
| NCU SpeedOfLight profiles | generated | NCU `--section SpeedOfLight` CSVs (not in bundle) | Bottleneck calibration, gamma=3.0, Section 3.6 |
| Synthetic configuration matrix | generated | encoded in measurement CSVs and `generate_figures.py` | Method, matrix coverage, splits |
| White-box predictor code | generated | `generate_figures.py`, model implementation in repository | Figures, predictions, reproducibility |
| Figure source files | generated | `figures/figure1_predicted_vs_measured.svg`, `figures/figure2_residuals_by_bottleneck.svg`, `figures/figure3_pipeline.png` | Figures 1–3 |
| Bibliography | generated | `references.bib` | Citations |
| Reused public literature | reused | cited arXiv preprints | Related work, baseline rates |
