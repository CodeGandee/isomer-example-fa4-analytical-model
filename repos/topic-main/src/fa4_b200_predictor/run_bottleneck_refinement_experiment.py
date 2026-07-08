"""Bottleneck-mapping refinement experiment for the FA4 B200 white-box predictor.

This pass reuses the real-hardware measurements and NCU records from the
previous improved-predictor run.  It keeps the runtime calibration intact,
adds an NCU-guided bottleneck-threshold calibration, and reports whether the
refined model pushes NCU bottleneck accuracy above 75% while preserving MAPE.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from fa4_b200_predictor.config_matrix import config_to_dict, dict_to_config
from fa4_b200_predictor.improved_predictor import (
    ImprovedPredictor,
    calibrate_bottleneck_threshold,
    calibrate_improved,
)
from fa4_b200_predictor.ncu_profile import attach_ncu_labels
from fa4_b200_predictor.predictor import FA4Config, baseline_predictor
from fa4_b200_predictor.evaluate import evaluate_predictor


def _config_key(d: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        d.get("batch"),
        d.get("heads"),
        d.get("seqlen"),
        d.get("head_dim"),
        d.get("causal"),
        d.get("precision"),
    )


def load_previous_run(prev_dir: Path) -> Tuple[List[FA4Config], List[Dict[str, Any]]]:
    """Load the full measurement matrix and attach NCU labels."""
    with (prev_dir / "all_measurements.json").open("r", encoding="utf-8") as f:
        measurements = json.load(f)
    with (prev_dir / "ncu_records.json").open("r", encoding="utf-8") as f:
        ncu_records = json.load(f)
    attach_ncu_labels(measurements, ncu_records)

    configs = [dict_to_config(m) for m in measurements]
    return configs, measurements


def load_split(prev_dir: Path, name: str) -> List[FA4Config]:
    """Load a previous split and convert to FA4Config objects."""
    path = prev_dir / "splits" / f"{name}_configs.json"
    with path.open("r", encoding="utf-8") as f:
        return [dict_to_config(d) for d in json.load(f)]


def filter_ok(
    configs: List[FA4Config],
    measurements: List[Dict[str, Any]],
) -> Tuple[List[FA4Config], List[Dict[str, Any]]]:
    """Return configs and measurements that ran successfully."""
    ok_configs: List[FA4Config] = []
    ok_measurements: List[Dict[str, Any]] = []
    for cfg, meas in zip(configs, measurements):
        if meas["status"] == "ok":
            ok_configs.append(cfg)
            ok_measurements.append(meas)
    return ok_configs, ok_measurements


def evaluate_improved(
    predictor: ImprovedPredictor,
    configs: List[FA4Config],
    measurements: List[Dict[str, Any]],
) -> Dict[str, float]:
    """Evaluate the improved predictor on a split, including NCU bottleneck accuracy."""
    wrapper = _as_legacy_predictor(predictor)
    base = evaluate_predictor(wrapper, configs, measurements)

    ncu_rows = [
        (cfg, meas)
        for cfg, meas in zip(configs, measurements)
        if meas.get("ncu_bottleneck") in ("compute", "memory")
    ]
    if ncu_rows:
        correct = 0
        for cfg, meas in ncu_rows:
            pred_label = predictor.predict(cfg)["predicted_bottleneck"]
            coarse = "compute" if pred_label in ("mma", "mufu") else "memory"
            if coarse == meas["ncu_bottleneck"]:
                correct += 1
        base["ncu_bottleneck_accuracy"] = 100.0 * correct / len(ncu_rows)
        base["ncu_profiled_count"] = len(ncu_rows)
    else:
        base["ncu_bottleneck_accuracy"] = float("nan")
        base["ncu_profiled_count"] = 0

    return base


def _as_legacy_predictor(predictor: ImprovedPredictor):
    """Wrap an ImprovedPredictor so the legacy evaluator can call it."""

    class _Wrapper:
        def __init__(self, p: ImprovedPredictor) -> None:
            self.name = p.name
            self._p = p

        def predict(self, cfg: FA4Config) -> Dict[str, Any]:
            return self._p.predict(cfg)

    return _Wrapper(predictor)


def save_predictions(
    predictor: ImprovedPredictor,
    configs: List[FA4Config],
    measurements: List[Dict[str, Any]],
    out_path: Path,
) -> None:
    """Write per-config predictions for the refined model."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
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
                "measured_bottleneck": meas.get("measured_bottleneck", "unknown"),
                "ncu_bottleneck": meas.get("ncu_bottleneck", "unprofiled"),
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
                "ncu_bottleneck",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def save_evaluation(
    results: Dict[str, Dict[str, float]],
    out_dir: Path,
) -> None:
    """Write metrics JSON and CSV."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    with (out_dir / "metrics.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "model",
                "mape",
                "max_ape",
                "pct_within_30",
                "bottleneck_accuracy",
                "ncu_bottleneck_accuracy",
                "ncu_profiled_count",
                "n_configs",
            ],
        )
        writer.writeheader()
        for model, metrics in results.items():
            row = {"model": model, **metrics}
            writer.writerow(row)


def main(argv=None):  # type: ignore
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--previous-run-dir",
        type=Path,
        required=True,
        help="Directory containing the previous improved-run outputs.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--calibration-rounds", type=int, default=2)
    args = parser.parse_args(argv)

    prev_dir: Path = args.previous_run_dir
    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load previous measurements and splits.
    all_configs, all_measurements = load_previous_run(prev_dir)
    config_index = {_config_key(config_to_dict(c)): i for i, c in enumerate(all_configs)}

    cal_configs = load_split(prev_dir, "calibration")
    val_configs = load_split(prev_dir, "validation")
    query_configs = load_split(prev_dir, "query")

    cal_idx = [config_index[_config_key(config_to_dict(c))] for c in cal_configs]
    val_idx = [config_index[_config_key(config_to_dict(c))] for c in val_configs]
    query_idx = [config_index[_config_key(config_to_dict(c))] for c in query_configs]

    cal_configs_ok, cal_measurements = filter_ok(
        cal_configs, [all_measurements[i] for i in cal_idx]
    )
    val_configs_ok, val_measurements = filter_ok(
        val_configs, [all_measurements[i] for i in val_idx]
    )
    query_configs_ok, query_measurements = filter_ok(
        query_configs, [all_measurements[i] for i in query_idx]
    )

    print(
        f"OK counts: cal={len(cal_configs_ok)}, val={len(val_configs_ok)}, query={len(query_configs_ok)}"
    )

    if len(cal_configs_ok) < 10:
        raise RuntimeError(
            f"Too few calibration measurements ({len(cal_configs_ok)}); cannot calibrate."
        )

    # 2. Re-run runtime calibration on the calibration split (unchanged from previous pass).
    cal_runtimes = [m["measured_runtime_ms"] for m in cal_measurements]
    print(f"Recalibrating runtime model on {len(cal_runtimes)} calibration configs...")
    improved, improved_params = calibrate_improved(
        cal_configs_ok, cal_runtimes, rounds=args.calibration_rounds
    )
    print(f"Runtime calibration params: {improved_params}")

    # 3. Calibrate bottleneck threshold on NCU-labelled calibration configs.
    print("Calibrating bottleneck threshold on NCU labels...")
    slack = calibrate_bottleneck_threshold(improved, cal_configs_ok, cal_measurements)
    print(f"Calibrated bottleneck_mem_slack: {slack:.4f}")

    refined = improved.__class__(**{**improved.to_params(), "bottleneck_mem_slack": slack})
    refined_params = refined.to_params()
    print(f"Refined params: {refined_params}")
    with (out_dir / "calibration_params.json").open("w", encoding="utf-8") as f:
        json.dump(refined_params, f, indent=2)

    # 4. Evaluate on held-out validation and query sets.
    baseline = baseline_predictor()
    baseline_val = evaluate_predictor(baseline, val_configs_ok, val_measurements)
    baseline_query = evaluate_predictor(baseline, query_configs_ok, query_measurements)

    refined_val = evaluate_improved(refined, val_configs_ok, val_measurements)
    refined_query = evaluate_improved(refined, query_configs_ok, query_measurements)

    val_results = {
        "baseline_fa4_roofline": baseline_val,
        "refined": refined_val,
    }
    query_results = {
        "baseline_fa4_roofline": baseline_query,
        "refined": refined_query,
    }

    save_evaluation(val_results, out_dir / "validation_metrics")
    save_evaluation(query_results, out_dir / "query_metrics")
    save_predictions(
        refined, val_configs_ok, val_measurements, out_dir / "refined_validation_predictions.csv"
    )
    save_predictions(
        refined, query_configs_ok, query_measurements, out_dir / "refined_query_predictions.csv"
    )

    # Copy raw data for reproducibility.
    with (out_dir / "all_measurements.json").open("w", encoding="utf-8") as f:
        json.dump(all_measurements, f, indent=2)
    with (out_dir / "ncu_records.json").open("w", encoding="utf-8") as f:
        json.dump(json.load((prev_dir / "ncu_records.json").open()), f, indent=2)

    delta_val_mape = baseline_val["mape"] - refined_val["mape"]
    delta_query_mape = baseline_query["mape"] - refined_query["mape"]

    success_val = (
        refined_val["mape"] <= 25.0
        and refined_val["pct_within_30"] >= 75.0
        and refined_val.get("ncu_bottleneck_accuracy", 0.0) >= 75.0
        and delta_val_mape >= 5.0
    )
    success_query = (
        refined_query["mape"] <= 25.0
        and refined_query["pct_within_30"] >= 75.0
        and refined_query.get("ncu_bottleneck_accuracy", 0.0) >= 75.0
        and delta_query_mape >= 5.0
    )

    if success_val and success_query:
        status = "supported"
        status_reason = "Refined predictor meets all useful-improvement thresholds on real B200 measurements."
    else:
        status = "refuted"
        status_reason = "Refined predictor fails at least one useful-improvement threshold."

    # Load environment metadata from the previous experiment.
    with (prev_dir / "experiment_result.json").open("r", encoding="utf-8") as f:
        prev_experiment = json.load(f)

    experiment_result = {
        "status": status,
        "status_reason": status_reason,
        "hypothesis_id": "fa4-b200-bottleneck-threshold-calibration-v1",
        "precisions_tested": prev_experiment.get("precisions_tested", ["bf16", "fp16", "fp8"]),
        "precisions_skipped": prev_experiment.get("precisions_skipped", ["fp4"]),
        "config_counts": {
            "generated": prev_experiment.get("config_counts", {}).get("generated", len(all_configs)),
            "calibration": len(cal_configs),
            "validation": len(val_configs),
            "query": len(query_configs),
            "ok": sum(1 for m in all_measurements if m["status"] == "ok"),
            "oom": sum(1 for m in all_measurements if m["status"] == "oom"),
            "error": sum(1 for m in all_measurements if m["status"] == "error"),
            "ok_calibration": len(cal_configs_ok),
            "ok_validation": len(val_configs_ok),
            "ok_query": len(query_configs_ok),
            "ncu_profiled": len(json.load((prev_dir / "ncu_records.json").open())),
            "ncu_ok": prev_experiment.get("config_counts", {}).get("ncu_ok", 0),
            "ncu_error": prev_experiment.get("config_counts", {}).get("ncu_error", 0),
        },
        "calibration_params": refined_params,
        "validation_metrics": {
            "baseline_mape": baseline_val["mape"],
            "refined_mape": refined_val["mape"],
            "delta_mape_pp": delta_val_mape,
            "max_ape": refined_val["max_ape"],
            "pct_within_30": refined_val["pct_within_30"],
            "bottleneck_accuracy": refined_val.get("bottleneck_accuracy", float("nan")),
            "ncu_bottleneck_accuracy": refined_val.get("ncu_bottleneck_accuracy", float("nan")),
            "ncu_profiled_count": refined_val.get("ncu_profiled_count", 0),
            "n_configs": refined_val["n_configs"],
            "per_model": val_results,
        },
        "query_metrics": {
            "baseline_mape": baseline_query["mape"],
            "refined_mape": refined_query["mape"],
            "delta_mape_pp": delta_query_mape,
            "max_ape": refined_query["max_ape"],
            "pct_within_30": refined_query["pct_within_30"],
            "bottleneck_accuracy": refined_query.get("bottleneck_accuracy", float("nan")),
            "ncu_bottleneck_accuracy": refined_query.get("ncu_bottleneck_accuracy", float("nan")),
            "ncu_profiled_count": refined_query.get("ncu_profiled_count", 0),
            "n_configs": refined_query["n_configs"],
            "per_model": query_results,
        },
        "environment": prev_experiment.get(
            "environment",
            {
                "device_name": "NVIDIA B200",
                "cuda_version": "13.0",
                "torch_version": "2.12.1+cu130",
            },
        ),
        "caveats": [
            "fp4 precision is not supported by the installed FA4 build and was skipped.",
            "Bottleneck accuracy uses NCU SpeedOfLight compute/memory labels on a profiled subset; unprofiled configs are excluded from that metric.",
            "This pass reused the real-hardware measurements and NCU records from the previous improved-predictor run; only the bottleneck-mapping logic changed.",
        ],
    }

    with (out_dir / "experiment_result.json").open("w", encoding="utf-8") as f:
        json.dump(experiment_result, f, indent=2)

    print(json.dumps(experiment_result, indent=2))
    print(f"Experiment status: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
