# Execution-Flow Models

The repository contains a family of execution-flow models. The **main proposed
model** is the SASS-level RAW critical-path model (Round 3). The other models
are coarser, runnable approximations that are useful for diagnosis and fast
prediction.

## SASS-level RAW critical-path model (main proposed)

Round 3 models one FA4 tile block as a read-after-write (RAW) instruction
dependency graph. Nodes are SASS instruction classes:

- TMA loads for Q, K, V tiles,
- `tcgen05.mma` for the $Q@K^T$ and $P@V$ Tensor Core contractions,
- SFU `exp` for the online softmax,
- FP32 scale/update instructions for the running $O$ accumulator,
- the TMA store of the final $O$ tile.

Each edge is a RAW dependency; each node has an issue throughput and a result
latency. The critical path is the throughput-limited schedule across the DAG
plus the longest latency chain, scaled across all KV iterations. This model
reaches approximately 21.2% validation MAPE on the small 16/8 B200 split and
is the target abstraction for predicting *which* hardware component and
*which* execution path saturates.

A full standalone implementation of the SASS dependency builder is not yet in
the repository; the paper contains the detailed formulation and calibration.

## Node-saturation / per-SM reservation model (runnable approximation)

`DetailedNodeModel` treats each Blackwell SM as a collection of specialized
pipes--Tensor Cores, SFU, FP32/INT32, the global TMA memory pipe, and the on-SM
TMEM read/write pipe--and predicts which node is the bottleneck.

```python
from fa4_b200_predictor.detailed_node_model import DetailedNodeModel
from fa4_b200_predictor.config_matrix import FA4Config

cfg = FA4Config(batch=4, heads=32, seqlen=4096, head_dim=128, causal=True, precision="bf16")
model = DetailedNodeModel()
pred = model.predict(cfg)
print(pred["saturated_component"])
print(pred["predicted_blocking_path"])
```

The model reports:

- `saturated_component`: the hardware unit with the largest required time.
- `predicted_blocking_path`: a human-readable description of the dependent path
  that feeds the saturated unit.

This is Round 1 of the execution-flow refinement and reaches approximately 16.7% validation
MAPE on the small 16/8 split. It is the closest runnable proxy to the SASS
critical-path model in the current code.

## Sub-core partition scheduling model

Round 2 models each SM as four independent sub-core partitions. Warps are
distributed across partitions, and the SM makespan is the busiest partition's
instruction schedule. The partition model is also implemented in
`detailed_node_model.py`; enable it by constructing the partition variant
(see the module docstring for the exact class/flag). It reaches approximately
16.4% validation MAPE on the small split.

## Fast runtime predictor

For broad configuration matrices where the full execution-flow model is not
required, use `ImprovedPredictor`
(`repos/topic-main/src/fa4_b200_predictor/improved_predictor.py`). It is the
roofline + launch-overhead model used for the 540-configuration B200
evaluation and is documented in [Main predictor](main-predictor.md).

## When to use which model

| Goal | Recommended model |
|------|-------------------|
| Predict saturated hardware component / execution path | SASS RAW critical-path model (paper) |
| Runnable diagnosis of saturating unit | `DetailedNodeModel` (node variant) |
| Study intra-SM scheduling bottlenecks | Partition variant |
| Fast runtime prediction on a broad config matrix | `ImprovedPredictor` |

For calibration details and accuracy numbers, see the final paper PDF and the
result summaries in `records/artifacts/research-records/evidence_item/`.
