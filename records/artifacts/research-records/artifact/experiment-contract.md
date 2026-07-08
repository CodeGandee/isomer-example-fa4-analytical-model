# Experiment Contract: Bottleneck Saturation Validation for FA4 on B200

## Research question
When FlashAttention-4 input configurations are deliberately pushed to saturate one of six hardware resources (Tensor Core MMA, MUFU/SFU, HBM, L2, shared memory, TMA), can the white-box analytical predictor correctly identify the saturated resource, as confirmed by NCU SpeedOfLight counters?

## Selected hypothesis
`artifact-SELECTED_HYPOTHESIS` for bottleneck saturation predictability (see `selected-hypothesis.md`).

## Comparator
- **Comparator identity**: The white-box predictor itself, evaluated on bottleneck-label accuracy per saturation regime.
- **Baseline**: Random or constant bottleneck assignment (expected ~17% for six labels, ~50% for compute-vs-memory).
- **Success threshold**: Overall bottleneck-label accuracy ≥ 75%; each realized regime has ≥ 2 correct predictions out of the configurations tested for that regime.

## Dataset
Synthetic FA4 forward-pass configurations:
- batch ∈ {1, 4, 8, 16}
- heads ∈ {16, 32, 64}
- seqlen ∈ {256, 1024, 4096, 16384}
- head_dim ∈ {64, 128}
- causal ∈ {True, False}
- precision ∈ {bf16, fp16, fp8}
- A deliberately chosen saturation subset (~12–20 configs) that targets each bottleneck term.

## Primary metric
`bottleneck_label_accuracy` — percentage of saturation configurations whose predicted dominant bottleneck matches the NCU-derived dominant bottleneck.

## Required metrics
- `per_regime_accuracy`: correct predictions / total predictions for each targeted bottleneck.
- `predicted_vs_ncu_table`: one row per configuration with predicted label, NCU compute/memory label, and largest model term.
- `runtime_mape` on the saturation set, to ensure the predictor remains accurate under pressure.
- `ncu_counter_csv`: raw SpeedOfLight `Compute (SM) Throughput %` and `Memory Throughput %` for audit.

## Run procedure
1. Implement `saturation_matrix.py` that emits the targeted configurations and runs the existing white-box predictor to get `predicted_runtime_ms` and `predicted_bottleneck`.
2. Measure each configuration on a single B200 (`cuda:0`) with `flash_attn_func`, 3 warmups, 10 timed launches.
3. Profile each configuration with `ncu --section SpeedOfLight --csv ...` filtering the `flash_attn` kernel.
4. Post-process NCU output to extract SM and memory throughput percentages and assign the NCU bottleneck label.
5. Compare predicted and NCU labels and compute accuracy.

## Stop condition
The run stops when all configurations in the saturation matrix have been measured and profiled, or when an unrecoverable error (OOM, NCU failure, unsupported precision) prevents further profiling.

## Expected outputs
- `saturation_predictions.csv`
- `saturation_ncu_results.csv`
- `saturation_accuracy_report.json`
- `experiment_result.json`

## Compute budget
Bounded to ~12–20 NCU profiles on a single B200; estimated wall time < 2 hours.

## Abandonment condition
If fewer than four bottleneck regimes are realizable, or overall accuracy < 60%, the hypothesis is refuted.

## Route linkage
This contract routes from the bottleneck-saturation selected hypothesis; on success it routes to `isomer-deepsci-analysis` for per-regime interpretation.
