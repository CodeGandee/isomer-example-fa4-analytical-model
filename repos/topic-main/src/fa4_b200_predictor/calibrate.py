"""White-box calibration of bounded correction factors on the calibration split."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from fa4_b200_predictor.constants import B200, B200Spec, CALIBRATION_BOUNDS
from fa4_b200_predictor.predictor import (
    FA4Config,
    Predictor,
    combined_predictor,
    occupancy_only_predictor,
    precision_only_predictor,
    tma_l2_predictor,
)


def mape(predicted: List[float], measured: List[float]) -> float:
    """Mean absolute percentage error, clipped at 0.1% to avoid divide-by-zero."""
    errors = []
    for p, m in zip(predicted, measured):
        denom = max(abs(m), 1e-6)
        errors.append(abs(p - m) / denom * 100.0)
    return sum(errors) / len(errors) if errors else float("inf")


def grid_search_1d(
    param_name: str,
    values: List[float],
    predictor_builder: Callable[..., Predictor],
    configs: List[FA4Config],
    measurements: List[float],
) -> Tuple[float, float]:
    """Search one bounded parameter to minimize calibration MAPE."""
    best_val, best_mape = values[0], float("inf")
    for v in values:
        pred = predictor_builder(**{param_name: v})
        preds = [pred.predict(c)["predicted_runtime_ms"] for c in configs]
        err = mape(preds, measurements)
        if err < best_mape:
            best_mape = err
            best_val = v
    return best_val, best_mape


def calibrate_combined(
    configs: List[FA4Config],
    measurements: List[float],
    spec: B200Spec = B200,
    rounds: int = 2,
) -> Tuple[Predictor, Dict[str, float]]:
    """Calibrate the combined predictor using only bounded white-box factors."""
    if len(configs) != len(measurements):
        raise ValueError("configs and measurements must have the same length")

    # Reasonable initial guess from the uncalibrated combined predictor.
    params: Dict[str, float] = {
        "hbm_factor": 0.80,
        "mma_efficiency": 0.85,
        "mufu_efficiency": 0.85,
        "launch_overhead_us": 2.0,
    }

    # Candidate grids for each factor, centered on realistic B200 sustained values.
    grids = {
        "hbm_factor": [0.60, 0.70, 0.80, 0.85, 0.90, 0.95],
        "mma_efficiency": [0.70, 0.80, 0.85, 0.90, 0.95],
        "mufu_efficiency": [0.70, 0.80, 0.85, 0.90, 0.95],
        "launch_overhead_us": [0.0, 0.5, 1.0, 2.0, 3.0, 5.0],
    }

    def build(**overrides: float) -> Predictor:
        merged = {**params, **overrides}
        return combined_predictor(
            spec=spec,
            hbm_factor=merged.get("hbm_factor", 0.80),
            l2_factor=0.70,
            tma_factor=0.65,
            smem_factor=0.90,
            mma_efficiency=merged.get("mma_efficiency", 0.85),
            mufu_efficiency=merged.get("mufu_efficiency", 0.85),
            launch_overhead_us=merged.get("launch_overhead_us", 2.0),
        )

    best_mape = float("inf")
    for _ in range(rounds):
        improved = False
        for key, grid in grids.items():
            lo, hi = CALIBRATION_BOUNDS[key]
            clipped_grid = [max(lo, min(hi, v)) for v in grid]
            best_v, err = grid_search_1d(key, clipped_grid, build, configs, measurements)
            if abs(params[key] - best_v) > 1e-6 or err < best_mape:
                params[key] = best_v
                best_mape = err
                improved = True
        if not improved:
            break

    return build(), params


def calibrate_ablation_factors(
    configs: List[FA4Config],
    measurements: List[float],
    spec: B200Spec = B200,
) -> Dict[str, Dict[str, float]]:
    """Calibrate each ablation model with its own bounded correction factors."""
    results: Dict[str, Dict[str, float]] = {}

    # Occupancy-only: only mma/mufu efficiency matter because occupancy is computed.
    occ_pred = occupancy_only_predictor(spec)
    occ_preds = [occ_pred.predict(c)["predicted_runtime_ms"] for c in configs]
    results["occupancy_only"] = {"mma_efficiency": 1.0, "mufu_efficiency": 1.0}
    # Occupancy model already has the correction baked into occupancy_fraction.
    # We still allow a small efficiency adjustment to avoid double counting.
    best_eff = 1.0
    best_err = mape(occ_preds, measurements)
    for eff in [0.75, 0.85, 0.90, 0.95, 1.00]:
        p = occupancy_only_predictor(spec)
        p.mma_efficiency = eff
        p.mufu_efficiency = eff
        preds = [p.predict(c)["predicted_runtime_ms"] for c in configs]
        err = mape(preds, measurements)
        if err < best_err:
            best_err = err
            best_eff = eff
    results["occupancy_only"] = {"mma_efficiency": best_eff, "mufu_efficiency": best_eff}

    # TMA/L2 effective bandwidth.
    best = {"hbm_factor": 0.80, "l2_factor": 0.70, "tma_factor": 0.65}

    def build_tma_l2(**kw):
        merged = {**best, **kw}
        return tma_l2_predictor(
            spec=spec,
            hbm_factor=merged.get("hbm_factor", 0.75),
            l2_factor=merged.get("l2_factor", 0.60),
            tma_factor=merged.get("tma_factor", 0.55),
        )

    for key, grid in [
        ("hbm_factor", [0.60, 0.70, 0.80, 0.85, 0.90, 0.95]),
        ("l2_factor", [0.45, 0.55, 0.65, 0.70, 0.75, 0.80]),
        ("tma_factor", [0.40, 0.50, 0.60, 0.65, 0.70, 0.75]),
    ]:
        lo, hi = CALIBRATION_BOUNDS[key]
        clipped_grid = [max(lo, min(hi, v)) for v in grid]
        best_v, _ = grid_search_1d(
            key,
            clipped_grid,
            build_tma_l2,
            configs,
            measurements,
        )
        best[key] = best_v
    results["tma_l2_effective_bw"] = best

    # Precision-only.
    best_pe = 1.0
    best_err_pe = float("inf")
    for eff in [0.75, 0.85, 0.90, 0.95, 1.00]:
        p = precision_only_predictor(spec)
        p.mma_efficiency = eff
        p.mufu_efficiency = eff
        preds = [p.predict(c)["predicted_runtime_ms"] for c in configs]
        err = mape(preds, measurements)
        if err < best_err_pe:
            best_err_pe = err
            best_pe = eff
    results["precision_only"] = {"mma_efficiency": best_pe, "mufu_efficiency": best_pe}

    return results


def save_calibration(
    params: Dict[str, float],
    ablation_params: Dict[str, Dict[str, float]],
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "combined": params,
        "ablations": ablation_params,
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
