# Actor Definitions

## operator

- **Name**: operator
- **Duty**: Human-orchestrated researcher / lead coder for the white-box FlashAttention-4 runtime model.
- **Intended usage**: Drive the B200 hardware specification capture, derive the algorithmic execution model from the official Flash Attention repository, implement the closed-form Python predictor, and validate predicted runtimes and NCU counters against measurements on this host.
- **Expected cwd label**: `topic.actors.workspace`
- **Actor kind**: operator
- **Runtime kind**: local
- **Role kind**: operator
- **Controller kind**: manual
- **Source env gate requirements**: Pixi env with Python 3.11, NumPy, SymPy, SciPy, Markdown; `ncu` 2025.4.1+ reachable; official `flash-attention` topic repo present.
- **Open actor setup questions**: None.
