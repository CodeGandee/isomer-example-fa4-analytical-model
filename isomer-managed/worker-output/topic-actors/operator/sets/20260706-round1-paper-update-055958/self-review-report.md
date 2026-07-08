# Self-Review: GPU Hardware Execution System Diagram Revision

## What changed

- Added Figure 4 (`figures/figure4_gpu_execution_system.svg`) showing the GPU hardware component execution system for FlashAttention-4 on NVIDIA B200.
- Added Section 3.7, a cycle-level hardware execution model that traces Q/K/V loads, Tensor Core MMAs, softmax MUFU operations, and the O store hop-by-hop through the memory hierarchy.
- Updated the abstract, contributions, Section 5.8, limitations, and conclusion to reference the new diagram and cycle-level model.
- Updated `generate_figures.py` to emit the Graphviz DOT source and render the SVG automatically.

## Quality checks

- `pixi run lint` passes with no issues.
- `python generate_figures.py` regenerates all figures, including Figure 4, without errors.
- The revised draft references Figure 4 inline and the figure file is present in `figures/`.
- The diagram distinguishes load (blue), MMA (green), softmax/MUFU (orange), and store (purple) data paths and nests host, GPU, SM, L2, memory partitions, and HBM.

## Concerns and limitations

- The cycle-level model is validated on only eight held-out configurations; the numbers are reported as a consistency check, not a replacement for the 540-config evaluation. This is stated explicitly in Section 5.8.
- The Graphviz layout is acceptable but could be polished further for publication if required.

## Blockers

None.

## Next action

Archive the revision operation set or hand it off for final paper bundle assembly.
