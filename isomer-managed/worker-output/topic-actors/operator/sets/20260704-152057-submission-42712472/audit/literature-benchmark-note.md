# Literature Benchmark Note — FlashAttention-4 White-Box Runtime Model

## Target venue
Unspecified at submission-pass entry; no exact journal policy was checked.

## Strong nearby comparators
- **Zadouri et al., 2026** — FlashAttention-4 roofline model, algorithm quantities, and Blackwell kernel design. This paper takes the roofline as its baseline.
- **Jarmusch & Chandrasekaran, 2025/2026** — Blackwell microbenchmarks providing HBM/L2/TMA and Tensor Core rate assumptions.
- **Williams et al., 2009; Yang et al., 2019** — Roofline and hierarchical roofline framing for GPUs.

## Positioning vs. comparators
The draft does not claim a new attention algorithm; it claims a more accurate white-box predictor of an existing algorithm's runtime on a specific architecture. That residual positioning is narrow but defensible.

## Citation coverage
- Core FA family (Dao et al. 2022; Dao 2023; Shah et al. 2024; Zadouri et al. 2026) is cited.
- GPU modeling and Blackwell microbenchmarks are cited.
- No additional comparator papers surfaced during this audit.

## Risk
The paper's novelty claim rests on accuracy improvement and interpretability, not on a new kernel. A venue expecting algorithmic novelty may ask for stronger positioning; a venue expecting modeling work should find the framing acceptable.
