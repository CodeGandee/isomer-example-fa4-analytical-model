"""Main experiment runner for the improved FA4 B200 white-box predictor.

Measures real B200 runtimes for a bounded config matrix, profiles a stratified
subset with NCU, calibrates the improved predictor on the calibration split
only, and reports held-out validation/query metrics.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import torch

from fa4_b200_predictor.config_matrix import config_to_dict
from fa4_b200_predictor.evaluate import evaluate_predictor
from fa4_b200_predictor.improved_predictor import ImprovedPredictor, calibrate_improved
from fa4_b200_predictor.ncu_profile import (
    attach_ncu_labels,
    coarse_bottleneck,
    profile_configs,
)
from fa4_b200_predictor.predictor import FA4Config, baseline_predictor
from fa4_b200_predictor.real_hardware_benchmark import (
    SUPPORTED_DTYPES,
    measure_config,
    stratified_split,
)


# Bounded matrix used for this pass.  We drop fp4 (unsupported) and the longest
# sequence to stay comfortably inside the ~25-minute wall-clock budget while
# still yielding >= 200 diverse configs.
BATCHES = [1, 4, 8]
HEADS = [16, 32, 64]
SEQLENS = [1024, 2048, 4096, 8192, 16384]
HEAD_DIMS = [64, 128]
CAUSAL = [True, False]
PRECISIONS = ["bf16", "fp16", "fp8"]


def build_bounded_matrix() -> List[FA4Config]:
    """Generate the bounded Cartesian config matrix for this experiment."""
    configs: List[FA4Config] = []
    for b in BATCHES:
        for h in HEADS:
            for s in SEQLENS:
                for d in HEAD_DIMS:
                    for causal in CAUSAL:
                        for p in PRECISIONS:
                            configs.append(
                                FA4Config(
                                    batch=b,
                                    heads=h,
                                    seqlen=s,
                                    head_dim=d,
                                    causal=causal,
                                    precision=p,
                                )
                            )
    return configs


def select_ncu_subset(
    configs: List[FA4Config],
    seqlens: List[int] = None,
    head_dims: List[int] = None,
    precisions: List[str] = None,
    seed: int = 20260704,
) -> List[FA4Config]:
    """Choose a stratified NCU subset covering sequence/headdim/causal/precision."""
    seqlens = seqlens or SEQLENS
    head_dims = head_dims or HEAD_DIMS
    precisions = precisions or PRECISIONS

    # Fix batch/head count to keep the subset focused but diverse in the
    # dimensions that most change the bottleneck.
    subset: List[FA4Config] = []
    for s in seqlens:
        for d in head_dims:
            for causal in [True, False]:
                for p in precisions:
                    subset.append(
                        FA4Config(
                            batch=4,
                            heads=32,
                            seqlen=s,
                            head_dim=d,
                            causal=causal,
                            precision=p,
                        )
                    )
    rng = random.Random(seed)
    rng.shuffle(subset)
    return subset


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
    """Evaluate the improved predictor on a split.

    Bottleneck accuracy is computed only on configs that were profiled with NCU
    and therefore have a hardware-counter label.
    """
    base = evaluate_predictor(_as_legacy_predictor(predictor), configs, measurements)

    ncu_rows = [
        (cfg, meas)
        for cfg, meas in zip(configs, measurements)
        if meas.get("ncu_bottleneck") in ("compute", "memory")
    ]
    if ncu_rows:
        correct = 0
        for cfg, meas in ncu_rows:
            pred_label = predictor.predict(cfg)["predicted_bottleneck"]
            if coarse_bottleneck(pred_label) == meas["ncu_bottleneck"]:
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
    """Write per-config predictions for the improved model."""
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
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--seed", type=int, default=20260704)
    parser.add_argument("--calibration-frac", type=float, default=0.20)
    parser.add_argument("--validation-frac", type=float, default=0.20)
    parser.add_argument("--calibration-rounds", type=int, default=2)
    parser.add_argument("--ncu-subset-size", type=int, default=0)
    parser.add_argument("--skip-ncu", action="store_true")
    args = parser.parse_args(argv)

    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device(args.device)
    torch.cuda.set_device(device)
    print(f"Using device: {device} ({torch.cuda.get_device_name(device)})")

    # 1. Config matrix and splits.
    configs = build_bounded_matrix()
    print(f"Generated {len(configs)} configs")
    cal_configs, val_configs, query_configs = stratified_split(
        configs,
        calibration_frac=args.calibration_frac,
        validation_frac=args.validation_frac,
        seed=args.seed,
    )
    print(f"Split: cal={len(cal_configs)}, val={len(val_configs)}, query={len(query_configs)}")

    split_dir = out_dir / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    for name, split in [
        ("calibration", cal_configs),
        ("validation", val_configs),
        ("query", query_configs),
    ]:
        with (split_dir / f"{name}_configs.json").open("w", encoding="utf-8") as f:
            json.dump([config_to_dict(c) for c in split], f, indent=2)

    # 2. Real-hardware timing.
    print("Starting real B200 measurements...")
    t0 = time.time()
    all_measurements: List[Dict[str, Any]] = []
    counts = {"ok": 0, "oom": 0, "error": 0}
    for i, cfg in enumerate(configs):
        meas = measure_config(cfg, device, warmup_runs=3, timed_runs=10)
        counts[meas["status"]] += 1
        record = {
            **config_to_dict(cfg),
            "status": meas["status"],
            "measured_runtime_ms": meas["measured_runtime_ms"],
            "measured_runtime_std_ms": meas["measured_runtime_std_ms"],
            "measured_bottleneck": "unknown",
            "error": meas["error"],
        }
        all_measurements.append(record)
        if (i + 1) % 50 == 0 or i == len(configs) - 1:
            print(
                f"Measured {i + 1}/{len(configs)} configs "
                f"(ok={counts['ok']}, oom={counts['oom']}, error={counts['error']}) "
                f"elapsed={time.time() - t0:.1f}s"
            )

    with (out_dir / "all_measurements.json").open("w", encoding="utf-8") as f:
        json.dump(all_measurements, f, indent=2)

    with (out_dir / "all_measurements.csv").open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(config_to_dict(configs[0]).keys()) + [
            "status",
            "measured_runtime_ms",
            "measured_runtime_std_ms",
            "measured_bottleneck",
            "error",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_measurements:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    # 3. NCU profiling on a stratified subset.
    ncu_records: List[Dict[str, Any]] = []
    ncu_counts = {"ok": 0, "error": 0}
    if not args.skip_ncu:
        ncu_subset = select_ncu_subset(configs)
        if args.ncu_subset_size > 0:
            ncu_subset = ncu_subset[: args.ncu_subset_size]
        print(f"NCU profiling {len(ncu_subset)} representative configs...")
        ncu_records, ncu_counts = profile_configs(ncu_subset, device=str(device))
        with (out_dir / "ncu_records.json").open("w", encoding="utf-8") as f:
            json.dump(ncu_records, f, indent=2)
        attach_ncu_labels(all_measurements, ncu_records)

    # 4. Build per-split OK sets.
    config_index = {id(c): i for i, c in enumerate(configs)}
    cal_idx = [config_index[id(c)] for c in cal_configs]
    val_idx = [config_index[id(c)] for c in val_configs]
    query_idx = [config_index[id(c)] for c in query_configs]

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

    # 5. Calibrate improved predictor on calibration split only.
    cal_runtimes = [m["measured_runtime_ms"] for m in cal_measurements]
    print(f"Calibrating improved model on {len(cal_runtimes)} calibration configs...")
    improved, improved_params = calibrate_improved(
        cal_configs_ok, cal_runtimes, rounds=args.calibration_rounds
    )
    print(f"Calibrated params: {improved_params}")
    with (out_dir / "calibration_params.json").open("w", encoding="utf-8") as f:
        json.dump(improved_params, f, indent=2)

    # 6. Evaluate on held-out validation and query sets.
    baseline = baseline_predictor()
    baseline_val = evaluate_predictor(baseline, val_configs_ok, val_measurements)
    baseline_query = evaluate_predictor(baseline, query_configs_ok, query_measurements)

    improved_val = evaluate_improved(improved, val_configs_ok, val_measurements)
    improved_query = evaluate_improved(improved, query_configs_ok, query_measurements)

    val_results = {
        "baseline_fa4_roofline": baseline_val,
        "improved": improved_val,
    }
    query_results = {
        "baseline_fa4_roofline": baseline_query,
        "improved": improved_query,
    }

    save_evaluation(val_results, out_dir / "validation_metrics")
    save_evaluation(query_results, out_dir / "query_metrics")
    save_predictions(improved, val_configs_ok, val_measurements, out_dir / "improved_validation_predictions.csv")
    save_predictions(improved, query_configs_ok, query_measurements, out_dir / "improved_query_predictions.csv")

    delta_val_mape = baseline_val["mape"] - improved_val["mape"]
    delta_query_mape = baseline_query["mape"] - improved_query["mape"]

    success_val = (
        improved_val["mape"] <= 25.0
        and improved_val["pct_within_30"] >= 75.0
        and improved_val.get("ncu_bottleneck_accuracy", 0.0) >= 75.0
        and delta_val_mape >= 5.0
    )
    success_query = (
        improved_query["mape"] <= 25.0
        and improved_query["pct_within_30"] >= 75.0
        and improved_query.get("ncu_bottleneck_accuracy", 0.0) >= 75.0
        and delta_query_mape >= 5.0
    )

    if counts["error"] > max(5, len(configs) * 0.05):
        status = "inconclusive"
        status_reason = f"Too many measurement errors ({counts['error']}) to trust the result."
    elif ncu_counts["error"] > max(5, len(ncu_records) * 0.20):
        status = "inconclusive"
        status_reason = f"Too many NCU profiling errors ({ncu_counts['error']}) to trust bottleneck labels."
    elif success_val and success_query:
        status = "supported"
        status_reason = "Improved predictor meets all useful-improvement thresholds on real B200 measurements."
    else:
        status = "refuted"
        status_reason = "Improved predictor fails at least one useful-improvement threshold."

    experiment_result = {
        "status": status,
        "status_reason": status_reason,
        "hypothesis_id": "fa4-b200-improved-launch-overhead-ncu-calibration-v1",
        "precisions_tested": list(SUPPORTED_DTYPES.keys()),
        "precisions_skipped": ["fp4"],
        "config_counts": {
            "generated": len(configs),
            "calibration": len(cal_configs),
            "validation": len(val_configs),
            "query": len(query_configs),
            "ok": counts["ok"],
            "oom": counts["oom"],
            "error": counts["error"],
            "ok_calibration": len(cal_configs_ok),
            "ok_validation": len(val_configs_ok),
            "ok_query": len(query_configs_ok),
            "ncu_profiled": len(ncu_records),
            "ncu_ok": ncu_counts["ok"],
            "ncu_error": ncu_counts["error"],
        },
        "calibration_params": improved_params,
        "validation_metrics": {
            "baseline_mape": baseline_val["mape"],
            "improved_mape": improved_val["mape"],
            "delta_mape_pp": delta_val_mape,
            "max_ape": improved_val["max_ape"],
            "pct_within_30": improved_val["pct_within_30"],
            "bottleneck_accuracy": improved_val.get("bottleneck_accuracy", float("nan")),
            "ncu_bottleneck_accuracy": improved_val.get("ncu_bottleneck_accuracy", float("nan")),
            "ncu_profiled_count": improved_val.get("ncu_profiled_count", 0),
            "n_configs": improved_val["n_configs"],
            "per_model": val_results,
        },
        "query_metrics": {
            "baseline_mape": baseline_query["mape"],
            "improved_mape": improved_query["mape"],
            "delta_mape_pp": delta_query_mape,
            "max_ape": improved_query["max_ape"],
            "pct_within_30": improved_query["pct_within_30"],
            "bottleneck_accuracy": improved_query.get("bottleneck_accuracy", float("nan")),
            "ncu_bottleneck_accuracy": improved_query.get("ncu_bottleneck_accuracy", float("nan")),
            "ncu_profiled_count": improved_query.get("ncu_profiled_count", 0),
            "n_configs": improved_query["n_configs"],
            "per_model": query_results,
        },
        "environment": {
            "device_name": torch.cuda.get_device_name(device),
            "cuda_version": torch.version.cuda,
            "torch_version": torch.__version__,
        },
        "caveats": [
            "fp4 precision is not supported by the installed FA4 build and was skipped.",
            "Bottleneck accuracy uses NCU SpeedOfLight compute/memory labels on a profiled subset; unprofiled configs are excluded from that metric.",
        ],
    }

    with (out_dir / "experiment_result.json").open("w", encoding="utf-8") as f:
        json.dump(experiment_result, f, indent=2)

    print(json.dumps(experiment_result, indent=2))
    print(f"Experiment status: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
