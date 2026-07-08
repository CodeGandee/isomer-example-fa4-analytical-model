"""Three focused analysis slices for the FA4 B200 bottleneck-saturation result.

Slice A: diagnostic ratios of predicted memory/compute stage times.
Slice B: TMA/MMA overlap counterfactual.
Slice C: tma_factor x mma_efficiency calibration sweep.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(
    0,
    str(
        Path("<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/src")
    ),
)

from fa4_b200_predictor.config_matrix import config_to_dict
from fa4_b200_predictor.predictor import FA4Config, Predictor, combined_predictor

SATURATION_MATRIX: List[Tuple[str, FA4Config]] = [
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

# Observed NCU coarse labels from parent experiment (compute vs memory).
NCU_COARSE = {
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


def cfg_key(cfg: FA4Config) -> Tuple[int, int, int, int]:
    return (cfg.batch, cfg.heads, cfg.seqlen, cfg.head_dim)


def run_slice_a() -> List[Dict[str, Any]]:
    predictor = combined_predictor()
    rows: List[Dict[str, Any]] = []
    for target, cfg in SATURATION_MATRIX:
        pred = predictor.predict(cfg)
        compute_time = max(pred["mma_time_us"], pred["mufu_time_us"])
        mem_time = max(pred["hbm_time_us"], pred["l2_time_us"], pred["smem_time_us"], pred["tma_time_us"])
        rows.append(
            {
                "target_regime": target,
                **config_to_dict(cfg),
                "predicted_bottleneck": pred["predicted_bottleneck"],
                "ncu_coarse": NCU_COARSE[cfg_key(cfg)],
                "mma_time_us": pred["mma_time_us"],
                "mufu_time_us": pred["mufu_time_us"],
                "tma_time_us": pred["tma_time_us"],
                "hbm_time_us": pred["hbm_time_us"],
                "l2_time_us": pred["l2_time_us"],
                "smem_time_us": pred["smem_time_us"],
                "tma_over_mma": pred["tma_time_us"] / max(pred["mma_time_us"], 1e-9),
                "tma_over_mufu": pred["tma_time_us"] / max(pred["mufu_time_us"], 1e-9),
                "memory_over_compute": mem_time / max(compute_time, 1e-9),
            }
        )
    return rows


def label_from_times(  # noqa: PLR0913
    hbm_time_us: float,
    l2_time_us: float,
    smem_time_us: float,
    tma_time_us: float,
    mma_time_us: float,
    mufu_time_us: float,
) -> str:
    times = {
        "hbm": hbm_time_us,
        "l2": l2_time_us,
        "smem": smem_time_us,
        "tma": tma_time_us,
        "mma": mma_time_us,
        "mufu": mufu_time_us,
    }
    return max(times, key=times.get)  # type: ignore[arg-type]


def coarse(label: str) -> str:
    return "compute" if label in ("mma", "mufu") else "memory"


def run_slice_b() -> List[Dict[str, Any]]:
    predictor = combined_predictor()
    overlap_fracs = [0.0, 0.25, 0.50, 0.75]
    rows: List[Dict[str, Any]] = []

    for overlap_frac in overlap_fracs:
        correct = 0
        total = 0
        per_regime: Dict[str, Dict[str, Any]] = {}
        for target, cfg in SATURATION_MATRIX:
            pred = predictor.predict(cfg)
            compute_time = max(pred["mma_time_us"], pred["mufu_time_us"])
            mem_time = max(pred["hbm_time_us"], pred["l2_time_us"], pred["smem_time_us"], pred["tma_time_us"])
            # Overlap model: memory traffic can hide behind compute up to overlap_frac.
            effective_mem_time = mem_time * (1.0 - overlap_frac)
            effective_total = max(compute_time, effective_mem_time)
            # Label by the effective dominant stage.
            label = label_from_times(
                pred["hbm_time_us"] * (1.0 - overlap_frac),
                pred["l2_time_us"] * (1.0 - overlap_frac),
                pred["smem_time_us"] * (1.0 - overlap_frac),
                pred["tma_time_us"] * (1.0 - overlap_frac),
                pred["mma_time_us"],
                pred["mufu_time_us"],
            )
            pred_coarse = coarse(label)
            ncu_coarse = NCU_COARSE[cfg_key(cfg)]
            match = pred_coarse == ncu_coarse
            total += 1
            if match:
                correct += 1
            per_regime.setdefault(target, {"count": 0, "correct": 0})
            per_regime[target]["count"] += 1
            if match:
                per_regime[target]["correct"] += 1

        rows.append(
            {
                "overlap_frac": overlap_frac,
                "coarse_accuracy": correct / total,
                "correct": correct,
                "total": total,
                "hbm_accuracy": per_regime["hbm"]["correct"] / per_regime["hbm"]["count"],
                "tma_accuracy": per_regime["tma"]["correct"] / per_regime["tma"]["count"],
                "mma_accuracy": per_regime["mma"]["correct"] / per_regime["mma"]["count"],
                "mufu_accuracy": per_regime["mufu"]["correct"] / per_regime["mufu"]["count"],
            }
        )
    return rows


def predictor_with_factors(tma_factor: float, mma_efficiency: float) -> Predictor:
    return Predictor(
        name=f"tma_{tma_factor}_mma_{mma_efficiency}",
        hbm_factor=0.80,
        l2_factor=0.70,
        smem_factor=0.90,
        tma_factor=tma_factor,
        occupancy_factor_override=None,
        mma_efficiency=mma_efficiency,
        mufu_efficiency=0.85,
        launch_overhead_us=2.0,
    )


def run_slice_c() -> List[Dict[str, Any]]:
    tma_factors = [0.20, 0.35, 0.50, 0.65, 0.80, 1.00]
    mma_effs = [0.50, 0.65, 0.75, 0.85, 0.95, 1.00]
    rows: List[Dict[str, Any]] = []

    for tma_factor in tma_factors:
        for mma_eff in mma_effs:
            predictor = predictor_with_factors(tma_factor, mma_eff)
            correct = 0
            total = 0
            for target, cfg in SATURATION_MATRIX:
                pred = predictor.predict(cfg)
                pred_coarse = coarse(pred["predicted_bottleneck"])
                ncu_coarse = NCU_COARSE[cfg_key(cfg)]
                match = pred_coarse == ncu_coarse
                total += 1
                if match:
                    correct += 1
            rows.append(
                {
                    "tma_factor": tma_factor,
                    "mma_efficiency": mma_eff,
                    "coarse_accuracy": correct / total,
                    "correct": correct,
                    "total": total,
                }
            )
    return rows


def main() -> None:
    out_dir = Path(__file__).parent

    slice_a = run_slice_a()
    slice_b = run_slice_b()
    slice_c = run_slice_c()

    a_path = out_dir / "slice_a_diagnostic_ratios.csv"
    b_path = out_dir / "slice_b_overlap_counterfactual.csv"
    c_path = out_dir / "slice_c_factor_sweep.csv"

    with a_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=slice_a[0].keys())
        writer.writeheader()
        writer.writerows(slice_a)

    with b_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=slice_b[0].keys())
        writer.writeheader()
        writer.writerows(slice_b)

    with c_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=slice_c[0].keys())
        writer.writeheader()
        writer.writerows(slice_c)

    best_c = max(slice_c, key=lambda r: r["coarse_accuracy"])
    summary = {
        "slice_a_findings": {
            "tma_configs_mean_tma_over_mma": sum(
                r["tma_over_mma"] for r in slice_a if r["target_regime"] == "tma"
            )
            / 3,
            "other_configs_mean_tma_over_mma": sum(
                r["tma_over_mma"] for r in slice_a if r["target_regime"] != "tma"
            )
            / 9,
        },
        "slice_b_findings": {
            "best_overlap_frac": max(slice_b, key=lambda r: r["coarse_accuracy"])["overlap_frac"],
            "best_coarse_accuracy": max(slice_b, key=lambda r: r["coarse_accuracy"])["coarse_accuracy"],
            "full_table": slice_b,
        },
        "slice_c_findings": {
            "best_tma_factor": best_c["tma_factor"],
            "best_mma_efficiency": best_c["mma_efficiency"],
            "best_coarse_accuracy": best_c["coarse_accuracy"],
        },
    }

    summary_path = out_dir / "analysis_slices_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote {a_path}")
    print(f"Wrote {b_path}")
    print(f"Wrote {c_path}")
    print(f"Wrote {summary_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
