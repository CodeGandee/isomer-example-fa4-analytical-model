<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/evidence/scout-context-brief/v1
schema_ref: isomer:deepsci/record-format/schema/evidence/scout-context-brief/v1
payload_digest: sha256:4e983779b87627b4a27ae746e6c3428782b7e18a79533713494c983e001539ef
-->
# Scout Context Brief

Reconstructed research frame for the Flash Attention 4 white-box runtime model on NVIDIA B200.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-scout, isomer-deepsci-baseline, isomer-deepsci-idea, isomer-deepsci-decision",
    "placeholder": "\u003cSCOUT_CONTEXT_BRIEF\u003e",
    "producer": "isomer-deepsci-scout from user context, Workspace Runtime records, Artifacts, Findings, Evidence Items, and Decision Records.",
    "skill": "isomer-deepsci-scout"
  },
  "sections": {
    "blockers": "None for routing to isomer-deepsci-baseline.",
    "comparator_status": "No existing white-box FA4 runtime predictor found. FA4 paper roofline analysis is the seed comparator.",
    "evidence": [
      "intent/src/topic-overview.md",
      "intent/src/topic-env-gate.md",
      "actors/operator/host-b200-spec.md",
      "repos/extern/flash-attention",
      "arXiv 2603.05451v1",
      "arXiv 2512.02189v1",
      "arXiv 2605.04178v1"
    ],
    "research_topic": "flash-attention-4-whitebox-runtime-model",
    "scope": {
      "excluded": [
        "backward pass",
        "multi-GPU/tensor-parallel"
      ],
      "gpu_target": "NVIDIA B200, single GPU",
      "inputs": [
        "batch size",
        "heads",
        "sequence length",
        "head dimension",
        "mask mode",
        "precision"
      ],
      "precisions": [
        "BF16",
        "FP16",
        "FP8",
        "FP4"
      ]
    },
    "task_frame": "Build a white-box, hardware-grounded predictor of Flash Attention 4 forward-pass kernel runtime in milliseconds from input configuration, without executing the queried kernel."
  },
  "status": "ready",
  "summary": "Reconstructed research frame for the Flash Attention 4 white-box runtime model on NVIDIA B200.",
  "title": "Scout Context Brief"
}
```