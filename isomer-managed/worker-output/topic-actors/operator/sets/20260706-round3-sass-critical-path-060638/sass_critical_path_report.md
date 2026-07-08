# Round 3: SASS-Level Instruction Critical-Path Model

## Summary

Round 3 refines the sub-core partition model by modelling the actual read-after-write (RAW) instruction dependency graph inside one FA4 tile block.  Each node is a SASS instruction class—TMA load, Tensor Core `tcgen05.mma`, SFU `exp`, FP32 scale/update, and TMA store—with a measured issue rate and result latency.  The critical path through the DAG, scaled across iterations, gives the predicted runtime.

## Model Structure

`B200SASSCriticalPathModel` builds a minimal instruction DAG for one representative tile block:

1. **TMA load Q**, **TMA load K**, and **TMA load V** are independent memory instructions.
2. **MMA Q@K^T** depends on Q and K being resident.
3. **SFU exp** depends on the MMA Q@K^T accumulator.
4. **FP scale/update** depends on the exponentiated scores.
5. **MMA P@V** depends on the normalized scores and the V tile.
6. **TMA store O** depends on the MMA P@V output.

For each node the model computes:

- **Throughput cycles**: `count / (partitions · active_SMs · issue_rate · efficiency · occupancy)`.
- **Latency chain**: a one-time pipeline fill/drain cost equal to the sum of latencies along the longest RAW chain.

The per-iteration compute time is the throughput-limited critical path.  Total compute time is `per_iteration_cycles · total_iterations + latency_chain`.  Global memory time is modelled separately and overlapped with compute using the stage-overlap factor.

## Calibration and Validation

The model was fit to the same 16 calibration / 8 validation B200 measurements.

| Model | Calibration MAPE | Validation MAPE |
|---|---|---|
| Baseline roofline | — | 56.23 |
| Improved predictor | — | 14.89 |
| Cycle-level component model | 7.37 | 13.16 |
| Per-SM reservation model (Round 1) | 8.15 | 16.69 |
| Sub-core partition model (Round 2) | 8.39 | 16.41 |
| SASS critical-path model (Round 3) | 16.85 | 21.16 |

Round 3 is the most mechanistically detailed model but also the most constrained: it must reproduce runtime from instruction counts and latencies with only seven free parameters.  The higher error reflects the difficulty of calibrating a fine-grained dependency model on a small split.  The recovered parameters are:

```json
{
  "tma_efficiency": 3.00,
  "tc_efficiency": 0.28,
  "sfu_efficiency": 0.20,
  "fp_efficiency": 3.00,
  "dependency_slack_factor": 2.47,
  "stage_overlap_factor": 0.85,
  "launch_overhead_us": 15.98
}
```

The low fitted TC and SFU efficiencies compensate for the coarse instruction-count model: one `tcgen05.mma` instruction per tile may not map cleanly to the warp-group MMAs used by FA4, and the SFU work is partially fused with the FP update.

## Critical-Path Analysis

On the validation split the critical path is dominated by:

- The `tcgen05.mma` throughput for large head-dim-128 configurations.
- The TMA load/store chain for small or low-precision configurations.
- The RAW latency chain contributes a fixed overhead that matters most at small sequence lengths.

## Strengths and Limitations

**Strengths**

- First model to explicitly represent RAW dependencies among TMA, Tensor Core, SFU, and FP instructions.
- Exposes why certain tile shapes or instruction fusions change runtime even when aggregate FLOPs are constant.
- Provides a natural bridge to microbenchmark-derived per-instruction latencies.

**Limitations**

- Instruction counts per tile are approximate (e.g., one MMA "instruction" hides warp-group and sub-core details).
- The fixed latency-chain model does not capture deep pipelining across many warps.
- Validation MAPE is higher than Round 2, showing that added detail without enough calibration data can hurt accuracy.

## Files Produced

- `sass_critical_path_model.py` — the model implementation.
- `calibrate_sass_critical_path_model.py` — calibration and validation script.
- `predictions.csv` — per-config measured vs. predicted runtimes.
- `summary.json` — MAPE and fitted parameters.
- `sass_model_spec.json` — calibrated hardware spec.
- `sass_critical_path.{dot,pdf,png}` — instruction DAG diagram.
- `sass_critical_path_report.md` — this report.

## Conclusion of the Three-Round Refinement

Across three rounds we moved from a per-hop cycle-level model, to per-SM unit reservations, to sub-core partition scheduling, and finally to a SASS-level instruction dependency graph.  Each round adds execution-flow detail and exposes a different bottleneck mechanism:

- Round 1 names the saturating unit (TC, SFU, TMA memory).
- Round 2 exposes intra-SM scheduler contention.
- Round 3 exposes RAW dependency chains among instruction classes.

The most accurate small-split model remains the cycle-level component model (13.16% validation MAPE).  The reservation and partition models trade a few points of accuracy for interpretability and provide a principled path toward simulator-style detail.  Future work should collect larger calibration grids and per-instruction microbenchmarks to realize the full accuracy potential of the SASS-level model.
