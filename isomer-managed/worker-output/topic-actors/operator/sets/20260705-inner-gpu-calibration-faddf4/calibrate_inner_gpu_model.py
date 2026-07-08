"""Calibrate and validate the AccelSim-inspired inner-GPU model on real B200.

This script keeps the experiment minimal:
- 16 configs for calibration
- 8 configs for held-out validation
- fits five physically-scoped parameters with bounded scipy optimization
- compares MAPE against the existing baseline and improved predictors.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
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

from fa4_b200_predictor.improved_predictor import (  # type: ignore
    ImprovedPredictor,
    calibrate_improved,
)
from fa4_b200_predictor.predictor import FA4Config, baseline_predictor  # type: ignore
from fa4_b200_predictor.real_hardware_benchmark import (  # type: ignore
    SUPPORTED_DTYPES,
    measure_config,
    stratified_split,
)
from inner_gpu_model import (  # type: ignore
    B200InnerGPUModel,
    B200InnerGPUModelSpec,
    FA4WorkloadDesc,
)

# Experiment matrix -----------------------------------------------------------
BATCH = 2
HEADS = 16
SEQLENS = [1024, 4096, 8192]
HEAD_DIMS = [64, 128]
CAUSAL = [True, False]
PRECISIONS = ["fp16", "fp8"]


def build_matrix() -> List[FA4Config]:
    configs: List[FA4Config] = []
    for s in SEQLENS:
        for d in HEAD_DIMS:
            for causal in CAUSAL:
                for p in PRECISIONS:
                    configs.append(
                        FA4Config(
                            batch=BATCH,
                            heads=HEADS,
                            seqlen=s,
                            head_dim=d,
                            causal=causal,
                            precision=p,
                        )
                    )
    return configs


def fa4config_to_workload(cfg: FA4Config) -> FA4WorkloadDesc:
    return FA4WorkloadDesc(
        batch=cfg.batch,
        heads=cfg.heads,
        seqlen=cfg.seqlen,
        head_dim=cfg.head_dim,
        causal=cfg.causal,
        precision=cfg.precision,
    )


# Measurements ----------------------------------------------------------------

def measure_configs(
    configs: List[FA4Config],
    device: torch.device,
    warmup: int = 3,
    timed: int = 10,
) -> List[Dict[str, Any]]:
    measurements = []
    for i, cfg in enumerate(configs):
        print(f"[{i + 1}/{len(configs)}] measuring {config_to_str(cfg)}")
        meas = measure_config(cfg, device, warmup_runs=warmup, timed_runs=timed)
        measurements.append({"config": config_to_dict(cfg), **meas})
    return measurements


def config_to_str(cfg: FA4Config) -> str:
    return (
        f"b{cfg.batch}_h{cfg.heads}_s{cfg.seqlen}_d{cfg.head_dim}_"
        f"c{int(cfg.causal)}_{cfg.normalized_precision}"
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


# Model calibration -----------------------------------------------------------

def make_spec_from_params(x: np.ndarray) -> B200InnerGPUModelSpec:
    tc_scale, occ_eff, l1_miss, l2_miss, row_hit = x
    base = B200InnerGPUModelSpec()
    mma = {k: v * tc_scale for k, v in base.mma_throughput_per_sm_per_clock.items()}
    return replace(
        base,
        mma_throughput_per_sm_per_clock=mma,
        operand_collector_efficiency=float(occ_eff),
        l1_miss_rate=float(l1_miss),
        l2_miss_rate=float(l2_miss),
        hbm_row_buffer_hit_rate=float(row_hit),
    )


def objective(
    x: np.ndarray,
    cal_configs: List[FA4Config],
    cal_measured: np.ndarray,
) -> float:
    spec = make_spec_from_params(x)
    model = B200InnerGPUModel(spec)
    preds = np.array(
        [model.predict(fa4config_to_workload(cfg))["predicted_runtime_ms"] for cfg in cal_configs]
    )
    return mape(preds, cal_measured)


def fit_inner_model(
    cal_configs: List[FA4Config],
    cal_measured: List[Dict[str, Any]],
) -> Tuple[B200InnerGPUModelSpec, Dict[str, float]]:
    measured = np.array([m["measured_runtime_ms"] for m in cal_measured])

    # Initial guess and physically reasonable bounds.
    x0 = np.array([1.0, 0.92, 0.08, 0.25, 0.65], dtype=float)
    bounds = [
        (0.1, 5.0),   # tc_scale
        (0.1, 1.0),   # operand_collector_efficiency
        (0.0, 0.5),   # l1_miss_rate
        (0.0, 0.8),   # l2_miss_rate
        (0.0, 1.0),   # hbm_row_buffer_hit_rate
    ]

    result = minimize(
        objective,
        x0,
        args=(cal_configs, measured),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 200, "disp": False},
    )
    spec = make_spec_from_params(result.x)
    metrics = {"mape_percent": result.fun, "success": result.success, "params": result.x.tolist()}
    return spec, metrics


# Baseline / improved predictor evaluation ------------------------------------

def evaluate_legacy(
    predictor: Any,
    configs: List[FA4Config],
    measured: np.ndarray,
) -> float:
    preds = np.array([predictor.predict(cfg)["predicted_runtime_ms"] for cfg in configs])
    return mape(preds, measured)


# Main ------------------------------------------------------------------------

def main() -> None:
    out_dir = OPERATION_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda:0")
    print(f"Device: {torch.cuda.get_device_name(device)} ({device})")

    all_configs = build_matrix()
    rng = np.random.default_rng(20260705)
    indices = np.arange(len(all_configs))
    rng.shuffle(indices)

    n_cal = 16
    n_val = 8
    cal_idx = indices[:n_cal].tolist()
    val_idx = indices[n_cal : n_cal + n_val].tolist()
    cal_configs = [all_configs[i] for i in cal_idx]
    val_configs = [all_configs[i] for i in val_idx]

    print(f"Calibration configs: {len(cal_configs)}; validation configs: {len(val_configs)}")

    # Measure
    t0 = time.time()
    cal_meas = measure_configs(cal_configs, device)
    val_meas = measure_configs(val_configs, device)
    print(f"Measurement wall time: {time.time() - t0:.1f}s")

    # Save raw measurements
    with (out_dir / "measurements.csv").open("w", newline="") as f:
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
                "measured_runtime_std_ms",
                "status",
                "error",
                "times_ms",
            ],
        )
        writer.writeheader()
        for split, rows in [("cal", cal_meas), ("val", val_meas)]:
            for row in rows:
                record = {"split": split, **row["config"]}
                record.update({k: row[k] for k in writer.fieldnames if k in row and k != "split"})
                writer.writerow(record)

    # Filter successful measurements
    def ok(rows):
        return [r for r in rows if r["status"] == "ok"]

    cal_ok = ok(cal_meas)
    val_ok = ok(val_meas)
    cal_configs_ok = [cfg for cfg, r in zip(cal_configs, cal_meas) if r["status"] == "ok"]
    val_configs_ok = [cfg for cfg, r in zip(val_configs, val_meas) if r["status"] == "ok"]

    if len(cal_ok) < 6:
        raise RuntimeError(f"Too few successful calibration measurements: {len(cal_ok)}")

    # Calibrate inner model
    spec, cal_metrics = fit_inner_model(cal_configs_ok, cal_ok)
    inner_model = B200InnerGPUModel(spec)

    # Evaluate
    cal_measured = np.array([r["measured_runtime_ms"] for r in cal_ok])
    val_measured = np.array([r["measured_runtime_ms"] for r in val_ok])

    inner_cal_preds = np.array(
        [inner_model.predict(fa4config_to_workload(cfg))["predicted_runtime_ms"] for cfg in cal_configs_ok]
    )
    inner_val_preds = np.array(
        [inner_model.predict(fa4config_to_workload(cfg))["predicted_runtime_ms"] for cfg in val_configs_ok]
    )

    inner_cal_mape = mape(inner_cal_preds, cal_measured)
    inner_val_mape = mape(inner_val_preds, val_measured)

    # Baseline and improved
    base = baseline_predictor()
    base_cal_mape = evaluate_legacy(base, cal_configs_ok, cal_measured)
    base_val_mape = evaluate_legacy(base, val_configs_ok, val_measured)

    improved, _ = calibrate_improved(cal_configs_ok, [r["measured_runtime_ms"] for r in cal_ok])
    imp_cal_mape = evaluate_legacy(improved, cal_configs_ok, cal_measured)
    imp_val_mape = evaluate_legacy(improved, val_configs_ok, val_measured)

    # Save predictions
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
                "inner_predicted_ms",
                "baseline_predicted_ms",
                "improved_predicted_ms",
            ],
        )
        writer.writeheader()
        for split, configs, rows in [("cal", cal_configs_ok, cal_ok), ("val", val_configs_ok, val_ok)]:
            for cfg, row, ip, bp, imp in zip(
                configs,
                rows,
                inner_cal_preds if split == "cal" else inner_val_preds,
                [base.predict(cfg)["predicted_runtime_ms"] for cfg in configs],
                [improved.predict(cfg)["predicted_runtime_ms"] for cfg in configs],
            ):
                writer.writerow(
                    {
                        "split": split,
                        **config_to_dict(cfg),
                        "measured_runtime_ms": row["measured_runtime_ms"],
                        "inner_predicted_ms": ip,
                        "baseline_predicted_ms": bp,
                        "improved_predicted_ms": imp,
                    }
                )

    # Save calibration spec
    with (out_dir / "inner_model_spec.json").open("w") as f:
        json.dump(
            {
                "mma_throughput_per_sm_per_clock": spec.mma_throughput_per_sm_per_clock,
                "operand_collector_efficiency": spec.operand_collector_efficiency,
                "l1_miss_rate": spec.l1_miss_rate,
                "l2_miss_rate": spec.l2_miss_rate,
                "hbm_row_buffer_hit_rate": spec.hbm_row_buffer_hit_rate,
            },
            f,
            indent=2,
        )

    summary = {
        "calibration_mape_percent": round(inner_cal_mape, 2),
        "validation_mape_percent": round(inner_val_mape, 2),
        "baseline_validation_mape_percent": round(base_val_mape, 2),
        "improved_validation_mape_percent": round(imp_val_mape, 2),
        "calibration_count": len(cal_ok),
        "validation_count": len(val_ok),
        "calibration_success": cal_metrics["success"],
        "fit_params": cal_metrics["params"],
        "spec": {
            "mma_throughput_per_sm_per_clock_fp16": spec.mma_throughput_per_sm_per_clock["fp16"],
            "mma_throughput_per_sm_per_clock_fp8": spec.mma_throughput_per_sm_per_clock["fp8"],
            "operand_collector_efficiency": spec.operand_collector_efficiency,
            "l1_miss_rate": spec.l1_miss_rate,
            "l2_miss_rate": spec.l2_miss_rate,
            "hbm_row_buffer_hit_rate": spec.hbm_row_buffer_hit_rate,
        },
    }

    with (out_dir / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== Summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
