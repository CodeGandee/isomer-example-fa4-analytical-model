"""Real-hardware benchmark for the FA4 B200 white-box runtime model.

This harness generates the design-matrix from `real-data-evaluation-dataset-design.md`,
launches `flash_attn_func` from `flash_attn.cute` on a single B200 (`cuda:0`),
measures median wall-clock runtime, runs the existing white-box predictors,
calibrates the combined model on the calibration split only, and reports
validation/query metrics.

Caveat on bottleneck labels
---------------------------
Real kernel launches give us wall-clock runtime, not hardware-counter breakdowns.
`measured_bottleneck` is therefore a white-box proxy: the dominant stage predicted
by the uncalibrated baseline predictor.  Bottleneck-label accuracy compares the
combined predictor's dominant-stage diagnosis to that proxy.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
from flash_attn.cute import flash_attn_func

from fa4_b200_predictor.calibrate import (
    calibrate_ablation_factors,
    calibrate_combined,
    save_calibration,
)
from fa4_b200_predictor.config_matrix import config_to_dict
from fa4_b200_predictor.evaluate import (
    evaluate_predictor,
    run_evaluation,
    save_evaluation,
    save_predictions,
)
from fa4_b200_predictor.predictor import (
    FA4Config,
    baseline_predictor,
    combined_predictor,
)


# Config matrix used by the dataset design doc.
DESIGN_BATCHES = [1, 2, 4, 8]
DESIGN_HEADS = [16, 32, 64]
DESIGN_SEQLENS = [1024, 2048, 4096, 8192, 16384, 32768]
DESIGN_HEAD_DIMS = [64, 128]
DESIGN_CAUSAL = [True, False]
DESIGN_PRECISIONS = ["bf16", "fp16", "fp8", "fp4"]

# Dtypes supported by the installed FA4 build. fp4 is not supported.
SUPPORTED_DTYPES = {
    "bf16": torch.bfloat16,
    "fp16": torch.float16,
    "fp8": torch.float8_e4m3fn,
}


def build_design_matrix(
    precisions: Optional[List[str]] = None,
) -> List[FA4Config]:
    """Generate the full Cartesian design matrix from the dataset design doc."""
    precisions = precisions or DESIGN_PRECISIONS
    configs: List[FA4Config] = []
    for b in DESIGN_BATCHES:
        for h in DESIGN_HEADS:
            for s in DESIGN_SEQLENS:
                for d in DESIGN_HEAD_DIMS:
                    for causal in DESIGN_CAUSAL:
                        for p in precisions:
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


def stratified_split(
    configs: List[FA4Config],
    calibration_frac: float = 0.20,
    validation_frac: float = 0.20,
    seed: int = 20260704,
) -> Tuple[List[FA4Config], List[FA4Config], List[FA4Config]]:
    """Stratified split across seqlen and precision, then random within strata."""
    rng = random.Random(seed)
    strata: Dict[Tuple[int, str], List[FA4Config]] = {}
    for cfg in configs:
        key = (cfg.seqlen, cfg.normalized_precision)
        strata.setdefault(key, []).append(cfg)

    cal: List[FA4Config] = []
    val: List[FA4Config] = []
    query: List[FA4Config] = []

    for key, stratum in sorted(strata.items()):
        shuffled = stratum[:]
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_cal = max(1, int(round(n * calibration_frac))) if n >= 3 else 0
        n_val = max(1, int(round(n * validation_frac))) if n >= 3 else 0
        # If stratum is tiny, put at least one sample in calibration.
        if n_cal + n_val > n:
            n_cal = n // 3 or (1 if n > 0 else 0)
            n_val = n // 3 or (1 if n > n_cal else 0)
        cal.extend(shuffled[:n_cal])
        val.extend(shuffled[n_cal : n_cal + n_val])
        query.extend(shuffled[n_cal + n_val :])

    return cal, val, query


def make_tensors(
    cfg: FA4Config,
    device: torch.device,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Create Q/K/V tensors in the precision required by the config."""
    shape = (cfg.batch, cfg.seqlen, cfg.heads, cfg.head_dim)
    dtype = SUPPORTED_DTYPES[cfg.normalized_precision]
    if cfg.normalized_precision == "fp8":
        # torch.randn does not support fp8; create bf16 and cast.
        q = torch.randn(shape, dtype=torch.bfloat16, device=device).to(dtype)
        k = torch.randn(shape, dtype=torch.bfloat16, device=device).to(dtype)
        v = torch.randn(shape, dtype=torch.bfloat16, device=device).to(dtype)
    else:
        q = torch.randn(shape, dtype=dtype, device=device)
        k = torch.randn(shape, dtype=dtype, device=device)
        v = torch.randn(shape, dtype=dtype, device=device)
    return q, k, v


def measure_config(
    cfg: FA4Config,
    device: torch.device,
    warmup_runs: int = 3,
    timed_runs: int = 10,
) -> Dict[str, Any]:
    """Measure a single config on real B200 hardware.

    Returns a dict with measured_runtime_ms, measured_runtime_std_ms, status, and
    error info.  status is one of 'ok', 'oom', or 'error'.
    """
    torch.cuda.synchronize(device)
    torch.cuda.empty_cache()
    torch.cuda.synchronize(device)

    try:
        q, k, v = make_tensors(cfg, device)
    except torch.cuda.OutOfMemoryError as exc:
        torch.cuda.empty_cache()
        return {
            "status": "oom",
            "measured_runtime_ms": float("nan"),
            "measured_runtime_std_ms": float("nan"),
            "error": str(exc),
        }

    # Warmup
    try:
        for _ in range(warmup_runs):
            _ = flash_attn_func(q, k, v, causal=cfg.causal)
        torch.cuda.synchronize(device)
    except torch.cuda.OutOfMemoryError as exc:
        torch.cuda.empty_cache()
        return {
            "status": "oom",
            "measured_runtime_ms": float("nan"),
            "measured_runtime_std_ms": float("nan"),
            "error": str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "measured_runtime_ms": float("nan"),
            "measured_runtime_std_ms": float("nan"),
            "error": f"{type(exc).__name__}: {exc}",
        }

    # Timed runs (wall-clock via host timer; synchronizes before/after).
    times_ms: List[float] = []
    try:
        for _ in range(timed_runs):
            torch.cuda.synchronize(device)
            t0 = time.perf_counter()
            _ = flash_attn_func(q, k, v, causal=cfg.causal)
            torch.cuda.synchronize(device)
            t1 = time.perf_counter()
            times_ms.append((t1 - t0) * 1000.0)
    except torch.cuda.OutOfMemoryError as exc:
        torch.cuda.empty_cache()
        return {
            "status": "oom",
            "measured_runtime_ms": float("nan"),
            "measured_runtime_std_ms": float("nan"),
            "error": str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "measured_runtime_ms": float("nan"),
            "measured_runtime_std_ms": float("nan"),
            "error": f"{type(exc).__name__}: {exc}",
        }

    times_ms.sort()
    median = times_ms[len(times_ms) // 2] if times_ms else float("nan")
    std = (
        math.sqrt(sum((t - median) ** 2 for t in times_ms) / len(times_ms))
        if times_ms
        else float("nan")
    )

    return {
        "status": "ok",
        "measured_runtime_ms": median,
        "measured_runtime_std_ms": std,
        "times_ms": times_ms,
        "error": None,
    }


def measured_bottleneck_proxy(cfg: FA4Config) -> str:
    """White-box proxy for the dominant bottleneck on real hardware.

    Uses the uncalibrated baseline predictor's dominant-stage label as the proxy
    because real kernel timing alone does not expose hardware-counter-level
    breakdowns.
    """
    return baseline_predictor().predict(cfg)["predicted_bottleneck"]


def run_benchmark(
    configs: List[FA4Config],
    device: torch.device,
    progress_every: int = 50,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Measure all configs, skipping OOMs and errors, and report counts."""
    measurements: List[Dict[str, Any]] = []
    counts = {"ok": 0, "oom": 0, "error": 0}
    total = len(configs)
    t0 = time.time()
    for i, cfg in enumerate(configs):
        meas = measure_config(cfg, device)
        counts[meas["status"]] += 1
        record = {
            **config_to_dict(cfg),
            "status": meas["status"],
            "measured_runtime_ms": meas["measured_runtime_ms"],
            "measured_runtime_std_ms": meas["measured_runtime_std_ms"],
            "measured_bottleneck": (
                measured_bottleneck_proxy(cfg) if meas["status"] == "ok" else "unknown"
            ),
            "predicted_runtime_ms": (
                combined_predictor().predict(cfg)["predicted_runtime_ms"]
                if meas["status"] == "ok"
                else float("nan")
            ),
            "predicted_bottleneck": (
                combined_predictor().predict(cfg)["predicted_bottleneck"]
                if meas["status"] == "ok"
                else "unknown"
            ),
            "error": meas["error"],
        }
        measurements.append(record)
        if (i + 1) % progress_every == 0 or i == total - 1:
            elapsed = time.time() - t0
            print(
                f"Measured {i + 1}/{total} configs "
                f"(ok={counts['ok']}, oom={counts['oom']}, error={counts['error']}) "
                f"elapsed={elapsed:.1f}s"
            )
    return measurements, counts


def filter_ok(
    configs: List[FA4Config],
    measurements: List[Dict[str, Any]],
) -> Tuple[List[FA4Config], List[Dict[str, float]]]:
    """Return only configs/measurements that ran successfully."""
    ok_configs: List[FA4Config] = []
    ok_measurements: List[Dict[str, float]] = []
    for cfg, meas in zip(configs, measurements):
        if meas["status"] == "ok":
            ok_configs.append(cfg)
            ok_measurements.append(
                {
                    "measured_runtime_ms": float(meas["measured_runtime_ms"]),
                    "measured_bottleneck": str(meas["measured_bottleneck"]),
                }
            )
    return ok_configs, ok_measurements


def main(argv=None):  # type: ignore
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write all benchmark artifacts.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda:0",
        help="CUDA device to run measurements on.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260704,
        help="Random seed for config split.",
    )
    parser.add_argument(
        "--calibration-frac",
        type=float,
        default=0.20,
        help="Fraction of configs used for calibration.",
    )
    parser.add_argument(
        "--validation-frac",
        type=float,
        default=0.20,
        help="Fraction of configs used for held-out validation.",
    )
    parser.add_argument(
        "--calibration-rounds",
        type=int,
        default=2,
        help="Number of coordinate-descent calibration rounds for the combined model.",
    )
    parser.add_argument(
        "--skip-unsupported-precisions",
        action="store_true",
        default=True,
        help="Skip fp4 and other precisions not supported by the installed FA4 build.",
    )
    args = parser.parse_args(argv)

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device(args.device)
    torch.cuda.set_device(device)
    print(f"Using device: {device} ({torch.cuda.get_device_name(device)})")

    # Detect supported precisions.
    if args.skip_unsupported_precisions:
        precisions = [p for p in DESIGN_PRECISIONS if p in SUPPORTED_DTYPES]
        unsupported = [p for p in DESIGN_PRECISIONS if p not in SUPPORTED_DTYPES]
        if unsupported:
            print(f"Skipping unsupported precisions: {unsupported}")
    else:
        precisions = DESIGN_PRECISIONS

    # 1. Generate design matrix.
    configs = build_design_matrix(precisions=precisions)
    print(f"Generated {len(configs)} configs (precisions={precisions})")

    # 2. Split into calibration / validation / query.
    cal_configs, val_configs, query_configs = stratified_split(
        configs,
        calibration_frac=args.calibration_frac,
        validation_frac=args.validation_frac,
        seed=args.seed,
    )
    print(
        f"Split: cal={len(cal_configs)}, val={len(val_configs)}, query={len(query_configs)}"
    )

    # Save splits.
    split_dir = out_dir / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    for name, split in [
        ("calibration", cal_configs),
        ("validation", val_configs),
        ("query", query_configs),
    ]:
        path = split_dir / f"{name}_configs.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump([config_to_dict(c) for c in split], f, indent=2)

    # 3. Measure all configs in one pass, then split results.
    print("Starting real B200 measurements...")
    all_measurements, counts = run_benchmark(configs, device)

    raw_path = out_dir / "all_measurements.json"
    with raw_path.open("w", encoding="utf-8") as f:
        json.dump(all_measurements, f, indent=2)

    # CSV summary for humans.
    csv_path = out_dir / "all_measurements.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "batch",
            "heads",
            "seqlen",
            "head_dim",
            "causal",
            "precision",
            "status",
            "measured_runtime_ms",
            "measured_runtime_std_ms",
            "measured_bottleneck",
            "predicted_runtime_ms",
            "predicted_bottleneck",
            "error",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_measurements:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    # 4. Build per-split measurement lists using original indices.
    config_index = {id(c): i for i, c in enumerate(configs)}
    cal_idx = [config_index[id(c)] for c in cal_configs]
    val_idx = [config_index[id(c)] for c in val_configs]
    query_idx = [config_index[id(c)] for c in query_configs]

    cal_measurements_raw = [all_measurements[i] for i in cal_idx]
    val_measurements_raw = [all_measurements[i] for i in val_idx]
    query_measurements_raw = [all_measurements[i] for i in query_idx]

    cal_configs_ok, cal_measurements = filter_ok(
        cal_configs, cal_measurements_raw
    )
    val_configs_ok, val_measurements = filter_ok(
        val_configs, val_measurements_raw
    )
    query_configs_ok, query_measurements = filter_ok(
        query_configs, query_measurements_raw
    )

    print(
        f"OK counts: cal={len(cal_configs_ok)}, val={len(val_configs_ok)}, query={len(query_configs_ok)}"
    )

    # 5. Calibrate on calibration split only.
    cal_runtimes = [m["measured_runtime_ms"] for m in cal_measurements]
    if len(cal_runtimes) < 10:
        raise RuntimeError(
            f"Too few calibration measurements ({len(cal_runtimes)}); cannot calibrate."
        )

    print(f"Calibrating combined model on {len(cal_runtimes)} calibration configs...")
    combined, combined_params = calibrate_combined(
        cal_configs_ok,
        cal_runtimes,
        rounds=args.calibration_rounds,
    )
    ablation_params = calibrate_ablation_factors(cal_configs_ok, cal_runtimes)
    save_calibration(combined_params, ablation_params, out_dir / "calibration_params.json")
    print(f"Calibrated combined params: {combined_params}")

    # 6. Evaluate on held-out validation and query sets.
    results_val, _ = run_evaluation(
        cal_configs_ok,
        cal_measurements,
        val_configs_ok,
        val_measurements,
        combined_params,
        ablation_params,
    )
    results_query, _ = run_evaluation(
        cal_configs_ok,
        cal_measurements,
        query_configs_ok,
        query_measurements,
        combined_params,
        ablation_params,
    )

    baseline = baseline_predictor()
    baseline_val = evaluate_predictor(baseline, val_configs_ok, val_measurements)
    baseline_query = evaluate_predictor(baseline, query_configs_ok, query_measurements)
    results_val["baseline_fa4_roofline"] = baseline_val
    results_query["baseline_fa4_roofline"] = baseline_query

    save_evaluation(results_val, out_dir / "validation_metrics")
    save_evaluation(results_query, out_dir / "query_metrics")

    save_predictions(
        combined,
        val_configs_ok,
        val_measurements,
        out_dir / "combined_validation_predictions.csv",
    )
    save_predictions(
        combined,
        query_configs_ok,
        query_measurements,
        out_dir / "combined_query_predictions.csv",
    )

    combined_val = results_val["combined"]
    delta_mape = baseline_val["mape"] - combined_val["mape"]
    success = (
        combined_val["mape"] <= 25.0
        and combined_val["pct_within_30"] >= 75.0
        and combined_val["bottleneck_accuracy"] >= 75.0
        and delta_mape >= 5.0
    )

    # Decide status.
    if counts["error"] > max(5, len(configs) * 0.05):
        status = "inconclusive"
        status_reason = f"Too many errors ({counts['error']}) to trust the result."
    else:
        status = "supported" if success else "refuted"
        status_reason = (
            "Combined predictor meets all useful-improvement thresholds on real B200 measurements."
            if success
            else "Combined predictor fails at least one useful-improvement threshold on real B200 measurements."
        )

    experiment_result = {
        "status": status,
        "status_reason": status_reason,
        "hypothesis_id": "fa4-b200-whitebox-occupancy-tma-l2-precision-v1-real-hardware",
        "precisions_tested": precisions,
        "precisions_skipped": [p for p in DESIGN_PRECISIONS if p not in precisions],
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
        },
        "calibration_params": combined_params,
        "ablation_params": ablation_params,
        "validation_metrics": {
            "baseline_mape": baseline_val["mape"],
            "combined_mape": combined_val["mape"],
            "delta_mape_pp": delta_mape,
            "max_ape": combined_val["max_ape"],
            "pct_within_30": combined_val["pct_within_30"],
            "bottleneck_accuracy": combined_val["bottleneck_accuracy"],
            "n_configs": combined_val["n_configs"],
            "per_model": results_val,
        },
        "query_metrics": {
            "baseline_mape": baseline_query["mape"],
            "combined_mape": results_query["combined"]["mape"],
            "delta_mape_pp": baseline_query["mape"] - results_query["combined"]["mape"],
            "max_ape": results_query["combined"]["max_ape"],
            "pct_within_30": results_query["combined"]["pct_within_30"],
            "bottleneck_accuracy": results_query["combined"]["bottleneck_accuracy"],
            "n_configs": results_query["combined"]["n_configs"],
            "per_model": results_query,
        },
        "environment": {
            "device_name": torch.cuda.get_device_name(device),
            "cuda_version": torch.version.cuda,
            "torch_version": torch.__version__,
        },
        "caveats": [
            "measured_bottleneck is a white-box proxy from the uncalibrated baseline predictor; hardware counters were not collected.",
            "fp4 precision is not supported by the installed FA4 build and was skipped.",
        ],
    }

    with (out_dir / "experiment_result.json").open("w", encoding="utf-8") as f:
        json.dump(experiment_result, f, indent=2)

    print(json.dumps(experiment_result, indent=2))
    print(f"Experiment status: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
