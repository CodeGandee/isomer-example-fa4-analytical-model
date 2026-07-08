"""Evaluation harness for white-box predictors."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

from fa4_b200_predictor.predictor import (
    FA4Config,
    Predictor,
    baseline_predictor,
    combined_predictor,
    occupancy_only_predictor,
    precision_only_predictor,
    tma_l2_predictor,
)


def evaluate_predictor(
    predictor: Predictor,
    configs: List[FA4Config],
    measurements: List[Dict[str, float]],
) -> Dict[str, float]:
    """Evaluate a predictor on a held-out set."""
    if len(configs) != len(measurements):
        raise ValueError("configs and measurements must have the same length")

    predicted = [predictor.predict(c)["predicted_runtime_ms"] for c in configs]
    measured = [m["measured_runtime_ms"] for m in measurements]
    pred_labels = [predictor.predict(c)["predicted_bottleneck"] for c in configs]
    meas_labels = [m["measured_bottleneck"] for m in measurements]

    errors = []
    within_30 = 0
    for p, m in zip(predicted, measured):
        denom = max(abs(m), 1e-6)
        ape = abs(p - m) / denom * 100.0
        errors.append(ape)
        if ape <= 30.0:
            within_30 += 1

    correct_bottleneck = sum(1 for pl, ml in zip(pred_labels, meas_labels) if pl == ml)

    return {
        "mape": sum(errors) / len(errors) if errors else float("inf"),
        "max_ape": max(errors) if errors else float("inf"),
        "pct_within_30": 100.0 * within_30 / len(errors) if errors else 0.0,
        "bottleneck_accuracy": 100.0 * correct_bottleneck / len(configs) if configs else 0.0,
        "n_configs": len(configs),
    }


def build_ablation_predictors(
    ablation_params: Dict[str, Dict[str, float]],
) -> List[Predictor]:
    """Build calibrated ablation predictors from saved parameters."""
    predictors: List[Predictor] = [baseline_predictor()]

    occ = occupancy_only_predictor()
    occ_p = ablation_params.get("occupancy_only", {})
    occ.mma_efficiency = occ_p.get("mma_efficiency", 1.0)
    occ.mufu_efficiency = occ_p.get("mufu_efficiency", 1.0)
    predictors.append(occ)

    tma_p = ablation_params.get("tma_l2_effective_bw", {})
    tma = tma_l2_predictor(
        hbm_factor=tma_p.get("hbm_factor", 0.75),
        l2_factor=tma_p.get("l2_factor", 0.60),
        tma_factor=tma_p.get("tma_factor", 0.55),
    )
    predictors.append(tma)

    prec = precision_only_predictor()
    prec_p = ablation_params.get("precision_only", {})
    prec.mma_efficiency = prec_p.get("mma_efficiency", 0.9)
    prec.mufu_efficiency = prec_p.get("mufu_efficiency", 0.9)
    predictors.append(prec)

    return predictors


def run_evaluation(
    cal_configs: List[FA4Config],
    cal_measurements: List[Dict[str, float]],
    val_configs: List[FA4Config],
    val_measurements: List[Dict[str, float]],
    combined_params: Dict[str, float],
    ablation_params: Dict[str, Dict[str, float]],
) -> Tuple[Dict[str, Dict[str, float]], Predictor]:
    """Run all predictors and return metrics per model plus the calibrated combined predictor."""
    combined = combined_predictor(
        hbm_factor=combined_params.get("hbm_factor", 0.80),
        l2_factor=combined_params.get("l2_factor", 0.70),
        tma_factor=combined_params.get("tma_factor", 0.65),
        smem_factor=combined_params.get("smem_factor", 0.90),
        mma_efficiency=combined_params.get("mma_efficiency", 0.85),
        mufu_efficiency=combined_params.get("mufu_efficiency", 0.85),
        launch_overhead_us=combined_params.get("launch_overhead_us", 2.0),
    )

    results: Dict[str, Dict[str, float]] = {}
    for pred in build_ablation_predictors(ablation_params):
        results[pred.name] = evaluate_predictor(pred, val_configs, val_measurements)

    results["combined"] = evaluate_predictor(combined, val_configs, val_measurements)

    # Cal-set sanity check for overfitting signal.
    results["combined_calibration"] = evaluate_predictor(combined, cal_configs, cal_measurements)

    return results, combined


def save_evaluation(
    results: Dict[str, Dict[str, float]],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "validation_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    with (out_dir / "validation_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "model",
                "mape",
                "max_ape",
                "pct_within_30",
                "bottleneck_accuracy",
                "n_configs",
            ],
        )
        writer.writeheader()
        for model, metrics in results.items():
            row = {"model": model, **metrics}
            writer.writerow(row)


def save_predictions(
    predictor: Predictor,
    configs: List[FA4Config],
    measurements: List[Dict[str, float]],
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for cfg, meas in zip(configs, measurements):
        pred = predictor.predict(cfg)
        rows.append(
            {
                "batch": cfg.batch,
                "heads": cfg.heads,
                "seqlen": cfg.seqlen,
                "head_dim": cfg.head_dim,
                "causal": cfg.causal,
                "precision": cfg.normalized_precision,
                "predicted_runtime_ms": pred["predicted_runtime_ms"],
                "measured_runtime_ms": meas["measured_runtime_ms"],
                "predicted_bottleneck": pred["predicted_bottleneck"],
                "measured_bottleneck": meas["measured_bottleneck"],
            }
        )
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "batch",
                "heads",
                "seqlen",
                "head_dim",
                "causal",
                "precision",
                "predicted_runtime_ms",
                "measured_runtime_ms",
                "predicted_bottleneck",
                "measured_bottleneck",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
