# Alternative Execution-Flow Models

The main predictor collapses hardware execution into effective bandwidth and
throughput terms. The repository also contains three progressively more
detailed models that expose *which* unit saturates and *which* path blocks.
They are implemented in `detailed_node_model.py` and are kept as alternatives
rather than the primary runtime predictor.

## Node-saturation / per-SM reservation model

`DetailedNodeModel` treats each Blackwell SM as a collection of specialized
pipes—Tensor Cores, SFU, FP32/INT32, the global TMA memory pipe, and the on-SM
TMEM read/write pipe—and predicts which node is the bottleneck.

```python
from fa4_b200_predictor.detailed_node_model import DetailedNodeModel
from fa4_b200_predictor.config_matrix import FA4Config

cfg = FA4Config(batch=4, heads=32, seqlen=4096, head_dim=128, causal=True, precision="bf16")
model = DetailedNodeModel()
pred = model.predict(cfg)
print(pred["saturated_node"])
print(pred["blocking_path"])
```

The model reports:

- `saturated_node`: the hardware unit with the largest required time.
- `blocking_path`: a human-readable description of the dependent path that
  feeds the saturated node.

This is Round 1 of the execution-flow refinement and reaches ≈16.7% validation
MAPE on the small 16/8 split.

## Sub-core partition scheduling model

Round 2 models each SM as four independent sub-core partitions. Warps are
distributed across partitions, and the SM makespan is the busiest partition's
instruction schedule. The partition model is also implemented in
`detailed_node_model.py`; enable it by constructing the partition variant
(see the module docstring for the exact class/flag).

## SASS-level RAW critical-path model

Round 3 traces the read-after-write (RAW) instruction dependency graph for one
FA4 tile block. Nodes are SASS instruction classes (TMA loads,
`tcgen05.mma`, `exp`, FP32 updates, TMA store) and edges are RAW dependencies.
This variant reaches ≈21.2% validation MAPE on the small split but exposes the
finest-grained execution-flow mechanisms.

## When to use which model

| Goal | Recommended model |
|------|-------------------|
| Fast runtime prediction on a broad config matrix | `ImprovedPredictor` |
| Identify the saturating hardware unit | `DetailedNodeModel` (node variant) |
| Study intra-SM scheduling bottlenecks | Partition variant |
| Inspect instruction-fusion or dependency effects | SASS RAW variant |

For calibration details and accuracy numbers, see the final paper PDF and the
result summaries in `records/artifacts/research-records/evidence_item/`.
