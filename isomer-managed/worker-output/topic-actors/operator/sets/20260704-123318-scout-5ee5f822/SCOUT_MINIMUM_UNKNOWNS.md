# Scout Minimum Unknowns

These unresolved questions can change the shape of the baseline model or the validation plan. They are not blockers for entering `isomer-deepsci-baseline`, but they must be answered during that stage.

1. **B200 sustained HBM bandwidth and L2 transaction parameters**. The host spec captures peak clocks but not the sustained HBM bandwidth or effective L2 line size/transaction count under FA4-style access patterns. The baseline model must either measure these or adopt a conservative value and document the assumption.

2. **FA4 default tile sizes, warpgroup assignment, and 2-CTA mode per precision**. The FlashAttention-4 paper describes the forward pipeline at a high level, but the exact tile dimensions (M, N), number of warpgroups, and whether 2-CTA MMA is used for each precision are needed to compute shared-memory traffic and MMA instruction counts.

3. **TMA latency and TMEM allocation constraints per SM**. TMA load/store latency and the TMEM capacity required for the ping-pong pipeline affect occupancy and the latency-hiding model. These are not stated in the host spec or paper.

4. **Fraction of exponentials emulated via polynomial and the conditional-rescaling threshold τ**. The paper reports partial emulation (10–25%) and τ = log₂(256) = 8.0, but the actual values may vary by precision/tile. The baseline model must either adopt the paper's values or calibrate them.

5. **Primary accuracy threshold and validation split**. The topic intent requires a measured-vs-predicted comparison but does not fix an error tolerance or a held-out configuration set. The baseline stage must propose a numeric contract and a split, and the operator must approve or record a waiver.

## Route Impact

- If the operator accepts a proposed accuracy threshold and split, baseline work proceeds normally.
- If no FA4 tile or scheduling details can be sourced, the stage may need a short decision gate or a return to scout for repository archaeology.
- None of these unknowns justify stopping the empirical pass now.
