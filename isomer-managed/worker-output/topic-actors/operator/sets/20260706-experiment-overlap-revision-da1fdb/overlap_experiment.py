"""Calibrate and validate the overlap-aware FA4 B200 predictor.

Steps:
1. Define an expanded 24-config saturation matrix.
2. Use the original 12 configs' known NCU labels to calibrate overlap_frac.
3. Profile the full 24-config matrix with NCU SpeedOfLight.
4. Report predictor accuracy vs NCU for the best overlap_frac and the baseline.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[8] / "repos" / "topic-main" / "src"),
)

from fa4_b200_predictor.config_matrix import config_to_dict
from fa4_b200_predictor.ncu_profile import profile_configs
from fa4_b200_predictor.predictor import FA4Config, combined_predictor

# Original 12 configs (used for calibration).
ORIGINAL_MATRIX: List[Tuple[str, FA4Config]] = [
    ("hbm", FA4Config(batch=8, heads=32, seqlen=256, head_dim=128, causal=True, precision="bf16")),
    ("hbm", FA4Config(batch=16, heads=32, seqlen=256, head_dim=128, causal=True, precision="bf16")),
    ("hbm", FA4Config(batch=32, heads=16, seqlen=512, head_dim=64, causal=True, precision="bf16")),
    ("tma", FA4Config(batch=16, heads=16, seqlen=2048, head_dim=128, causal=True, precision="bf16")),
    ("tma", FA4Config(batch=8, heads=32, seqlen=4096, head_dim=128, causal=True, precision="bf16")),
    ("tma", FA4Config(batch=4, heads=64, seqlen=2048, head_dim=64, causal=True, precision="bf16")),
    ("mma", FA4Config(batch=4, heads=32, seqlen=8192, head_dim=128, causal=True, precision="bf16")),
    ("mma", FA4Config(batch=8, heads=48, seqlen=8192, head_dim=64, causal=True, precision="bf16")),
    ("mma", FA4Config(batch=2, heads=64, seqlen=16384, head_dim=64, causal=True, precision="bf16")),
    ("mufu", FA4Config(batch=4, heads=64, seqlen=8192, head_dim=16, causal=True, precision="bf16")),
    ("mufu", FA4Config(batch=8, heads=32, seqlen=16384, head_dim=16, causal=True, precision="bf16")),
    ("mufu", FA4Config(batch=2, heads=96, seqlen=8192, head_dim=32, causal=True, precision="bf16")),
]

# Expanded matrix adds 12 new configs.
EXPANDED_MATRIX: List[Tuple[str, FA4Config]] = ORIGINAL_MATRIX + [
    # Additional HBM-bound configs.
    ("hbm", FA4Config(batch=4, heads=64, seqlen=256, head_dim=128, causal=True, precision="bf16")),
    ("hbm", FA4Config(batch=8, heads=16, seqlen=512, head_dim=256, causal=True, precision="bf16")),
    ("hbm", FA4Config(batch=16, heads=16, seqlen=512, head_dim=128, causal=True, precision="bf16")),
    ("hbm", FA4Config(batch=32, heads=8, seqlen=1024, head_dim=64, causal=True, precision="bf16")),
    ("hbm", FA4Config(batch=64, heads=8, seqlen=256, head_dim=128, causal=True, precision="bf16")),
    # Additional TMA-bound configs.
    ("tma", FA4Config(batch=8, heads=16, seqlen=4096, head_dim=128, causal=True, precision="bf16")),
    ("tma", FA4Config(batch=4, heads=32, seqlen=2048, head_dim=128, causal=True, precision="bf16")),
    ("tma", FA4Config(batch=2, heads=64, seqlen=4096, head_dim=64, causal=True, precision="bf16")),
    # Additional MMA-bound configs.
    ("mma", FA4Config(batch=4, heads=64, seqlen=8192, head_dim=64, causal=True, precision="bf16")),
    ("mma", FA4Config(batch=2, heads=32, seqlen=16384, head_dim=128, causal=True, precision="bf16")),
    ("mma", FA4Config(batch=4, heads=48, seqlen=8192, head_dim=128, causal=True, precision="bf16")),
    # Additional MUFU-bound config.
    ("mufu", FA4Config(batch=4, heads=48, seqlen=16384, head_dim=16, causal=True, precision="bf16")),
]


def cfg_key(cfg: FA4Config) -> Tuple[int, int, int, int]:
    return (cfg.batch, cfg.heads, cfg.seqlen, cfg.head_dim)


def coarse(label: str) -> str:
    return "compute" if label in ("mma", "mufu") else "memory"


def ncu_to_fine(ncu_bottleneck: str, pred: Dict[str, Any]) -> str:
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


def calibrate_overlap(original_ncu_labels: Dict[Tuple[int, int, int, int], str]) -> Tuple[float, List[Dict[str, Any]]]:
    overlap_fracs = [0.0, 0.25, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9]
    best_frac = 0.0
    best_acc = 0.0
    rows: List[Dict[str, Any]] = []

    for frac in overlap_fracs:
        predictor = combined_predictor(overlap_frac=frac)
        correct = 0
        total = 0
        per_regime: Dict[str, Dict[str, int]] = {}
        for target, cfg in ORIGINAL_MATRIX:
            pred = predictor.predict(cfg)
            pred_coarse = coarse(pred["predicted_bottleneck"])
            ncu_coarse = original_ncu_labels[cfg_key(cfg)]
            match = pred_coarse == ncu_coarse
            total += 1
            if match:
                correct += 1
            per_regime.setdefault(target, {"count": 0, "correct": 0})
            per_regime[target]["count"] += 1
            if match:
                per_regime[target]["correct"] += 1

        acc = correct / total
        rows.append(
            {
                "overlap_frac": frac,
                "coarse_accuracy": acc,
                "correct": correct,
                "total": total,
                "hbm_accuracy": per_regime["hbm"]["correct"] / per_regime["hbm"]["count"],
                "tma_accuracy": per_regime["tma"]["correct"] / per_regime["tma"]["count"],
                "mma_accuracy": per_regime["mma"]["correct"] / per_regime["mma"]["count"],
                "mufu_accuracy": per_regime["mufu"]["correct"] / per_regime["mufu"]["count"],
            }
        )
        if acc > best_acc:
            best_acc = acc
            best_frac = frac

    return best_frac, rows


def main() -> None:
    out_dir = Path(__file__).parent

    # Known NCU labels for original 12 configs (from parent experiment).
    original_ncu_labels: Dict[Tuple[int, int, int, int], str] = {
        (8, 32, 256, 128): "memory",
        (16, 32, 256, 128): "memory",
        (32, 16, 512, 64): "compute",
        (16, 16, 2048, 128): "compute",
        (8, 32, 4096, 128): "compute",
        (4, 64, 2048, 64): "compute",
        (4, 32, 8192, 128): "compute",
        (8, 48, 8192, 64): "compute",
        (2, 64, 16384, 64): "compute",
        (4, 64, 8192, 16): "compute",
        (8, 32, 16384, 16): "compute",
        (2, 96, 8192, 32): "compute",
    }

    # Step 1: Calibrate overlap_frac on original 12 configs.
    best_overlap, calibration_rows = calibrate_overlap(original_ncu_labels)

    # Step 2: Profile expanded 24-config matrix with NCU.
    expanded_configs = [cfg for _, cfg in EXPANDED_MATRIX]
    ncu_records, counts = profile_configs(expanded_configs, device="cuda:0", progress_every=4)

    # Step 3: Evaluate baseline and best overlap predictor on expanded matrix.
    baseline = combined_predictor(overlap_frac=0.0)
    best_predictor = combined_predictor(overlap_frac=best_overlap)

    comparison_rows: List[Dict[str, Any]] = []
    baseline_correct = 0
    best_correct = 0
    total = 0
    per_regime_baseline: Dict[str, Dict[str, int]] = {}
    per_regime_best: Dict[str, Dict[str, int]] = {}

    for (target, cfg), ncu in zip(EXPANDED_MATRIX, ncu_records):
        ncu_coarse = ncu.get("bottleneck", "unknown")
        if ncu_coarse == "unknown":
            continue

        base_pred = baseline.predict(cfg)
        best_pred = best_predictor.predict(cfg)
        base_coarse = coarse(base_pred["predicted_bottleneck"])
        best_coarse = coarse(best_pred["predicted_bottleneck"])
        base_match = base_coarse == ncu_coarse
        best_match = best_coarse == ncu_coarse

        total += 1
        if base_match:
            baseline_correct += 1
        if best_match:
            best_correct += 1

        per_regime_baseline.setdefault(target, {"count": 0, "correct": 0})
        per_regime_best.setdefault(target, {"count": 0, "correct": 0})
        per_regime_baseline[target]["count"] += 1
        per_regime_best[target]["count"] += 1
        if base_match:
            per_regime_baseline[target]["correct"] += 1
        if best_match:
            per_regime_best[target]["correct"] += 1

        comparison_rows.append(
            {
                "target_regime": target,
                **config_to_dict(cfg),
                "ncu_bottleneck_coarse": ncu_coarse,
                "ncu_bottleneck_fine": ncu_to_fine(ncu_coarse, best_pred),
                "baseline_predicted_bottleneck": base_pred["predicted_bottleneck"],
                "baseline_predicted_coarse": base_coarse,
                "best_predicted_bottleneck": best_pred["predicted_bottleneck"],
                "best_predicted_coarse": best_coarse,
                "baseline_match": base_match,
                "best_match": best_match,
                "ncu_compute_pct": ncu.get("compute_pct"),
                "ncu_memory_pct": ncu.get("memory_pct"),
                "ncu_duration_ns": ncu.get("duration_ns"),
            }
        )

    def regime_acc(d: Dict[str, Dict[str, int]], regime: str) -> float:
        r = d.get(regime, {"count": 0, "correct": 0})
        return r["correct"] / r["count"] if r["count"] else 0.0

    report = {
        "best_overlap_frac": best_overlap,
        "expanded_total_configs": total,
        "ncu_ok": counts["ok"],
        "ncu_error": counts["error"],
        "baseline_coarse_accuracy": baseline_correct / total if total else 0.0,
        "best_coarse_accuracy": best_correct / total if total else 0.0,
        "per_regime_baseline_accuracy": {
            regime: regime_acc(per_regime_baseline, regime) for regime in ("hbm", "tma", "mma", "mufu")
        },
        "per_regime_best_accuracy": {
            regime: regime_acc(per_regime_best, regime) for regime in ("hbm", "tma", "mma", "mufu")
        },
    }

    # Write outputs.
    cal_path = out_dir / "overlap_calibration.csv"
    ncu_path = out_dir / "overlap_ncu_results.csv"
    report_path = out_dir / "overlap_accuracy_report.json"

    with cal_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=calibration_rows[0].keys())
        writer.writeheader()
        writer.writerows(calibration_rows)

    with ncu_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=comparison_rows[0].keys())
        writer.writeheader()
        writer.writerows(comparison_rows)

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote {cal_path}")
    print(f"Wrote {ncu_path}")
    print(f"Wrote {report_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
