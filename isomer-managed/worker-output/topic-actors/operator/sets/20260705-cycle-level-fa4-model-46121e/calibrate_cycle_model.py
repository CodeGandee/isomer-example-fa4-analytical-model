"""Calibrate and validate the cycle-level FA4 model on real B200 measurements.

The script reads the measurements CSV produced by the inner-GPU calibration
operation set, fits eight physically-scoped parameters of
``B200CycleLevelModel`` with ``scipy.optimize.minimize``, and compares the
resulting validation MAPE against the baseline and improved white-box
predictors.  No GPU is required.
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

from cycle_level_model import (  # type: ignore
    B200CycleLevelModel,
    B200CycleLevelModelSpec,
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
    """Convert predictor config to cycle-level workload descriptor."""
    return FA4WorkloadDesc(
        batch=cfg.batch,
        heads=cfg.heads,
        seqlen=cfg.seqlen,
        head_dim=cfg.head_dim,
        causal=cfg.causal,
        precision=cfg.precision,
    )


def config_to_dict(cfg: FA4Config) -> Dict[str, Any]:
    """Return a serialisable dict for a predictor config."""
    return {
        "batch": cfg.batch,
        "heads": cfg.heads,
        "seqlen": cfg.seqlen,
        "head_dim": cfg.head_dim,
        "causal": cfg.causal,
        "precision": cfg.normalized_precision,
    }


def config_to_fa4config(desc: FA4WorkloadDesc) -> FA4Config:
    """Convert cycle-level workload descriptor to predictor config."""
    return FA4Config(
        batch=desc.batch,
        heads=desc.heads,
        seqlen=desc.seqlen,
        head_dim=desc.head_dim,
        causal=desc.causal,
        precision=desc.precision,
    )


def mape(predicted: np.ndarray, measured: np.ndarray) -> float:
    """Mean absolute percentage error (percent)."""
    mask = measured > 0
    return float(np.mean(np.abs((predicted[mask] - measured[mask]) / measured[mask])) * 100.0)


# -----------------------------------------------------------------------------
# Calibration
# -----------------------------------------------------------------------------


def make_spec_from_params(x: np.ndarray) -> B200CycleLevelModelSpec:
    """Build a ``B200CycleLevelModelSpec`` from the calibrated vector."""
    (
        tc_eff,
        mufu_eff,
        hbm_eff,
        l1_miss,
        l2_miss,
        occ_eff,
        mem_overlap,
        launch_us,
    ) = x
    base = B200CycleLevelModelSpec()
    return replace(
        base,
        tc_efficiency=float(tc_eff),
        mufu_efficiency=float(mufu_eff),
        hbm_efficiency=float(hbm_eff),
        l1_miss_rate=float(l1_miss),
        l2_miss_rate=float(l2_miss),
        occupancy_efficiency=float(occ_eff),
        memory_overlap_factor=float(mem_overlap),
        launch_overhead_us=float(launch_us),
    )


def objective(
    x: np.ndarray,
    cal_configs: List[FA4Config],
    cal_measured: np.ndarray,
) -> float:
    """Calibration objective: validation MAPE on the calibration split."""
    spec = make_spec_from_params(x)
    model = B200CycleLevelModel(spec)
    preds = np.array(
        [
            model.predict(config_to_workload(cfg))["predicted_runtime_ms"]
            for cfg in cal_configs
        ]
    )
    return mape(preds, cal_measured)


def fit_cycle_model(
    cal_configs: List[FA4Config],
    cal_measured: np.ndarray,
) -> Tuple[B200CycleLevelModelSpec, Dict[str, Any]]:
    """Fit the eight cycle-level parameters to the calibration data."""
    x0 = np.array(
        [1.0, 1.0, 1.0, 0.08, 0.25, 1.0, 0.85, 2.0], dtype=float
    )
    bounds = [
        (0.20, 3.00),  # tc_efficiency
        (0.20, 3.00),  # mufu_efficiency
        (0.20, 3.00),  # hbm_efficiency
        (0.00, 0.50),  # l1_miss_rate
        (0.00, 0.80),  # l2_miss_rate
        (0.20, 1.50),  # occupancy_efficiency
        (0.00, 1.00),  # memory_overlap_factor
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
            "mufu_efficiency",
            "hbm_efficiency",
            "l1_miss_rate",
            "l2_miss_rate",
            "occupancy_efficiency",
            "memory_overlap_factor",
            "launch_overhead_us",
        ],
    }
    return spec, metrics


# -----------------------------------------------------------------------------
# Baseline / improved predictor evaluation
# -----------------------------------------------------------------------------


def evaluate_legacy(
    predictor: Any,
    configs: List[FA4Config],
    measured: np.ndarray,
) -> float:
    """Return MAPE for a legacy predictor on ``configs``."""
    preds = np.array([predictor.predict(cfg)["predicted_runtime_ms"] for cfg in configs])
    return mape(preds, measured)


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

    # Calibrate cycle-level model.
    spec, cal_metrics = fit_cycle_model(cal_configs, cal_measured)
    cycle_model = B200CycleLevelModel(spec)

    # Evaluate cycle-level model.
    cycle_cal_preds = np.array(
        [
            cycle_model.predict(config_to_workload(cfg))["predicted_runtime_ms"]
            for cfg in cal_configs
        ]
    )
    cycle_val_preds = np.array(
        [
            cycle_model.predict(config_to_workload(cfg))["predicted_runtime_ms"]
            for cfg in val_configs
        ]
    )
    cycle_cal_mape = mape(cycle_cal_preds, cal_measured)
    cycle_val_mape = mape(cycle_val_preds, val_measured)

    # Baseline and improved predictors.
    base = baseline_predictor()
    base_cal_mape = evaluate_legacy(base, cal_configs, cal_measured)
    base_val_mape = evaluate_legacy(base, val_configs, val_measured)

    improved, _ = calibrate_improved(cal_configs, cal_measured.tolist())
    imp_cal_mape = evaluate_legacy(improved, cal_configs, cal_measured)
    imp_val_mape = evaluate_legacy(improved, val_configs, val_measured)

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
                "cycle_predicted_ms",
                "baseline_predicted_ms",
                "improved_predicted_ms",
            ],
        )
        writer.writeheader()
        for split, configs, measured, cycle_preds in [
            ("cal", cal_configs, cal_measured, cycle_cal_preds),
            ("val", val_configs, val_measured, cycle_val_preds),
        ]:
            for cfg, m, cp in zip(configs, measured, cycle_preds):
                writer.writerow(
                    {
                        "split": split,
                        **config_to_dict(cfg),
                        "measured_runtime_ms": m,
                        "cycle_predicted_ms": cp,
                        "baseline_predicted_ms": base.predict(cfg)["predicted_runtime_ms"],
                        "improved_predicted_ms": improved.predict(cfg)["predicted_runtime_ms"],
                    }
                )

    # Save calibrated spec.
    spec_dict: Dict[str, Any] = {
        "tc_efficiency": spec.tc_efficiency,
        "mufu_efficiency": spec.mufu_efficiency,
        "hbm_efficiency": spec.hbm_efficiency,
        "l1_miss_rate": spec.l1_miss_rate,
        "l2_miss_rate": spec.l2_miss_rate,
        "occupancy_efficiency": spec.occupancy_efficiency,
        "memory_overlap_factor": spec.memory_overlap_factor,
        "launch_overhead_us": spec.launch_overhead_us,
        "xbar_contention_scale": spec.xbar_contention_scale,
        "tc_mma_throughput_per_sm_per_clock": spec.tc_mma_throughput_per_sm_per_clock,
        "mufu_throughput_per_sm_per_clock": spec.mufu_throughput_per_sm_per_clock,
        "peak_hbm_bw_gbps": spec.peak_hbm_bw_gbps,
        "peak_l2_bw_gbps": spec.peak_l2_bw_gbps,
        "peak_l1_bw_gbps": spec.peak_l1_bw_gbps,
        "num_sms": spec.num_sms,
        "peak_sm_clock_mhz": spec.peak_sm_clock_mhz,
    }
    with (out_dir / "cycle_model_spec.json").open("w") as f:
        json.dump(spec_dict, f, indent=2)

    summary = {
        "cycle_calibration_mape_percent": round(cycle_cal_mape, 2),
        "cycle_validation_mape_percent": round(cycle_val_mape, 2),
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
