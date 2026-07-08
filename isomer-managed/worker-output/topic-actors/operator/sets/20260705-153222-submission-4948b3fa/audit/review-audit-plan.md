# Review Audit Plan

Audit the finalized real-hardware paper bundle before submission packaging.

- Claim set: white-box FA4 B200 predictor accuracy, launch-overhead correction, NCU bottleneck calibration.
- Strongest evidence: 540 real B200 measurements; final validation MAPE 12.62%, query MAPE 10.01%; 100% NCU bottleneck accuracy.
- Weakest evidence: all NCU profiles are compute-bound; memory-bound generalisation untested; fp4 unsupported.
- Likely rejection routes: coverage claims overstated, reproducibility without public repository, reference verification.
- Comparator: reproduced FA4 roofline baseline.
- Language risks: none material; minor reference hygiene remains.
- Route target: finalize if review route decision is `finalize`.
