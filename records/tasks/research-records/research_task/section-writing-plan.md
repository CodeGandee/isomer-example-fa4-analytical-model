<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/paper/writing-plan/v1
schema_ref: isomer:deepsci/record-format/schema/paper/writing-plan/v1
payload_digest: sha256:7469d2b639994da0e0817fc4c5763640c4f7fd551194aa58a0da72386d74d86d
-->
# Section Writing Plan: White-Box FA4 B200 Predictor

Section jobs, source inputs, claim limits, and display requirements for the real-hardware paper draft.


```json
{
  "route_decision": "write",
  "sections": {
    "abstract": {
      "claim_limits": [
        "no fp4 claims",
        "note compute-bound NCU caveat"
      ],
      "displays": [],
      "job": "Summarize problem, method, real-hardware result, and limitation in 150 words.",
      "source_inputs": [
        "analysis summaries",
        "final metrics"
      ]
    },
    "conclusion": {
      "claim_limits": [
        "no unsupported generalisation"
      ],
      "displays": [],
      "job": "Summarize contributions and next steps.",
      "source_inputs": [
        "all above"
      ]
    },
    "experiments": {
      "claim_limits": [
        "real protocol only",
        "fp4 unsupported"
      ],
      "displays": [],
      "job": "Describe matrix, real measurement protocol, NCU subset, metrics.",
      "source_inputs": [
        "run_improved_experiment.py",
        "run_bottleneck_refinement_experiment.py"
      ]
    },
    "introduction": {
      "claim_limits": [
        "distinguish emulator preliminary from silicon final"
      ],
      "displays": [],
      "job": "Motivate white-box prediction; explain the emulator-to-silicon correction arc; state contributions.",
      "source_inputs": [
        "previous revised draft",
        "real-hardware narrative"
      ]
    },
    "limitations": {
      "claim_limits": [
        "explicit caveats only"
      ],
      "displays": [],
      "job": "List fp4, compute-only NCU labels, synthetic matrix, driver-specific calibration.",
      "source_inputs": [
        "analysis summaries"
      ]
    },
    "method": {
      "claim_limits": [
        "bounded factors only",
        "report final calibrated params"
      ],
      "displays": [
        "Table 1",
        "Figure 3"
      ],
      "job": "Describe workload quantities, baseline roofline, bounded corrections, launch overhead, NCU bottleneck calibration.",
      "source_inputs": [
        "improved_predictor.py",
        "ncu_profile.py",
        "calibration_params.json"
      ]
    },
    "related_work": {
      "claim_limits": [
        "cite only verified references"
      ],
      "displays": [],
      "job": "Position against FlashAttention family, GPU roofline models, Blackwell work.",
      "source_inputs": [
        "previous draft references"
      ]
    },
    "results": {
      "claim_limits": [
        "all real B200",
        "include refuted pass as negative result"
      ],
      "displays": [
        "Table 2",
        "Table 3",
        "Figure 1",
        "Figure 2"
      ],
      "job": "Report emulator preliminary, refuted first pass, improved pass, refined pass, per-precision and worst-case analysis.",
      "source_inputs": [
        "metrics.json files",
        "refined predictions CSVs"
      ]
    }
  },
  "status": "ready",
  "summary": "Section jobs, source inputs, claim limits, and display requirements for the real-hardware paper draft.",
  "title": "Section Writing Plan: White-Box FA4 B200 Predictor"
}
```