| Round | Intended node | N | Model matches NCU | Accuracy |
|-------|---------------|---|-------------------|----------|
| 1 | R1: Tensor Core MMA | 4 | 4 / 4 | 100% |
| 2 | R2: FMA compute | 4 | 4 / 4 | 100% |
| 3 | R3: TMA load | 4 | 4 / 4 | 100% |
| 4 | R4: FP32 update | 4 | 4 / 4 | 100% |
| 5 | R5: TMA store | 4 | 4 / 4 | 100% |