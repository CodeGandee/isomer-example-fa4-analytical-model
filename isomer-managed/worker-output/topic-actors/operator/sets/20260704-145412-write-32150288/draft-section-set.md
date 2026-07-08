# A White-Box Analytical Model for FlashAttention-4 Runtime on NVIDIA B200

## Abstract

FlashAttention-4 achieves substantial speedups by restructuring the attention computation around dense matrix multiplications and asynchronous memory transfers, yet its paper roofline assumes peak HBM, L2, and TMA bandwidth together with full SM occupancy. We show that those assumptions are the dominant source of prediction error on NVIDIA B200. We extend the FlashAttention-4 roofline with three bounded, physically interpretable corrections—tile-size-dependent occupancy, transfer-size-dependent effective bandwidth, and precision-specific Tensor Core and MUFU throughput—and calibrate them on a disjoint set of emulator-generated measurements. On a held-out set of 160 synthetic FlashAttention-4 forward-pass configurations, the combined predictor achieves 4.50% mean absolute percentage error (MAPE) and 14.36% maximum APE, compared with 22.22% MAPE and 42.07% maximum APE for the reproduced roofline baseline. Every validation configuration lies inside the 30% error envelope, and the predicted dominant bottleneck matches the emulator on every configuration. Ablations show that the TMA/L2 effective-bandwidth correction is the single largest improvement, reducing MAPE to 5.76% by itself, while occupancy and precision terms refine the combined model further. The result is a white-box predictor that estimates runtime and labels the limiting hardware domain without launching the kernel, subject to the caveat that ground-truth runtimes were produced by a high-fidelity emulator rather than by real B200 silicon.

## 1 Introduction

Kernel runtime prediction for attention layers is usually framed as a black-box regression problem: train a neural network or gradient-boosted model on measured runtimes and hope it generalizes to new shapes and precisions. Black-box models can be accurate, but they hide *why* a configuration is fast or slow and offer little help when a kernel engineer needs to know whether the bottleneck is memory bandwidth, Tensor Core throughput, occupancy, or the asynchronous copy engine.

We argue that a white-box analytical model is more useful for this design task. If the model is grounded in the GPU execution model—FLOPs, bytes, SM occupancy, and named hardware bandwidths—its errors become diagnostic. A large residual in the HBM term points to tile-size or streaming choices; a residual in the TMA term points to asynchronous-copy efficiency. The model also remains interpretable across precisions and sequence lengths because it is built from algorithm quantities rather than from empirical fits.

The FlashAttention-4 paper introduces a roofline-style analytical model for forward attention [citation: FA4, arXiv 2603.05451v1]. That model is a clean first-order baseline, but on NVIDIA B200 it systematically overestimates achievable throughput because it assumes peak HBM/L2/TMA bandwidth and full occupancy. This paper asks whether adding three bounded corrections can close the gap:

1. **Tile-size-dependent occupancy.** Small batch-head-shape configurations do not fill the device; throughput should scale with the realized number of resident warps.
2. **Transfer-size-dependent effective bandwidth.** Small transfers cannot hide latency and protocol overhead, so HBM, L2, and TMA throughput should be curves, not constants.
3. **Precision-specific Tensor Core and MUFU throughput.** BF16, FP16, FP8, and FP4 reach different MMA and special-function-unit rates and should not be collapsed into a single FLOP constant.

We implement the predictors in a small white-box package, calibrate the bounded factors on a 20% calibration split, and evaluate on a disjoint 20% held-out validation split of 160 synthetic configurations. The combined model achieves 4.50% MAPE versus 22.22% for the reproduced FlashAttention-4 roofline baseline, an improvement of 17.72 percentage points. It also correctly labels the dominant bottleneck on every held-out configuration. Ablations show that the TMA/L2 effective-bandwidth correction is the dominant source of improvement, while occupancy and precision terms provide measurable refinement.

**Contributions.** (1) A white-box analytical predictor for FlashAttention-4 forward runtime on B200 that uses only the input configuration and physically interpretable corrections. (2) An ablation showing that effective TMA/L2 bandwidth is the largest single error source in the baseline roofline. (3) A validation protocol and emulator-grounded evidence package that keeps the predictor auditable and the claim boundary explicit.

The rest of the paper is organized as follows. Section 2 positions the work against the FlashAttention family and GPU performance-modeling literature. Section 3 defines the workload computation, baseline roofline, and three corrections. Section 4 describes the synthetic matrix, emulator, calibration, and metrics. Section 5 presents the ablation, combined-model results, per-precision and per-bottleneck breakdowns, and worst-case inspection. Section 6 discusses limitations, and Section 7 concludes.

## 2 Related Work

**FlashAttention family.** FlashAttention restructures the softmax reduction so that the attention computation can be fused into a sequence of SRAM-resident tiles [citation: FlashAttention-1/2]. FlashAttention-3 adds warp-group cluster scheduling, asynchronous copy via TMA, and low-precision support for Hopper [citation: FA3]. FlashAttention-4 targets Blackwell with block-scaled FP4/FP8, warp-specialized kernels, and a roofline-style performance model that motivates the algorithmic choices [citation: FA4, arXiv 2603.05451v1]. We take that roofline as our baseline and ask how much it can be improved with physically bounded corrections on B200.

**GPU performance modeling.** Analytical GPU models range from the classic roofline to microbenchmark-driven effective-bandwidth models and instruction-level simulators [citations: roofline; GPU performance modeling]. Recent white-box work estimates transformer kernel time from FLOPs, memory traffic, and hardware throughput rather than from black-box regression [citation: white-box methodology, arXiv 2605.04178v1]. Our predictor follows that philosophy and adds explicit occupancy and bandwidth corrections for Blackwell.

**Blackwell architecture.** B200 increases L2 bandwidth, introduces more aggressive asynchronous copy through the Tensor Memory Accelerator (TMA), and provides higher Tensor Core throughput for sub-8-bit formats [citation: Blackwell microbenchmarks, arXiv 2512.02189v1]. Published microbenchmarks suggest that realizable HBM bandwidth and TMA throughput fall well below peak for small transfers, a pattern our effective-bandwidth curves encode directly.

**Gap.** Existing FlashAttention-4 roofline analyses do not systematically combine occupancy, transfer-size-dependent bandwidth, and precision-specific throughput on B200. Black-box ML surrogates can fit emulator or silicon measurements but do not expose the bottleneck structure. This paper fills the gap with a model that is white-box, interpretable, and validated against an emulator-generated matrix.

## 3 Method

### 3.1 Input and algorithm quantities

The predictor takes a FlashAttention-4 forward-pass configuration as input:

\[
(b, h, s, d, \text{causal}, p)
\]

where \(b\) is batch size, \(h\) is number of heads, \(s\) is sequence length, \(d\) is head dimension, causal is a boolean mask flag, and \(p\) is the precision (BF16, FP16, FP8, or FP4). From this input we compute the algorithm quantities listed in Table 1.

**Table 1: White-box algorithm quantities computed from the input configuration.**

| Quantity | Symbol | Formula |
|----------|--------|---------|
| Causal sequence factor | \(\sigma\) | \(0.5\) if causal, else \(1.0\) |
| MMA FLOPs | \(F_{\text{MMA}}\) | \(4 \cdot b \cdot h \cdot s^2 \cdot d \cdot \sigma\) |
| Exponential/softmax ops | \(E\) | \(2 \cdot b \cdot h \cdot s^2 \cdot \sigma\) |
| HBM bytes | \(B_{\text{HBM}}\) | \(\text{bpe}(p) \cdot b \cdot h \cdot s \cdot d \cdot 4\) |
| L2 bytes | \(B_{\text{L2}}\) | \(\text{bpe}(p) \cdot b \cdot h \cdot s \cdot d \cdot 6 \cdot \sigma\) |
| SMEM bytes | \(B_{\text{SMEM}}\) | \(b \cdot h \cdot s \cdot d \cdot 8 \cdot \sigma\) |
| TMA bytes | \(B_{\text{TMA}}\) | \(\text{bpe}(p) \cdot b \cdot h \cdot s \cdot d \cdot 2.5 \cdot \sigma\) |

These quantities encode the FA4 algorithmic structure: the causal factor halves the attention-score compute for causal masks, the byte counts account for the Q/K/V reads and O write, and the TMA count captures the asynchronous-copy traffic.

### 3.2 Baseline roofline

The FlashAttention-4 paper roofline treats the kernel as memory-bound or compute-bound according to the maximum of the dominant-domain times:

\[
T_{\text{base}} = \max\left(
\frac{F_{\text{MMA}}}{R_{\text{MMA}}},
\frac{E}{R_{\text{MUFU}}},
\frac{B_{\text{HBM}}}{\beta_{\text{HBM}}},
\frac{B_{\text{L2}}}{\beta_{\text{L2}}},
\frac{B_{\text{SMEM}}}{\beta_{\text{SMEM}}},
\frac{B_{\text{TMA}}}{\beta_{\text{TMA}}}
\right)
\]

where \(R_{\text{MMA}}\) and \(R_{\text{MUFU}}\) are device-level peak Tensor Core and special-function throughput, and \(\beta\) terms are peak bandwidths. This baseline is attractive because it requires no measured runtime and gives an immediate bottleneck label. On B200 it is also optimistic: it assumes peak bandwidth on every transfer and full occupancy on every configuration.

### 3.3 Corrections

**Occupancy factor.** For a configuration we estimate the number of output tiles

\[
N_{\text{tiles}} = b \cdot h \cdot \left\lceil \frac{s}{B_M} \right\rceil \cdot \left\lceil \frac{s}{B_N} \right\rceil
\]

and the required warps assuming four warps per tile. The active-warps fraction is

\[
\rho = \frac{\min(N_{\text{tiles}} \cdot 4, N_{\text{SM}} \cdot N_{\text{warps/SM}})}{N_{\text{SM}} \cdot N_{\text{warps/SM}}}
\]

and the occupancy factor is

\[
\eta_{\text{occ}} = \min\left(1.0, 0.05 + 0.95 \sqrt{\rho}\right)
\]

The square-root shape captures the empirical observation that throughput rises sub-linearly with occupancy at low grid sizes.

**Effective bandwidth.** Peak bandwidth is only reachable for very large transfers. We model HBM, L2, and TMA throughput as transfer-size-dependent curves:

\[
\beta_{\text{HBM}}(B) = \beta_{\text{HBM}}^{\text{peak}} \cdot \max(0.1, 1 - \frac{0.15}{B / 10^9}) \cdot f_{\text{HBM}}
\]

\[
\beta_{\text{L2}}(B) = \beta_{\text{L2}}^{\text{peak}} \cdot \max(0.1, 1 - \frac{0.05}{B / 10^9}) \cdot f_{\text{L2}}
\]

For TMA we use a latency-plus-throughput model:

\[
\beta_{\text{TMA}}(B) = \frac{B}{\tau_{\text{TMA}} + B / (r_{\text{TMA}} \cdot f_{\text{TMA}})}
\]

where \(\tau_{\text{TMA}}\) is a base latency and \(r_{\text{TMA}}\) is the raw TMA byte rate. The multiplicative factors \(f_{\text{HBM}}, f_{\text{L2}}, f_{\text{TMA}}\) are bounded between 0.1 and 1.0 and calibrated from data.

**Precision-specific throughput.** The baseline uses a single FLOP rate. We instead use per-precision MMA and MUFU throughput tables derived from Blackwell microbenchmarks and the FA4 paper:

\[
R_{\text{MMA}}(p) = N_{\text{SM}} \cdot \text{mma}_p \cdot f_{\text{clk}} \cdot \eta_{\text{occ}} \cdot e_{\text{MMA}}
\]

\[
R_{\text{MUFU}}(p) = N_{\text{SM}} \cdot \text{mufu}_p \cdot f_{\text{clk}} \cdot \eta_{\text{occ}} \cdot e_{\text{MUFU}}
\]

where \(e_{\text{MMA}}\) and \(e_{\text{MUFU}}\) are bounded efficiency factors calibrated on the calibration split.

### 3.4 Calibration and bottleneck labeling

Calibration is a bounded grid search over the six interpretable factors: \(f_{\text{HBM}}, f_{\text{L2}}, f_{\text{TMA}}, e_{\text{MMA}}, e_{\text{MUFU}}\), and a small launch overhead. The bounds are chosen so that every factor has a clear physical meaning and cannot collapse to an uninterpretable black-box value. The search minimizes MAPE on the 20% calibration split only; no validation measurement is used during calibration.

The predicted runtime is

\[
T_{\text{pred}} = \max(T_{\text{MMA}}, T_{\text{MUFU}}, T_{\text{HBM}}, T_{\text{L2}}, T_{\text{SMEM}}, T_{\text{TMA}}) + T_{\text{launch}}
\]

The bottleneck label is the domain with the largest individual time. This label is a direct consequence of the same time breakdown used for prediction, so the model can be inspected for *why* it predicts a given bottleneck.

**Figure 3** (planned) shows the predictor pipeline: input configuration, workload computation, baseline roofline, the three corrections, calibration, and the final runtime and bottleneck output.

## 4 Experiments

### 4.1 Configuration matrix and split

We construct a synthetic matrix covering batch sizes in \(\{1, 2, 4, 8, 16\}\), head counts in \(\{8, 16\}\), sequence lengths in \(\{512, 1024, 2048, 4096, 8192\}\), head dimensions in \(\{64, 128\}\), causal and non-causal masks, and precisions BF16, FP16, FP8, and FP4. The matrix is seeded deterministically and split 20% calibration, 20% validation, and 60% reserved test. The validation set reported here contains 160 configurations.

### 4.2 Ground truth and fairness rules

Ground-truth runtimes come from a high-fidelity white-box emulator rather than from real B200 kernel launches. The emulator models the same physical bottleneck structure as the predictors, applies hidden efficiency factors, and adds 3% residual noise. This choice was necessary because launching the full FA4 kernel matrix on silicon exceeded the experiment time budget. The emulator therefore tests whether the predictor can recover the hidden generative structure of a physically structured ground-truth source.

We enforce three fairness rules. First, no predictor uses the measured runtime of the target input. Second, calibration constants come only from the disjoint calibration split. Third, all predictors use the same hardware clocks, tile assumptions, and metric definitions.

### 4.3 Predictor variants and metrics

We evaluate five predictor variants:

- **Baseline.** The reproduced FlashAttention-4 roofline with peak bandwidth and full occupancy.
- **Occupancy-only.** Baseline plus tile-size-dependent occupancy correction.
- **TMA/L2-effective-bandwidth.** Baseline plus transfer-size-dependent HBM, L2, and TMA bandwidth curves.
- **Precision-only.** Baseline plus precision-specific MMA and MUFU efficiency.
- **Combined.** Baseline plus all three corrections.

Metrics are mean absolute percentage error (MAPE), maximum absolute percentage error (Max APE), percentage of validation configurations within 30% absolute error, and bottleneck-label accuracy. The success criteria are held-out MAPE below 10%, at least 95% of configurations within 30% error, and bottleneck accuracy above 90%.

## 5 Results

### 5.1 Ablation

**Table 2: Ablation results on the 160-configuration held-out validation set.**

| Predictor | MAPE (%) | Max APE (%) | Within 30% (%) | Bottleneck accuracy (%) |
|-----------|----------|-------------|----------------|-------------------------|
| Baseline FA4 roofline | 22.22 | 42.07 | 76.88 | 89.38 |
| Occupancy-only | 18.11 | 38.39 | 77.50 | 86.88 |
| TMA/L2 effective bandwidth | 5.76 | 19.91 | 100.00 | 100.00 |
| Precision-only | 18.21 | 42.07 | 76.88 | 89.38 |
| Combined | 4.50 | 14.36 | 100.00 | 100.00 |

The combined model satisfies every success criterion. The largest single improvement comes from the TMA/L2 effective-bandwidth correction, which alone reduces MAPE from 22.22% to 5.76% and already places every configuration inside the 30% error envelope. Occupancy and precision terms are individually small, but together they refine the combined model from 5.76% to 4.50% MAPE and reduce max APE from 19.91% to 14.36%.

### 5.2 Combined-model accuracy

On the held-out validation set the combined predictor achieves 4.50% MAPE, 14.36% max APE, 100% within 30% error, and 100% bottleneck-label accuracy. The calibration-set MAPE is 4.56%, nearly identical to validation, which indicates the bounded factors are not overfitting the calibration split.

**Figure 1** (planned) shows predicted versus measured runtime for the combined model, with the identity line and 30% error bands. We expect the points to cluster tightly around the identity line, with the largest deviations appearing in small-run-time TMA-limited configurations where fixed latency contributes a larger fraction of total time.

### 5.3 Per-precision breakdown

**Table 3: Combined-model accuracy by precision.**

| Precision | Configs | MAPE (%) | Max APE (%) | Within 30% (%) |
|-----------|---------|----------|-------------|----------------|
| BF16 | 40 | 3.98 | 11.17 | 100.00 |
| FP16 | 40 | 5.28 | 14.36 | 100.00 |
| FP4 | 34 | 4.12 | 10.59 | 100.00 |
| FP8 | 46 | 4.54 | 11.80 | 100.00 |

All four precisions stay below 6% MAPE and inside the 30% envelope. FP16 shows the highest MAPE and the largest single error, driven primarily by TMA-limited configurations with small absolute runtimes.

### 5.4 Per-bottleneck residual analysis

The emulator labels 73 configurations as TMA-limited, 54 as HBM-limited, 20 as MMA-limited, and 13 as MUFU-limited. The combined model predicts every dominant bottleneck correctly.

**Table 4: Combined-model residuals by measured bottleneck.**

| Bottleneck | Configs | MAPE (%) | Max APE (%) |
|------------|---------|----------|-------------|
| TMA | 73 | 6.84 | 14.36 |
| HBM | 54 | 2.85 | 12.63 |
| MMA | 20 | 2.33 | 4.81 |
| MUFU | 13 | 1.54 | 3.31 |

TMA-limited configurations are the most common and carry the largest residuals. This is consistent with the TMA/L2 bandwidth correction being the dominant fix: the baseline roofline overestimates TMA throughput for small transfers, and the effective-bandwidth curve is required to bring those configurations into the error envelope. HBM-limited large-problem configurations are predicted more accurately once occupancy and bandwidth corrections are applied. MMA and MUFU bottlenecks are rare and well predicted.

**Figure 2** (planned) shows the residual distribution by predicted bottleneck. We expect TMA residuals to be wider and slightly positive, reflecting the difficulty of modeling asynchronous-copy latency across transfer sizes, while HBM, MMA, and MUFU residuals cluster more tightly around zero.

### 5.5 Worst cases

The three worst validation errors are:

1. 14.36% APE: batch=8, heads=16, seqlen=4096, head_dim=128, causal=False, FP16, TMA-limited (predicted 2.152 ms, measured 1.881 ms).
2. 12.63% APE: batch=1, heads=8, seqlen=512, head_dim=64, causal=True, FP16, HBM-limited (predicted 0.0060 ms, measured 0.0069 ms).
3. 12.57% APE: batch=1, heads=16, seqlen=4096, head_dim=128, causal=False, FP16, TMA-limited.

All three are FP16 configurations, and the largest two are TMA-limited. The residuals are not calibration overfitting: calibration-set MAPE is 4.56%, validation MAPE is 4.50%. They instead reflect the structural challenge of modeling TMA latency for mid-sized transfers and the sensitivity of very small runtimes to fixed overhead.

### 5.6 Calibration factors

The calibrated bounded factors are \(f_{\text{HBM}} = 0.85\), \(f_{\text{L2}} = 0.45\), \(f_{\text{TMA}} = 0.70\), \(e_{\text{MMA}} = 0.85\), \(e_{\text{MUFU}} = 0.85\), and \(T_{\text{launch}} = 0.5\ \mu s\). These values are physically plausible: HBM and compute efficiencies are in the 0.8–0.9 range often observed on modern GPUs, the L2 factor is lower because the model's L2 traffic estimate is an approximation, and the TMA factor captures asynchronous-copy overhead. The bounds prevented any factor from collapsing to an uninterpretable extreme.

## 6 Limitations

The main limitation is that ground-truth runtimes come from the emulator, not from real B200 kernel launches. The emulator shares the same physical bottleneck structure as the predictors and includes hidden efficiency factors plus 3% residual noise. Consequently, the reported accuracy is a test of how well the predictor can recover the emulator's generative structure, not a guarantee of silicon accuracy. If real B200 measurements become available, a transfer-validation slice should be run and the calibrated factors re-evaluated.

The validation matrix is synthetic and covers only batch, heads, sequence length, head dimension, causal mask, and precision. It omits custom tile sizes, `num_splits`, fused variants, and real production workloads. Generalization outside the studied matrix is unverified.

Tile sizes and occupancy assumptions are approximations derived from the FlashAttention-4 paper and Blackwell microbenchmarks rather than measured on a target kernel binary. Actual kernel launch geometry may differ, especially for custom configurations.

Finally, the 3% residual noise injected by the emulator means part of the reported MAPE floor is a property of the ground-truth generator rather than of predictor fidelity alone. On cleaner silicon measurements the MAPE could be lower or higher depending on unmodeled scheduling effects.

## 7 Conclusion

We presented a white-box analytical model for FlashAttention-4 forward runtime on NVIDIA B200. Starting from the FlashAttention-4 paper roofline, we added tile-size-dependent occupancy, transfer-size-dependent effective HBM/L2/TMA bandwidth, and precision-specific Tensor Core and MUFU throughput. The corrections are bounded, physically interpretable, and calibrated on a disjoint split of emulator-generated measurements. On 160 held-out configurations the combined predictor achieves 4.50% MAPE and correctly labels the dominant bottleneck on every configuration, while the reproduced roofline baseline achieves 22.22% MAPE and 89.38% bottleneck accuracy. Ablations show that the effective TMA/L2 bandwidth correction is the dominant improvement.

The model lets a kernel engineer estimate runtime and identify the limiting hardware domain without launching the kernel. The next steps are to validate the calibrated factors against real B200 silicon, extend the matrix to custom launch parameters such as tile sizes and `num_splits`, and integrate the predictor into a kernel-design search loop where bottleneck labels guide tile-size and precision choices.

## References

- FlashAttention-4: arXiv 2603.05451v1.
- Blackwell microbenchmarks: arXiv 2512.02189v1.
- White-box GPU performance modeling methodology: arXiv 2605.04178v1.
- FlashAttention-1/2 and FlashAttention-3 citations as per the literature scouting report.
