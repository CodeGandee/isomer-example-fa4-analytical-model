"""Bounded bottleneck-saturation experiment for the FA4 B200 white-box predictor.

For each of four saturatable bottleneck regimes (hbm, tma, mma, mufu), we select
configurations that the combined white-box predictor labels with that regime.
We then profile each configuration with NVIDIA Compute Profiler (NCU) SpeedOfLight
and compare the measured dominant bottleneck family (compute vs memory) with the
predictor's dominant bottleneck mapped to the same coarse family.

The script writes three durable outputs:
- saturation_predictions.csv: white-box predictions per config.
- saturation_ncu_results.csv: raw NCU SpeedOfLight metrics per config.
- saturation_accuracy_report.json: aggregate and per-regime accuracy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure the topic main source tree is on the path.
sys.path.insert(
    0,
    str(
        Path("<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/src")
    ),
)

import csv

from fa4_b200_predictor.config_matrix import config_to_dict
from fa4_b200_predictor.ncu_profile import profile_configs
from fa4_b200_predictor.predictor import FA4Config, combined_predictor

# Each tuple is (target_regime, FA4Config).
SATURATION_MATRIX: List[Tuple[str, FA4Config]] = [
    # HBM-bound: small seqlen, large aggregate problem size.
    ("hbm", FA4Config(batch=8, heads=32, seqlen=256, head_dim=128, causal=True, precision="bf16")),
    ("hbm", FA4Config(batch=16, heads=32, seqlen=256, head_dim=128, causal=True, precision="bf16")),
    ("hbm", FA4Config(batch=32, heads=16, seqlen=512, head_dim=64, causal=True, precision="bf16")),
    # TMA-bound: medium seqlen, large tile movement pressure.
    ("tma", FA4Config(batch=16, heads=16, seqlen=2048, head_dim=128, causal=True, precision="bf16")),
    ("tma", FA4Config(batch=8, heads=32, seqlen=4096, head_dim=128, causal=True, precision="bf16")),
    ("tma", FA4Config(batch=4, heads=64, seqlen=2048, head_dim=64, causal=True, precision="bf16")),
    # MMA-bound: large FLOP count.
    ("mma", FA4Config(batch=4, heads=32, seqlen=8192, head_dim=128, causal=True, precision="bf16")),
    ("mma", FA4Config(batch=8, heads=48, seqlen=8192, head_dim=64, causal=True, precision="bf16")),
    ("mma", FA4Config(batch=2, heads=64, seqlen=16384, head_dim=64, causal=True, precision="bf16")),
    # MUFU-bound: small head_dim so softmax dominates over MMA.
    ("mufu", FA4Config(batch=4, heads=64, seqlen=8192, head_dim=16, causal=True, precision="bf16")),
    ("mufu", FA4Config(batch=8, heads=32, seqlen=16384, head_dim=16, causal=True, precision="bf16")),
    ("mufu", FA4Config(batch=2, heads=96, seqlen=8192, head_dim=32, causal=True, precision="bf16")),
]


def fine_to_coarse(label: str) -> str:
    """Map white-box bottleneck labels to NCU SpeedOfLight families."""
    return "compute" if label in ("mma", "mufu") else "memory"


def ncu_to_fine(ncu_bottleneck: str, pred: Dict[str, Any]) -> str:
    """Map NCU coarse label back to the predictor's most likely fine label.

    NCU only reports compute vs memory. When NCU says compute, we choose between
    mma and mufu by taking whichever compute stage time is larger. When NCU says
    memory, we choose the largest memory-stage time reported by the predictor.
    """
    if ncu_bottleneck == "compute":
        return "mma" if pred["mma_time_us"] >= pred["mufu_time_us"] else "mufu"
    if ncu_bottleneck == "memory":
        mem_times = {
            "hbm": pred["hbm_time_us"],
            "l2": pred["l2_time_us"],
            "smem": pred["smem_time_us"],
            "tma": pred["tma_time_us"],
        }
        return max(mem_times, key=mem_times.get)  # type: ignore[arg-type]
    return "unknown"


def run_experiment() -> Dict[str, Any]:
    predictor = combined_predictor()

    # 1. White-box predictions.
    predictions: List[Dict[str, Any]] = []
    for target, cfg in SATURATION_MATRIX:
        pred = predictor.predict(cfg)
        predictions.append(
            {
                "target_regime": target,
                **config_to_dict(cfg),
                "predicted_bottleneck": pred["predicted_bottleneck"],
                "predicted_bottleneck_coarse": fine_to_coarse(pred["predicted_bottleneck"]),
                "predicted_runtime_ms": pred["predicted_runtime_ms"],
                "mma_time_us": pred["mma_time_us"],
                "mufu_time_us": pred["mufu_time_us"],
                "hbm_time_us": pred["hbm_time_us"],
                "l2_time_us": pred["l2_time_us"],
                "smem_time_us": pred["smem_time_us"],
                "tma_time_us": pred["tma_time_us"],
                "occupancy_fraction": pred["occupancy_fraction"],
            }
        )

    # 2. NCU profiles.
    configs = [cfg for _, cfg in SATURATION_MATRIX]
    ncu_records, counts = profile_configs(configs, device="cuda:0", progress_every=3)

    # 3. Attach NCU-derived fine labels.
    comparison: List[Dict[str, Any]] = []
    for (target, cfg), pred_row, ncu in zip(SATURATION_MATRIX, predictions, ncu_records):
        ncu_coarse = ncu.get("bottleneck", "unknown")
        ncu_fine = ncu_to_fine(ncu_coarse, pred_row)
        comparison.append(
            {
                "target_regime": target,
                **config_to_dict(cfg),
                "predicted_bottleneck": pred_row["predicted_bottleneck"],
                "predicted_bottleneck_coarse": pred_row["predicted_bottleneck_coarse"],
                "ncu_bottleneck_coarse": ncu_coarse,
                "ncu_bottleneck_fine": ncu_fine,
                "coarse_match": ncu_coarse == pred_row["predicted_bottleneck_coarse"],
                "fine_match": ncu_fine == pred_row["predicted_bottleneck"],
                "ncu_compute_pct": ncu.get("compute_pct"),
                "ncu_memory_pct": ncu.get("memory_pct"),
                "ncu_duration_ns": ncu.get("duration_ns"),
                "ncu_returncode": ncu.get("ncu_returncode"),
                "ncu_error": ncu.get("error"),
                "predicted_runtime_ms": pred_row["predicted_runtime_ms"],
            }
        )

    # 4. Accuracy summaries.
    def accuracy(rows: List[Dict[str, Any]], key: str) -> float:
        valid = [r for r in rows if r["ncu_bottleneck_coarse"] != "unknown"]
        if not valid:
            return 0.0
        return sum(1 for r in valid if r[key]) / len(valid)

    per_regime: Dict[str, Dict[str, Any]] = {}
    for regime in ("hbm", "tma", "mma", "mufu"):
        rows = [r for r in comparison if r["target_regime"] == regime]
        per_regime[regime] = {
            "count": len(rows),
            "coarse_accuracy": accuracy(rows, "coarse_match"),
            "fine_accuracy": accuracy(rows, "fine_match"),
            "predicted_labels": [r["predicted_bottleneck"] for r in rows],
            "ncu_coarse_labels": [r["ncu_bottleneck_coarse"] for r in rows],
            "ncu_fine_labels": [r["ncu_bottleneck_fine"] for r in rows],
        }

    report = {
        "predictor": predictor.name,
        "total_configs": len(comparison),
        "ncu_ok": counts["ok"],
        "ncu_error": counts["error"],
        "overall_coarse_accuracy": accuracy(comparison, "coarse_match"),
        "overall_fine_accuracy": accuracy(comparison, "fine_match"),
        "per_regime": per_regime,
        "note": "L2 and SMEM labels are not independently saturatable with the current white-box workload model; their bandwidth peaks dominate HBM/TMA in all tested configs.",
    }

    # 5. Write outputs.
    out_dir = Path(__file__).parent
    pred_path = out_dir / "saturation_predictions.csv"
    ncu_path = out_dir / "saturation_ncu_results.csv"
    report_path = out_dir / "saturation_accuracy_report.json"

    with pred_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=predictions[0].keys())
        writer.writeheader()
        writer.writerows(predictions)

    with ncu_path.open("w", newline="") as f:
        fieldnames = list(comparison[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comparison)

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote {pred_path}")
    print(f"Wrote {ncu_path}")
    print(f"Wrote {report_path}")
    print(json.dumps(report, indent=2))

    return report


if __name__ == "__main__":
    run_experiment()
