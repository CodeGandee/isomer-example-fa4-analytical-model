# Selected Hypothesis: Inner-GPU Analytical Model for FlashAttention-4 on B200

## Claim
A white-box runtime predictor for FlashAttention-4 on NVIDIA B200 can be pushed beyond the coarse `max(FLOPs/peak, bytes/bandwidth)` roofline by explicitly modeling the inner-GPU mechanisms that AccelSim/GPGPU-Sim exposes: warp-scheduler issue throughput, tensor-core MMA issue rate and pipeline latency hiding, L1/L2 sector-cache traffic, HBM row-locality and bank-level-parallelism effects, and crossbar contention. The dominant component predicted by this inner-GPU model will correlate more tightly with measured kernel runtime than the existing coarse predictor, after calibration against a small set of hardware timings.

## Mechanism sketch
1. **Compute-issue bound**: total warp instructions (MMA, memory, MUFU) divided by aggregate scheduler issue rate (`schedulers_per_sm × issue_rate × num_sms × clock × operand_collector_efficiency`).
2. **Tensor-core throughput bound**: MMA FLOPs divided by effective tensor-core rate, scaled by occupancy.
3. **Execution-pipeline / occupancy bound**: tensor-core throughput inflated when resident warps cannot cover the tensor-core latency (`tc_latency / ii`).
4. **MUFU throughput bound**: softmax `exp` ops divided by MUFU rate.
5. **Memory-pipeline bound**: maximum of L1, L2, and HBM transfer times; HBM bandwidth is derated by row-buffer hit rate, bank-level parallelism, and read/write turnaround tax.
6. **Interconnect bound**: additive crossbar serialization when many SMs miss simultaneously.

Overall runtime is `max(compute_bound, memory_bound) + interconnect_tax + launch_overhead`.

## Anti-win condition
If the inner-GPU model does not reduce prediction error relative to the existing coarse predictor on the calibration set, or if the extra parameters cannot be grounded in AccelSim semantics or measurable hardware counters, the added complexity is not justified.

## Minimal validation
- Calibrate the six hardware parameters (`mma_throughput_per_sm_per_clock`, `operand_collector_efficiency`, `l1_miss_rate`, `l2_miss_rate`, `hbm_row_buffer_hit_rate`, `xbar_contention_exponent`) on 3–5 measured B200 FA4 configurations.
- Compare mean absolute percentage error (MAPE) against the existing `predictor.py`/`improved_predictor.py` baseline on a held-out set of configurations.
- Use NCU or Nsight Compute to confirm which component is actually dominant for each configuration.

## Abandonment condition
If NCU shows that the kernel is neither compute-issue nor HBM-bandwidth bound but instead limited by an unmodeled mechanism (e.g., TMA setup, warp-specialization serialization, or Blackwell-specific FP4 tensor-core scheduling), abandon this model and route back to scout/idea.

## Next route
Implement the model in `inner_gpu_model.py`, integrate it as an optional backend in the existing `fa4_b200_predictor` package, and run the calibration/validation experiment.
