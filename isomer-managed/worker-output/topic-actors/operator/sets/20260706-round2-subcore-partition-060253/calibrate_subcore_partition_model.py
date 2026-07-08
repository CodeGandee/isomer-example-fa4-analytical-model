"""Calibrate and validate the sub-core partition scheduling FA4 model on real B200 measurements.

The script reads the measurements CSV produced by the inner-GPU calibration
operation set, fits seven physically-scoped parameters of
``B200SubcorePartitionModel`` with ``scipy.optimize.minimize``, and compares
the resulting validation MAPE against the prior cycle-level and reservation
models.
"""

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

from subcore_partition_model import (  # type: ignore
    B200SubcorePartitionModel,
    B200SubcorePartitionModelSpec,
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
    """Convert predictor config to sub-core workload descriptor."""
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
    """Mean absolute percentage error (percent)."""
    mask = measured > 0
    return float(np.mean(np.abs((predicted[mask] - measured[mask]) / measured[mask])) * 100.0)


# -----------------------------------------------------------------------------
# Calibration
# -----------------------------------------------------------------------------


def make_spec_from_params(x: np.ndarray) -> B200SubcorePartitionModelSpec:
    """Build a ``B200SubcorePartitionModelSpec`` from the calibrated vector."""
    (
        tc_eff,
        sfu_eff,
        fp_eff,
        mem_eff,
        imbalance,
        overlap,
        launch_us,
    ) = x
    base = B200SubcorePartitionModelSpec()
    return replace(
        base,
        tc_efficiency=float(tc_eff),
        sfu_efficiency=float(sfu_eff),
        fp_efficiency=float(fp_eff),
        mem_efficiency=float(mem_eff),
        partition_imbalance_factor=float(imbalance),
        stage_overlap_factor=float(overlap),
        launch_overhead_us=float(launch_us),
    )


def objective(
    x: np.ndarray,
    cal_configs: List[FA4Config],
    cal_measured: np.ndarray,
) -> float:
    """Calibration objective: MAPE on the calibration split."""
    spec = make_spec_from_params(x)
    model = B200SubcorePartitionModel(spec)
    preds = np.array(
        [
            model.predict(config_to_workload(cfg))["predicted_runtime_ms"]
            for cfg in cal_configs
        ]
    )
    return mape(preds, cal_measured)


def fit_subcore_partition_model(
    cal_configs: List[FA4Config],
    cal_measured: np.ndarray,
) -> Tuple[B200SubcorePartitionModelSpec, Dict[str, Any]]:
    """Fit the seven subcore-partition parameters to the calibration data."""
    x0 = np.array(
        [1.0, 1.0, 1.0, 1.0, 0.0, 0.85, 2.0], dtype=float
    )
    bounds = [
        (0.20, 3.00),  # tc_efficiency
        (0.20, 3.00),  # sfu_efficiency
        (0.20, 3.00),  # fp_efficiency
        (0.20, 3.00),  # mem_efficiency
        (0.00, 2.00),  # partition_imbalance_factor
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
            "tc_efficiency",
            "sfu_efficiency",
            "fp_efficiency",
            "mem_efficiency",
            "partition_imbalance_factor",
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
    """Read the measurements CSV and split by the existing ``split`` column."""
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
    """Run calibration, validation, and write outputs."""
    out_dir = OPERATION_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    meas_path = OPERATION_DIR.parent / "20260705-inner-gpu-calibration-faddf4" / "measurements.csv"
    cal_configs, cal_measured, val_configs, val_measured = load_measurements(meas_path)
    print(f"Loaded {len(cal_configs)} calibration and {len(val_configs)} validation configs")

    if len(cal_configs) < 6:
        raise RuntimeError(f"Too few calibration measurements: {len(cal_configs)}")

    # Calibrate sub-core partition model.
    spec, cal_metrics = fit_subcore_partition_model(cal_configs, cal_measured)
    model = B200SubcorePartitionModel(spec)

    # Evaluate sub-core partition model.
    sub_cal_preds = np.array(
        [model.predict(config_to_workload(cfg))["predicted_runtime_ms"] for cfg in cal_configs]
    )
    sub_val_preds = np.array(
        [model.predict(config_to_workload(cfg))["predicted_runtime_ms"] for cfg in val_configs]
    )
    sub_cal_mape = mape(sub_cal_preds, cal_measured)
    sub_val_mape = mape(sub_val_preds, val_measured)

    # Baseline and improved predictors.
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

    # Save predictions.
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
                "subcore_predicted_ms",
                "baseline_predicted_ms",
                "improved_predicted_ms",
            ],
        )
        writer.writeheader()
        for split, configs, measured, sub_preds in [
            ("cal", cal_configs, cal_measured, sub_cal_preds),
            ("val", val_configs, val_measured, sub_val_preds),
        ]:
            for cfg, m, sp in zip(configs, measured, sub_preds):
                writer.writerow(
                    {
                        "split": split,
                        **config_to_dict(cfg),
                        "measured_runtime_ms": m,
                        "subcore_predicted_ms": sp,
                        "baseline_predicted_ms": base.predict(cfg)["predicted_runtime_ms"],
                        "improved_predicted_ms": improved.predict(cfg)["predicted_runtime_ms"],
                    }
                )

    # Save calibrated spec.
    spec_dict: Dict[str, Any] = {
        "tc_efficiency": spec.tc_efficiency,
        "sfu_efficiency": spec.sfu_efficiency,
        "fp_efficiency": spec.fp_efficiency,
        "mem_efficiency": spec.mem_efficiency,
        "partition_imbalance_factor": spec.partition_imbalance_factor,
        "stage_overlap_factor": spec.stage_overlap_factor,
        "launch_overhead_us": spec.launch_overhead_us,
        "num_sms": spec.num_sms,
        "partitions_per_sm": spec.partitions_per_sm,
        "peak_sm_clock_mhz": spec.peak_sm_clock_mhz,
    }
    with (out_dir / "subcore_model_spec.json").open("w") as f:
        json.dump(spec_dict, f, indent=2)

    summary = {
        "subcore_calibration_mape_percent": round(sub_cal_mape, 2),
        "subcore_validation_mape_percent": round(sub_val_mape, 2),
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
