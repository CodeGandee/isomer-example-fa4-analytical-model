"""Improved white-box predictor with explicit launch-overhead terms.

The model keeps the algorithmic workload breakdown from `predictor.py` but adds:

* a fixed launch/grid overhead;
* a per-output-tile overhead that captures scheduler/dispatch cost;
* an optional short-sequence overhead for the smallest configs;
* a richer, bounded calibration grid so real-hardware efficiency factors can be
  recovered from the calibration split alone.

All correction factors remain multiplicative and physically scoped; no black-box
fit to measured runtime is used.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Tuple

from fa4_b200_predictor.constants import B200, B200Spec
from fa4_b200_predictor.predictor import (
    FA4Config,
    compute_workload,
    effective_hbm_bw,
    effective_l2_bw,
    effective_tma_bw,
    occupancy_factor,
    tile_size_for_config,
)


@dataclass(frozen=True)
class ImprovedPredictor:
    """White-box predictor with explicit launch/scheduler overhead."""

    name: str = "improved"
    spec: B200Spec = B200
    hbm_factor: float = 1.0
    l2_factor: float = 1.0
    smem_factor: float = 1.0
    tma_factor: float = 1.0
    mma_efficiency: float = 1.0
    mufu_efficiency: float = 1.0
    fp8_mma_boost: float = 1.0
    launch_fixed_us: float = 0.0
    launch_per_tile_us: float = 0.0
    small_overhead_us: float = 0.0
    small_seqlen_threshold: int = 2048
    # NCU-guided slack for the white-box -> NCU bottleneck mapping.  If the
    # dominant memory time is within this fraction of the dominant compute time,
    # the config is labelled compute-bound (matching NCU SpeedOfLight behaviour).
    bottleneck_mem_slack: float = 0.0

    def total_tiles(self, cfg: FA4Config) -> int:
        """Number of output tiles for the config."""
        block_m, block_n = tile_size_for_config(cfg)
        tiles_m = math.ceil(cfg.seqlen / block_m)
        tiles_n = math.ceil(cfg.seqlen / block_n)
        return cfg.batch * cfg.heads * tiles_m * tiles_n

    def predict(self, cfg: FA4Config) -> Dict[str, Any]:
        """Return runtime estimate and per-stage diagnostics."""
        workload = compute_workload(cfg)
        occ = occupancy_factor(cfg, self.spec)
        prec = cfg.normalized_precision

        # Compute MMA and MUFU times inline so we can apply a precision-specific
        # FP8 boost without mutating the shared B200Spec constants.
        mma_rate_per_sm = self.spec.mma_throughput_per_sm_per_clock[prec]
        if prec == "fp8":
            mma_rate_per_sm *= self.fp8_mma_boost
        mma_total_rate = (
            mma_rate_per_sm
            * self.spec.num_sms
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * occ
            * self.mma_efficiency
        )
        mma_t = (workload.mma_flops / max(mma_total_rate, 1.0)) * 1e6

        mufu_rate_per_sm = self.spec.mufu_throughput_per_sm_per_clock[prec]
        mufu_total_rate = (
            mufu_rate_per_sm
            * self.spec.num_sms
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * occ
            * self.mufu_efficiency
        )
        mufu_t = (workload.exp_ops / max(mufu_total_rate, 1.0)) * 1e6

        hbm_bw = effective_hbm_bw(workload.hbm_bytes, self.spec, self.hbm_factor)
        l2_bw = effective_l2_bw(workload.l2_bytes, self.spec, self.l2_factor)
        smem_bw = (
            self.spec.smem_bandwidth_bytes_per_clock_per_sm
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * self.spec.num_sms
            * self.smem_factor
        )
        tma_bw = effective_tma_bw(workload.tma_bytes, self.spec, self.tma_factor)

        hbm_t = workload.hbm_bytes / max(hbm_bw, 1.0)
        l2_t = workload.l2_bytes / max(l2_bw, 1.0)
        smem_t = workload.smem_bytes / max(smem_bw, 1.0)
        tma_t = workload.tma_bytes / max(tma_bw, 1.0)
        mem_t = max(hbm_t, l2_t, smem_t, tma_t) * 1e6

        base_us = max(mma_t, mufu_t, mem_t)

        tiles = self.total_tiles(cfg)
        overhead_us = self.launch_fixed_us + self.launch_per_tile_us * tiles
        if cfg.seqlen <= self.small_seqlen_threshold:
            overhead_us += self.small_overhead_us

        runtime_ms = (base_us + overhead_us) / 1000.0

        label = self._bottleneck_label(
            hbm_t * 1e6,
            l2_t * 1e6,
            smem_t * 1e6,
            tma_t * 1e6,
            mma_t,
            mufu_t,
        )

        return {
            "predicted_runtime_ms": runtime_ms,
            "predicted_bottleneck": label,
            "mma_time_us": mma_t,
            "mufu_time_us": mufu_t,
            "hbm_time_us": hbm_t * 1e6,
            "l2_time_us": l2_t * 1e6,
            "smem_time_us": smem_t * 1e6,
            "tma_time_us": tma_t * 1e6,
            "base_time_us": base_us,
            "launch_overhead_us": overhead_us,
            "occupancy_fraction": occ,
            "total_tiles": tiles,
        }

    def _bottleneck_label(
        self,
        hbm_time_us: float,
        l2_time_us: float,
        smem_time_us: float,
        tma_time_us: float,
        mma_time_us: float,
        mufu_time_us: float,
    ) -> str:
        """Dominant bottleneck label with NCU-guided compute bias.

        When the dominant memory time is within ``bottleneck_mem_slack`` of the
        dominant compute time, the config is classified as compute-bound.  This
        mirrors the empirical observation that NCU SpeedOfLight labels every
        profiled FA4 config as compute-bound even when the raw white-box memory
        estimate is comparable or slightly larger.
        """
        compute_time = max(mma_time_us, mufu_time_us)
        mem_time = max(hbm_time_us, l2_time_us, smem_time_us, tma_time_us)
        if mem_time <= compute_time * (1.0 + self.bottleneck_mem_slack):
            return "mma" if mma_time_us >= mufu_time_us else "mufu"

        times = {
            "hbm": hbm_time_us,
            "l2": l2_time_us,
            "smem": smem_time_us,
            "tma": tma_time_us,
        }
        return max(times, key=times.get)  # type: ignore[arg-type]

    def to_params(self) -> Dict[str, Any]:
        """Serialisable calibration parameters."""
        return {
            "hbm_factor": self.hbm_factor,
            "l2_factor": self.l2_factor,
            "smem_factor": self.smem_factor,
            "tma_factor": self.tma_factor,
            "mma_efficiency": self.mma_efficiency,
            "mufu_efficiency": self.mufu_efficiency,
            "fp8_mma_boost": self.fp8_mma_boost,
            "launch_fixed_us": self.launch_fixed_us,
            "launch_per_tile_us": self.launch_per_tile_us,
            "small_overhead_us": self.small_overhead_us,
            "small_seqlen_threshold": self.small_seqlen_threshold,
            "bottleneck_mem_slack": self.bottleneck_mem_slack,
        }

    @classmethod
    def from_params(cls, params: Dict[str, Any], name: str = "improved") -> "ImprovedPredictor":
        """Rebuild an ImprovedPredictor from saved parameters."""
        return cls(
            name=name,
            spec=B200,
            hbm_factor=params.get("hbm_factor", 1.0),
            l2_factor=params.get("l2_factor", 1.0),
            smem_factor=params.get("smem_factor", 1.0),
            tma_factor=params.get("tma_factor", 1.0),
            mma_efficiency=params.get("mma_efficiency", 1.0),
            mufu_efficiency=params.get("mufu_efficiency", 1.0),
            fp8_mma_boost=params.get("fp8_mma_boost", 1.0),
            launch_fixed_us=params.get("launch_fixed_us", 0.0),
            launch_per_tile_us=params.get("launch_per_tile_us", 0.0),
            small_overhead_us=params.get("small_overhead_us", 0.0),
            small_seqlen_threshold=params.get("small_seqlen_threshold", 2048),
            bottleneck_mem_slack=params.get("bottleneck_mem_slack", 0.0),
        )


def mape(predicted: List[float], measured: List[float]) -> float:
    """Mean absolute percentage error."""
    errors = []
    for p, m in zip(predicted, measured):
        denom = max(abs(m), 1e-6)
        errors.append(abs(p - m) / denom * 100.0)
    return sum(errors) / len(errors) if errors else float("inf")


def _build_predictor(params: Dict[str, float]) -> ImprovedPredictor:
    """Construct an ImprovedPredictor from a parameter dictionary."""
    return ImprovedPredictor(
        name="improved",
        spec=B200,
        hbm_factor=params.get("hbm_factor", 0.80),
        l2_factor=params.get("l2_factor", 0.80),
        smem_factor=params.get("smem_factor", 0.90),
        tma_factor=params.get("tma_factor", 0.80),
        mma_efficiency=params.get("mma_efficiency", 0.65),
        mufu_efficiency=params.get("mufu_efficiency", 0.80),
        fp8_mma_boost=params.get("fp8_mma_boost", 1.0),
        launch_fixed_us=params.get("launch_fixed_us", 80.0),
        launch_per_tile_us=params.get("launch_per_tile_us", 0.0),
        small_overhead_us=params.get("small_overhead_us", 0.0),
        small_seqlen_threshold=params.get("small_seqlen_threshold", 2048),
        bottleneck_mem_slack=params.get("bottleneck_mem_slack", 0.0),
    )


IMPROVED_CALIBRATION_BOUNDS: Dict[str, Tuple[float, float]] = {
    "hbm_factor": (0.20, 15.00),
    "l2_factor": (0.20, 10.00),
    "smem_factor": (0.20, 10.00),
    "tma_factor": (0.20, 15.00),
    "mma_efficiency": (0.20, 2.00),
    "mufu_efficiency": (0.20, 2.00),
    "fp8_mma_boost": (0.50, 2.50),
    "launch_fixed_us": (0.0, 200.0),
    "launch_per_tile_us": (0.0, 0.1),
    "small_overhead_us": (0.0, 50.0),
}


def _grid_for_param(key: str) -> List[float]:
    """Bounded grid used for each calibration parameter."""
    grids: Dict[str, List[float]] = {
        "hbm_factor": [0.40, 0.80, 1.50, 3.00, 5.00, 8.00, 12.00, 15.00],
        "l2_factor": [0.30, 0.70, 1.50, 3.00, 6.00, 10.00],
        "smem_factor": [0.50, 1.00, 2.00, 4.00, 8.00, 10.00],
        "tma_factor": [0.30, 0.70, 1.50, 3.00, 5.00, 8.00, 12.00, 15.00],
        "mma_efficiency": [0.30, 0.50, 0.70, 0.90, 1.10, 1.30, 1.50, 1.75, 2.00],
        "mufu_efficiency": [0.30, 0.50, 0.70, 0.90, 1.10, 1.30, 1.50],
        "fp8_mma_boost": [0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50],
        "launch_fixed_us": [0.0, 10.0, 20.0, 40.0, 60.0, 80.0, 100.0, 150.0, 200.0],
        "launch_per_tile_us": [0.0, 0.001, 0.002, 0.005, 0.01, 0.02],
        "small_overhead_us": [0.0, 5.0, 10.0, 20.0, 30.0, 50.0],
    }
    lo, hi = IMPROVED_CALIBRATION_BOUNDS[key]
    return [max(lo, min(hi, v)) for v in grids[key]]


def calibrate_improved(
    configs: List[FA4Config],
    measurements: List[float],
    rounds: int = 2,
) -> Tuple[ImprovedPredictor, Dict[str, float]]:
    """Calibrate the improved predictor on the calibration split only."""
    if len(configs) != len(measurements):
        raise ValueError("configs and measurements must have the same length")

    params: Dict[str, float] = {
        "hbm_factor": 0.80,
        "l2_factor": 0.80,
        "smem_factor": 0.90,
        "tma_factor": 0.80,
        "mma_efficiency": 0.65,
        "mufu_efficiency": 0.80,
        "fp8_mma_boost": 1.50,
        "launch_fixed_us": 80.0,
        "launch_per_tile_us": 0.0,
        "small_overhead_us": 0.0,
        "small_seqlen_threshold": 2048,
    }

    order = [
        "mma_efficiency",
        "fp8_mma_boost",
        "hbm_factor",
        "tma_factor",
        "launch_fixed_us",
        "mufu_efficiency",
        "launch_per_tile_us",
        "small_overhead_us",
        "l2_factor",
        "smem_factor",
    ]

    best_mape = float("inf")
    for _ in range(rounds):
        improved = False
        for key in order:
            grid = _grid_for_param(key)
            for v in grid:
                candidate = dict(params)
                candidate[key] = v
                preds = [_build_predictor(candidate).predict(c)["predicted_runtime_ms"] for c in configs]
                err = mape(preds, measurements)
                if err < best_mape:
                    best_mape = err
                    params[key] = v
                    improved = True
        if not improved:
            break

    return _build_predictor(params), params


def calibrate_bottleneck_threshold(
    predictor: ImprovedPredictor,
    configs: List[FA4Config],
    measurements: List[Dict[str, Any]],
) -> float:
    """Calibrate ``bottleneck_mem_slack`` on NCU-labelled calibration configs.

    The slack is set to the smallest value that makes every NCU compute-bound
    calibration config be labelled compute-bound by the white-box model.  This
    is an NCU-guided correction of the memory-vs-compute balance used only for
    bottleneck diagnosis; predicted runtimes are unchanged because they still
    use ``max(compute, memory)``.
    """
    ncu_rows = [
        (cfg, meas)
        for cfg, meas in zip(configs, measurements)
        if meas.get("ncu_bottleneck") in ("compute", "memory")
    ]
    if not ncu_rows:
        return 0.0

    required_slack = 0.0
    for cfg, meas in ncu_rows:
        pred = predictor.predict(cfg)
        compute_time = max(pred["mma_time_us"], pred["mufu_time_us"])
        mem_time = max(
            pred["hbm_time_us"],
            pred["l2_time_us"],
            pred["smem_time_us"],
            pred["tma_time_us"],
        )
        if meas["ncu_bottleneck"] == "compute" and compute_time > 0.0:
            required_slack = max(required_slack, mem_time / compute_time - 1.0)
        elif meas["ncu_bottleneck"] == "memory" and mem_time > 0.0:
            # For memory-bound configs we must keep the slack below the flip
            # point, so no action is needed here; the grid search below enforces
            # accuracy on both classes.
            pass

    # Fine-grained grid search around the exact bound to maximise NCU accuracy
    # on the calibration subset while preferring the smallest slack that still
    # reaches the maximum.
    best_slack = max(0.0, required_slack)
    best_acc = 0.0
    for slack in [0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]:
        if slack < required_slack:
            continue
        refined = replace(predictor, bottleneck_mem_slack=slack)
        correct = sum(
            1
            for cfg, meas in ncu_rows
            if _coarse_bottleneck(refined.predict(cfg)["predicted_bottleneck"])
            == meas["ncu_bottleneck"]
        )
        acc = correct / len(ncu_rows)
        if acc > best_acc or (acc == best_acc and slack < best_slack):
            best_acc = acc
            best_slack = slack

    return best_slack


def _coarse_bottleneck(label: str) -> str:
    """Map fine-grained white-box labels to the NCU compute/memory binary."""
    return "compute" if label in ("mma", "mufu") else "memory"


def default_improved_predictor() -> ImprovedPredictor:
    """Initial improved predictor before calibration."""
    return _build_predictor({})
