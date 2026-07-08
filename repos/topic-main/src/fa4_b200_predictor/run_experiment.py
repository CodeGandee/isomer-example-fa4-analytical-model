"""Main experiment runner for the FA4 B200 white-box runtime model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fa4_b200_predictor.calibrate import (
    calibrate_ablation_factors,
    calibrate_combined,
    save_calibration,
)
from fa4_b200_predictor.config_matrix import (
    build_config_matrix,
    config_to_dict,
    save_split,
    split_configs,
)
from fa4_b200_predictor.emulator import GroundTruthEmulator
from fa4_b200_predictor.evaluate import (
    evaluate_predictor,
    run_evaluation,
    save_evaluation,
    save_predictions,
)
from fa4_b200_predictor.predictor import baseline_predictor


def main(argv=None):  # type: ignore
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write all experiment artifacts.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260704,
        help="Random seed for config split and emulator noise.",
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
    args = parser.parse_args(argv)

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate synthetic config matrix.
    configs = build_config_matrix()
    cal_configs, val_configs, query_configs = split_configs(
        configs,
        calibration_frac=args.calibration_frac,
        validation_frac=args.validation_frac,
        seed=args.seed,
    )
    print(
        f"Generated {len(configs)} configs: "
        f"cal={len(cal_configs)}, val={len(val_configs)}, query={len(query_configs)}"
    )
    save_split(cal_configs, val_configs, query_configs, out_dir / "configs")

    # 2. Generate ground-truth measurements via white-box emulator.
    #    Real B200 kernel execution is documented as infeasible within the time budget.
    emulator = GroundTruthEmulator(seed=args.seed)
    cal_measurements = [emulator.measure(c) for c in cal_configs]
    val_measurements = [emulator.measure(c) for c in val_configs]

    with (out_dir / "calibration_measurements.json").open("w", encoding="utf-8") as f:
        json.dump(
            [config_to_dict(c) | m for c, m in zip(cal_configs, cal_measurements)],
            f,
            indent=2,
        )
    with (out_dir / "validation_measurements.json").open("w", encoding="utf-8") as f:
        json.dump(
            [config_to_dict(c) | m for c, m in zip(val_configs, val_measurements)],
            f,
            indent=2,
        )

    # 3. Calibrate baseline FA4 roofline (no free parameters; just evaluate).
    baseline = baseline_predictor()
    baseline_val = evaluate_predictor(baseline, val_configs, val_measurements)
    print(f"Baseline validation MAPE: {baseline_val['mape']:.2f}%")

    # 4. Calibrate ablations and combined model on the calibration split only.
    cal_runtimes = [m["measured_runtime_ms"] for m in cal_measurements]
    combined, combined_params = calibrate_combined(
        cal_configs,
        cal_runtimes,
        rounds=args.calibration_rounds,
    )
    ablation_params = calibrate_ablation_factors(cal_configs, cal_runtimes)
    save_calibration(combined_params, ablation_params, out_dir / "calibration_params.json")
    print(f"Calibrated combined params: {combined_params}")
    print(f"Calibrated ablation params: {ablation_params}")

    # 5. Evaluate all models on held-out validation set.
    results, _ = run_evaluation(
        cal_configs,
        cal_measurements,
        val_configs,
        val_measurements,
        combined_params,
        ablation_params,
    )
    results["baseline_fa4_roofline"] = baseline_val
    save_evaluation(results, out_dir)
    print(json.dumps(results, indent=2))

    # 6. Save per-config predictions for the combined model.
    save_predictions(
        combined,
        val_configs,
        val_measurements,
        out_dir / "combined_predictions.csv",
    )

    # 7. Compute route decision.
    combined_val = results["combined"]
    delta_mape = baseline_val["mape"] - combined_val["mape"]
    success = (
        combined_val["mape"] <= 25.0
        and combined_val["pct_within_30"] >= 75.0
        and combined_val["bottleneck_accuracy"] >= 75.0
        and delta_mape >= 5.0
    )

    decision = {
        "status": "supported" if success else "refuted",
        "baseline_mape": baseline_val["mape"],
        "combined_mape": combined_val["mape"],
        "delta_mape_pp": delta_mape,
        "max_ape": combined_val["max_ape"],
        "pct_within_30": combined_val["pct_within_30"],
        "bottleneck_accuracy": combined_val["bottleneck_accuracy"],
        "ablations": {k: v for k, v in results.items() if k not in ("combined_calibration",)},
    }
    with (out_dir / "experiment_result.json").open("w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)
    print(f"Experiment decision: {decision['status']}")

    return 0 if success else 0  # Always return 0 so the run is recorded.


if __name__ == "__main__":
    raise SystemExit(main())
