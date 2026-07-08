# Main Run Record

## Run identification
- **run id:** 20260706-experiment-overlap-revision-da1fdb
- **command:** `pixi run python overlap_experiment.py`
- **working directory:** `<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model`
- **environment:** topic Pixi env (Python 3.11, flash_attn.cute, ncu 2025.4.1)
- **device:** cuda:0 (B200)

## Commands and configs
- Predictor revision: added `overlap_frac` to `Predictor` and `combined_predictor` in `repos/topic-main/src/fa4_b200_predictor/predictor.py`.
- Calibration script: `overlap_experiment.py`
- Calibration grid: `overlap_frac` ∈ {0.0, 0.25, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9} on original 12 configs.
- Validation: NCU SpeedOfLight on expanded 24-config matrix.

## Outputs
- `overlap_calibration.csv`
- `overlap_ncu_results.csv`
- `overlap_accuracy_report.json`

## Environment facts
- `ncu` 2025.4.1
- `flash_attn.cute` importable in topic Pixi env
- 5x B200 GPUs available; profiling used cuda:0

## Last-known-good state
- Predictor package at `repos/topic-main/src/fa4_b200_predictor/predictor.py` with `overlap_frac` support.
- All existing unit tests pass.

## Completion status
Completed: 24/24 NCU profiles succeeded.
