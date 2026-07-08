# Round 2: Sub-Core Partition Scheduling Model

## Summary

Round 2 refines the per-SM reservation model by modelling each Blackwell SM as four independent sub-core partitions.  Each partition has its own warp scheduler that can issue one instruction per cycle to one of its execution units (Tensor Core, SFU, FP32/INT32, or LD/ST).  Warps are distributed across partitions, and the SM makespan is determined by the busiest partition.  This captures intra-SM scheduling constraints that a single-pool reservation model cannot represent.

## Model Structure

`B200SubcorePartitionModel` keeps the same FA4 tile-block decomposition as Round 1 but changes how compute is scheduled:

1. **Instruction counts per KV step.** For a representative tile the model counts:
   - `mma_inst` — warp-group MMA instructions for `Q@K^T` and `P@V`.
   - `exp_inst` — warp SFU instructions for softmax exponentiation.
   - `update_inst` — warp FP32/INT32 instructions for online softmax scaling and update.
   - `mem_inst` — 32-byte LD/ST or TMA transactions for K and V loads.

2. **Partition assignment.** Instructions are distributed evenly across the four partitions per SM.  Per-partition cycles are computed as:

\[
T_{\text{part}} = \frac{N_{\text{mma}}}{P \cdot S \cdot \eta_{\text{TC}}} + \frac{N_{\text{exp}}}{P \cdot S \cdot \eta_{\text{SFU}}} + \frac{N_{\text{update}}}{P \cdot S \cdot \eta_{\text{FP}}} + \frac{N_{\text{mem}}}{P \cdot S \cdot \eta_{\text{mem}}}
\]

where \(P = 4\) is the number of partitions per SM and \(S\) is the number of active SMs.

3. **Imbalance penalty.** Real warp assignment is not perfectly uniform.  The model adds a partition-imbalance penalty calibrated to the measurements.

4. **Global memory.** The memory path uses the same L2/HBM effective-bandwidth model as Round 1, but the memory pipe is treated as a global resource rather than a per-SM reservation.

5. **Stage overlap and launch overhead.** Same as Round 1.

## Calibration and Validation

The model was fit to the same 16 calibration / 8 validation B200 measurements.

| Model | Calibration MAPE | Validation MAPE |
|---|---|---|
| Baseline roofline | — | 56.23 |
| Improved predictor | — | 14.89 |
| Cycle-level component model | 7.37 | 13.16 |
| Per-SM reservation model (Round 1) | 8.15 | 16.69 |
| Sub-core partition model (Round 2) | 8.39 | 16.41 |

Round 2 slightly improves over Round 1 on validation (16.41% versus 16.69%) while adding the sub-core scheduling story.  The fitted parameters are:

```json
{
  "tc_efficiency": 3.00,
  "sfu_efficiency": 0.20,
  "fp_efficiency": 3.00,
  "mem_efficiency": 0.98,
  "partition_imbalance_factor": 1.61,
  "stage_overlap_factor": 0.85,
  "launch_overhead_us": 16.40
}
```

The high partition-imbalance factor reflects that, for small tile shapes, warp instruction mixes do not split evenly across four partitions, so the busiest partition dominates the SM makespan.

## Bottleneck Analysis

The model reports a per-partition bottleneck.  On the validation split:

- Large head-dim-128 configurations remain MMA-bound, now attributed to the Tensor Core issue slots across partitions.
- Small or FP8 configurations are memory-bound on the global LD/ST/TMA pipe.
- SFU is rarely the partition bottleneck because the exp work is spread across partitions.

## Strengths and Limitations

**Strengths**

- Models the intra-SM scheduler bottleneck explicitly.
- Explains why small tiles or unbalanced instruction mixes lose throughput even when total reservation cycles look sufficient.
- Still deterministic and fast.

**Limitations**

- Perfectly balanced partition assignment is an approximation; a real kernel scheduler may bin-pack instructions differently.
- The partition-imbalance factor is a coarse scalar rather than a tile-shape-dependent distribution.
- It does not yet model instruction dependencies or the exact SASS instruction sequence.

## Files Produced

- `subcore_partition_model.py` — the model implementation.
- `calibrate_subcore_partition_model.py` — calibration and validation script.
- `predictions.csv` — per-config measured vs. predicted runtimes.
- `summary.json` — MAPE and fitted parameters.
- `subcore_model_spec.json` — calibrated hardware spec.
- `subcore_partition.{dot,pdf,png}` — sub-core partition diagram.
- `subcore_partition_report.md` — this report.

## Next Refinement (Round 3)

Round 3 will model the SASS-level instruction critical path.  Instead of counting instructions by type, it will trace a minimal dependent instruction graph through TMA loads, TMEM staging, `tcgen05.mma` instructions, SFU/FP instructions, and stores, and compute the critical-path length including latencies and read-after-write dependencies.
