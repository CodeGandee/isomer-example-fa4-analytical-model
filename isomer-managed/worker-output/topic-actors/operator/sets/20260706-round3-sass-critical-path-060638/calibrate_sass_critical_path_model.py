"""Calibrate and validate the SASS-level instruction critical-path FA4 model."""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.optimize import minimize

# Paths -----------------------------------------------------------------------
OPERATION_DIR = Path(__file__).resolve().parent
REPO_SRC = (
    OPERATION_DIR.parents[7]
    / "repos"
    / "topic-main"
    / "src"
)
sys.path.insert(0, str(REPO_SRC))

from sass_critical_path_model import (  # type: ignore
    B200SASSCriticalPathModel,
    B200SASSCriticalPathModelSpec,
    FA4WorkloadDesc,
)
from fa4_b200_predictor.improved_predictor import (  # type: ignore
    ImprovedPredictor,
    calibrate_improved,
)
from fa4_b200_predictor.predictor import FA4Config, baseline_predictor  # type: ignore


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def config_to_workload(cfg: FA4Config) -> FA4WorkloadDesc:
    return FA4WorkloadDesc(
        batch=cfg.batch,
        heads=cfg.heads,
        seqlen=cfg.seqlen,
        head_dim=cfg.head_dim,
        causal=cfg.causal,
        precision=cfg.precision,
    )


def config_to_dict(cfg: FA4Config) -> Dict[str, Any]:
    return {
        "batch": cfg.batch,
        "heads": cfg.heads,
        "seqlen": cfg.seqlen,
        "head_dim": cfg.head_dim,
        "causal": cfg.causal,
        "precision": cfg.normalized_precision,
    }


def mape(predicted: np.ndarray, measured: np.ndarray) -> float:
    mask = measured > 0
    return float(np.mean(np.abs((predicted[mask] - measured[mask]) / measured[mask])) * 100.0)


# -----------------------------------------------------------------------------
# Calibration
# -----------------------------------------------------------------------------


def make_spec_from_params(x: np.ndarray) -> B200SASSCriticalPathModelSpec:
    (
        tma_eff,
        tc_eff,
        sfu_eff,
        fp_eff,
        slack,
        overlap,
        launch_us,
    ) = x
    base = B200SASSCriticalPathModelSpec()
    return replace(
        base,
        tma_efficiency=float(tma_eff),
        tc_efficiency=float(tc_eff),
        sfu_efficiency=float(sfu_eff),
        fp_efficiency=float(fp_eff),
        dependency_slack_factor=float(slack),
        stage_overlap_factor=float(overlap),
        launch_overhead_us=float(launch_us),
    )


def objective(
    x: np.ndarray,
    cal_configs: List[FA4Config],
    cal_measured: np.ndarray,
) -> float:
    spec = make_spec_from_params(x)
    model = B200SASSCriticalPathModel(spec)
    preds = np.array(
        [
            model.predict(config_to_workload(cfg))["predicted_runtime_ms"]
            for cfg in cal_configs
        ]
    )
    return mape(preds, cal_measured)


def fit_sass_critical_path_model(
    cal_configs: List[FA4Config],
    cal_measured: np.ndarray,
) -> Tuple[B200SASSCriticalPathModelSpec, Dict[str, Any]]:
    x0 = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 0.85, 2.0], dtype=float)
    bounds = [
        (0.20, 3.00),  # tma_efficiency
        (0.20, 3.00),  # tc_efficiency
        (0.20, 3.00),  # sfu_efficiency
        (0.20, 3.00),  # fp_efficiency
        (0.50, 3.00),  # dependency_slack_factor
        (0.00, 1.00),  # stage_overlap_factor
        (0.00, 50.0),  # launch_overhead_us
    ]

    result = minimize(
        objective,
        x0,
        args=(cal_configs, cal_measured),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 300},
    )
    spec = make_spec_from_params(result.x)
    metrics = {
        "mape_percent": result.fun,
        "success": result.success,
        "params": result.x.tolist(),
        "param_names": [
            "tma_efficiency",
            "tc_efficiency",
            "sfu_efficiency",
            "fp_efficiency",
            "dependency_slack_factor",
            "stage_overlap_factor",
            "launch_overhead_us",
        ],
    }
    return spec, metrics


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def load_measurements(
    path: Path,
) -> Tuple[List[FA4Config], np.ndarray, List[FA4Config], np.ndarray]:
    cal_configs: List[FA4Config] = []
    cal_measured: List[float] = []
    val_configs: List[FA4Config] = []
    val_measured: List[float] = []

    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status", "ok") != "ok":
                continue
            cfg = FA4Config(
                batch=int(row["batch"]),
                heads=int(row["heads"]),
                seqlen=int(row["seqlen"]),
                head_dim=int(row["head_dim"]),
                causal=row["causal"].lower() in ("true", "1", "yes"),
                precision=row["precision"],
            )
            measured = float(row["measured_runtime_ms"])
            split = row.get("split", "cal")
            if split == "cal":
                cal_configs.append(cfg)
                cal_measured.append(measured)
            else:
                val_configs.append(cfg)
                val_measured.append(measured)

    return cal_configs, np.array(cal_measured), val_configs, np.array(val_measured)


def main() -> None:
    out_dir = OPERATION_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    meas_path = OPERATION_DIR.parent / "20260705-inner-gpu-calibration-faddf4" / "measurements.csv"
    cal_configs, cal_measured, val_configs, val_measured = load_measurements(meas_path)
    print(f"Loaded {len(cal_configs)} calibration and {len(val_configs)} validation configs")

    if len(cal_configs) < 6:
        raise RuntimeError(f"Too few calibration measurements: {len(cal_configs)}")

    spec, cal_metrics = fit_sass_critical_path_model(cal_configs, cal_measured)
    model = B200SASSCriticalPathModel(spec)

    sass_cal_preds = np.array(
        [model.predict(config_to_workload(cfg))["predicted_runtime_ms"] for cfg in cal_configs]
    )
    sass_val_preds = np.array(
        [model.predict(config_to_workload(cfg))["predicted_runtime_ms"] for cfg in val_configs]
    )
    sass_cal_mape = mape(sass_cal_preds, cal_measured)
    sass_val_mape = mape(sass_val_preds, val_measured)

    base = baseline_predictor()
    base_val_mape = mape(
        np.array([base.predict(cfg)["predicted_runtime_ms"] for cfg in val_configs]),
        val_measured,
    )

    improved, _ = calibrate_improved(cal_configs, cal_measured.tolist())
    imp_val_mape = mape(
        np.array([improved.predict(cfg)["predicted_runtime_ms"] for cfg in val_configs]),
        val_measured,
    )

    with (out_dir / "predictions.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "split",
                "batch",
                "heads",
                "seqlen",
                "head_dim",
                "causal",
                "precision",
                "measured_runtime_ms",
                "sass_predicted_ms",
                "baseline_predicted_ms",
                "improved_predicted_ms",
            ],
        )
        writer.writeheader()
        for split, configs, measured, sass_preds in [
            ("cal", cal_configs, cal_measured, sass_cal_preds),
            ("val", val_configs, val_measured, sass_val_preds),
        ]:
            for cfg, m, sp in zip(configs, measured, sass_preds):
                writer.writerow(
                    {
                        "split": split,
                        **config_to_dict(cfg),
                        "measured_runtime_ms": m,
                        "sass_predicted_ms": sp,
                        "baseline_predicted_ms": base.predict(cfg)["predicted_runtime_ms"],
                        "improved_predicted_ms": improved.predict(cfg)["predicted_runtime_ms"],
                    }
                )

    spec_dict: Dict[str, Any] = {
        "tma_efficiency": spec.tma_efficiency,
        "tc_efficiency": spec.tc_efficiency,
        "sfu_efficiency": spec.sfu_efficiency,
        "fp_efficiency": spec.fp_efficiency,
        "dependency_slack_factor": spec.dependency_slack_factor,
        "stage_overlap_factor": spec.stage_overlap_factor,
        "launch_overhead_us": spec.launch_overhead_us,
        "num_sms": spec.num_sms,
        "partitions_per_sm": spec.partitions_per_sm,
        "peak_sm_clock_mhz": spec.peak_sm_clock_mhz,
    }
    with (out_dir / "sass_model_spec.json").open("w") as f:
        json.dump(spec_dict, f, indent=2)

    summary = {
        "sass_calibration_mape_percent": round(sass_cal_mape, 2),
        "sass_validation_mape_percent": round(sass_val_mape, 2),
        "baseline_validation_mape_percent": round(base_val_mape, 2),
        "improved_validation_mape_percent": round(imp_val_mape, 2),
        "calibration_count": len(cal_configs),
        "validation_count": len(val_configs),
        "calibration_success": cal_metrics["success"],
        "fit_params": dict(zip(cal_metrics["param_names"], cal_metrics["params"])),
    }

    with (out_dir / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== Summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
