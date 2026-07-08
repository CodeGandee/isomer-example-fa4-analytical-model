<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/current-board-packet/v1
schema_ref: isomer:deepsci/record-format/schema/evidence/current-board-packet/v1
payload_digest: sha256:2db859b1cbd20cb5b022b87e0fe31deaaf39c1c64a955cb9c0afdfa9ae79878b
-->
# Current Board Packet: FlashAttention-4 B200 Runtime Model Idea Pass

Current board packet for the FlashAttention-4 B200 runtime model idea pass.


```json
{
  "metadata": {
    "consumer": "candidate generation",
    "placeholder": "\u003cCURRENT_BOARD_PACKET\u003e",
    "producer": "isomer-deepsci-idea",
    "skill": "isomer-deepsci-idea"
  },
  "sections": {
    "active_blocker": "none",
    "budget_class": "slow-check",
    "budget_justification": "Validation requires building a Python/SymPy predictor, collecting measured B200 runtime and NCU counters on calibration/validation splits, and fitting bounded white-box constants.",
    "current_mainline": "Extend the FA4 paper roofline with B200-specific white-box terms (occupancy, TMA/L2, precision throughput, exponential emulation) and validate against held-out B200 runtime.",
    "incumbent": {
      "name": "FlashAttention-4 Paper Roofline Model reproduced and extended for NVIDIA B200",
      "record_id": "artifact-ACCEPTED_BASELINE_RECORD-e673ec2be9b4",
      "status": "accepted comparator",
      "what_it_beat": "Naive max(compute, memory) roofline sanity check."
    },
    "latest_decisive_result": "Baseline stage accepted the FA4 paper roofline as comparator with caveats; B200 host spec verified; flash-attention repository at commit 002cce0 available; comparability contract records required calibration constants for HBM bandwidth, L2 efficiency, TMA latency, SMEM bandwidth, Tensor Core MMA throughput, and occupancy limits.",
    "next_decision_scope": "mechanism",
    "stale_routes": [
      "Replace FA4 roofline with a closed-source predictor (cuDNN/Triton) \u2014 rejected in baseline shortlist.",
      "Target consumer GPUs or non-B200 precisions (SageAttention family) \u2014 scope mismatch.",
      "Use measured runtime as a feature \u2014 violates comparability contract."
    ],
    "strongest_negative_evidence": "The FA4 paper roofline intentionally abstracts L2/HBM, TMA latency, occupancy, and TMEM effects; these are exactly the terms that dominate error when tile sizes or precisions change on Blackwell."
  },
  "status": "ready",
  "summary": "Current board packet for the FlashAttention-4 B200 runtime model idea pass.",
  "title": "Current Board Packet: FlashAttention-4 B200 Runtime Model Idea Pass"
}
```