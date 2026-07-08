# Scout Discovery Ledger

Discovery was limited to the route-changing questions identified in `<SCOUT_MINIMUM_UNKNOWNS>`.

## Search / Inspection Passes

| Query / Inspection | Source Surface | Reason | Retained References |
| --- | --- | --- | --- |
| FlashAttention-4 forward-pass roofline and B200 pipeline details | arXiv 2603.05451v1 | Obtain the primary algorithm/hardware source and check whether a usable white-box model already exists | arXiv 2603.05451v1 — retained as algorithm source and seed comparator |
| Blackwell shared-memory and exponential-unit throughput | arXiv 2512.02189v1 | Ground B200 non-MMA hardware parameters independently | arXiv 2512.02189v1 — retained for SMEM/MUFU throughput |
| Cross-GPU analytical modeling methodology | arXiv 2605.04178v1 | Validate modeling approach and identify reusable white-box patterns | arXiv 2605.04178v1 — retained as methodology reference |
| FA4 implementation and benchmark scripts in official repo | `repos/extern/flash-attention` | Verify that source material exists locally and locate tile/schedule code | Official `Dao-AILab/flash-attention` repo (local clone) — retained as algorithm source |
| Existing white-box FA4 predictor or cost model | Local repo + project grep | Confirm no existing model short-circuits the research task | None found — confirms the baseline must be built from scratch |

## Retained References

1. **arXiv 2603.05451v1** — *FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling*.
   - Provenance: primary paper, authors from Princeton/Meta/Colfax/NVIDIA/Georgia Tech/Together AI.
   - Why it matters: gives the forward-pass roofline formulas (MMA, shared-memory traffic, exponential unit), B200 SM count/throughput derivation (148 SMs, 8192 ops/clock/SM for BF16), TMEM/TMA/2-CTA pipeline description, partial exponential emulation, and conditional softmax rescaling.
   - Informs: `<EVALUATION_CONTRACT>`, `<BASELINE_SHORTLIST>`, and the baseline model structure.

2. **arXiv 2512.02189v1** — *Microbenchmarking NVIDIA's Blackwell Architecture*.
   - Provenance: independent microbenchmark study.
   - Why it matters: confirms Blackwell shared-memory read throughput (128 bytes/clock/SM) and MUFU throughput (16 ops/clock/SM), which the FA4 paper also cites.
   - Informs: hardware-parameter choices in the baseline model.

3. **arXiv 2605.04178v1** — *Microbenchmark-Driven Analytical Performance Modeling Across Modern GPU Architectures*.
   - Provenance: analytical GPU modeling paper.
   - Why it matters: provides a reusable methodology for building instruction-level, memory-hierarchy-aware performance models without black-box fitting.
   - Informs: modeling methodology and validation plan.

4. **Official Flash Attention repository** (`https://github.com/Dao-AILab/flash-attention`, local clone at `repos/extern/flash-attention`).
   - Provenance: official implementation.
   - Why it matters: contains the CuTe-DSL FA4 kernel (`flash_attn/cute/`) and benchmark scripts (`benchmarks/`) that will supply tile/schedule details and ground-truth measurements.
   - Informs: baseline implementation and validation data collection.

## Rejected References

- **cuDNN 9.13 and Triton attention implementations**: retained only as indirect plausibility checks (FA4 paper reports speedups over them). They are closed-source or different kernels, so they are not direct baseline comparators for the white-box model.
- **SageAttention family**: targets consumer GPUs and low-precision quantization; outside the B200 datacenter scope of this topic.

## Unresolved Ambiguity

- Exact FA4 tile/occupancy defaults per precision are not stated in the paper; they must be read from the local source or measured.
- The numeric accuracy target is not fixed by the topic intent; it must be proposed by baseline and approved by the operator.

These ambiguities do not block routing to baseline.
