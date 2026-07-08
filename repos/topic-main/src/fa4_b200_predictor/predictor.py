"""White-box analytical predictors for Flash Attention 4 forward pass on B200.

All predictors are intentionally white-box: they estimate runtime from algorithm
quantities (FLOPs, bytes, op counts) and hardware throughput, never from a
black-box fit to measured runtime.  Calibration factors are bounded
multiplicative corrections with clear physical meaning.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from fa4_b200_predictor.constants import (
    B200,
    B200Spec,
    DEFAULT_TILE_SIZES,
    PRECISION_ALIASES,
    TILE,
)


@dataclass(frozen=True)
class FA4Config:
    """Input configuration for one forward-pass prediction."""

    batch: int
    heads: int
    seqlen: int
    head_dim: int
    causal: bool
    precision: str

    @property
    def normalized_precision(self) -> str:
        return PRECISION_ALIASES.get(self.precision.lower(), self.precision.lower())


@dataclass(frozen=True)
class FA4Workload:
    """Algorithmic workload quantities for one FA4 forward pass."""

    # Effective sequence length factor after causal masking.
    seq_factor: float
    # Total MMA FLOPs (Q@K^T + P@V) in the FA4 regime.
    mma_flops: float
    # Exponential / softmax element counts.
    exp_ops: float
    # HBM bytes moved (Q, K, V, O reads/writes).
    hbm_bytes: float
    # L2 bytes (estimated traffic between SMs and L2).
    l2_bytes: float
    # Shared-memory bytes (inter-SMEM traffic inside kernel).
    smem_bytes: float
    # TMA transfer bytes.
    tma_bytes: float


def compute_workload(cfg: FA4Config) -> FA4Workload:
    """Compute white-box algorithm quantities from a configuration."""
    b, h, s, d = cfg.batch, cfg.heads, cfg.seqlen, cfg.head_dim
    causal = cfg.causal
    bpe = TILE.bytes_per_element[cfg.normalized_precision]

    seq_factor = 0.5 if causal else 1.0

    # FA4 forward FLOPs: 4 * B * H * S^2 * D scaled by causal factor.
    mma_flops = 4.0 * b * h * (s * s) * d * seq_factor

    # Softmax exp ops: one exp per (b, h, s, s) attention score plus row reductions.
    exp_ops = 2.0 * b * h * (s * s) * seq_factor

    # HBM traffic: read Q, K, V; write O; plus tile-sized intermediates.
    hbm_bytes = bpe * b * h * s * d * 4.0

    # L2 traffic: tiles streamed through L2 (Q/K tiles, partial O).
    l2_bytes = bpe * b * h * s * d * 6.0 * seq_factor

    # SMEM traffic: Q/K/V tiles staged multiple times per output block.
    smem_bytes = b * h * s * d * 8.0 * seq_factor

    # TMA traffic: bulk async copies for Q/K/V tiles plus reductions.
    tma_bytes = bpe * b * h * s * d * 2.5 * seq_factor

    return FA4Workload(
        seq_factor=seq_factor,
        mma_flops=mma_flops,
        exp_ops=exp_ops,
        hbm_bytes=hbm_bytes,
        l2_bytes=l2_bytes,
        smem_bytes=smem_bytes,
        tma_bytes=tma_bytes,
    )


def tile_size_for_config(cfg: FA4Config) -> Tuple[int, int]:
    """Return (block_m, block_n) for the configuration."""
    return DEFAULT_TILE_SIZES.get(cfg.head_dim, (TILE.block_m, TILE.block_n))


def estimate_active_warps(cfg: FA4Config, spec: B200Spec = B200) -> float:
    """Estimate active warps across the device limited by tile geometry."""
    block_m, block_n = tile_size_for_config(cfg)
    # Number of output tiles.
    tiles_m = math.ceil(cfg.seqlen / block_m)
    tiles_n = math.ceil(cfg.seqlen / block_n)
    total_tiles = cfg.batch * cfg.heads * tiles_m * tiles_n

    # Warps required per tile (FA4 typically uses 4 warps per tile).
    warps_per_tile = 4
    required_warps = total_tiles * warps_per_tile

    # Maximum resident warps on the device.
    max_device_warps = spec.num_sms * spec.max_warps_per_sm

    active_warps = min(required_warps, max_device_warps)
    return max(active_warps, 1.0)


def occupancy_factor(cfg: FA4Config, spec: B200Spec = B200) -> float:
    """Fraction of theoretical throughput reachable given occupancy."""
    active_warps = estimate_active_warps(cfg, spec)
    max_device_warps = spec.num_sms * spec.max_warps_per_sm
    # Throughput scales roughly with sqrt of occupancy at low occupancy, then saturates.
    frac = active_warps / max_device_warps
    return min(1.0, math.sqrt(max(0.0, frac)) * 0.95 + 0.05)


def effective_hbm_bw(
    transfer_bytes: float,
    spec: B200Spec = B200,
    factor: float = 1.0,
) -> float:
    """HBM effective bandwidth decreases for small transfers due to latency."""
    peak = spec.peak_hbm_bw_gbps * 1e9
    # Latency term: fixed startup per transfer, amortized over bytes.
    transfer_gb = transfer_bytes / 1e9
    efficiency = max(0.1, 1.0 - 0.15 / max(transfer_gb, 0.001))
    return peak * efficiency * factor


def effective_l2_bw(
    transfer_bytes: float,
    spec: B200Spec = B200,
    factor: float = 1.0,
) -> float:
    """L2 bandwidth is higher but still transfer-size dependent."""
    peak = spec.peak_l2_bw_gbps * 1e9
    transfer_gb = transfer_bytes / 1e9
    efficiency = max(0.1, 1.0 - 0.05 / max(transfer_gb, 0.001))
    return peak * efficiency * factor


def effective_tma_bw(
    transfer_bytes: float,
    spec: B200Spec = B200,
    factor: float = 1.0,
) -> float:
    """TMA effective throughput includes a base latency plus linear term."""
    latency_s = spec.tma_base_latency_us * 1e-6
    throughput_bytes_s = spec.tma_bytes_per_ns * 1e9 * factor
    return transfer_bytes / max(
        latency_s + transfer_bytes / max(throughput_bytes_s, 1.0),
        transfer_bytes / (spec.peak_hbm_bw_gbps * 1e9),
    )


def mma_time_us(
    cfg: FA4Config,
    workload: FA4Workload,
    spec: B200Spec = B200,
    occupancy_factor: float = 1.0,
    mma_efficiency: float = 1.0,
) -> float:
    """Time (microseconds) for Tensor Core MMA work."""
    prec = cfg.normalized_precision
    rate_per_sm = spec.mma_throughput_per_sm_per_clock[prec]
    total_rate = rate_per_sm * spec.num_sms * spec.peak_sm_clock_mhz * 1e6
    effective_rate = total_rate * occupancy_factor * mma_efficiency
    return (workload.mma_flops / max(effective_rate, 1.0)) * 1e6


def mufu_time_us(
    cfg: FA4Config,
    workload: FA4Workload,
    spec: B200Spec = B200,
    occupancy_factor: float = 1.0,
    mufu_efficiency: float = 1.0,
) -> float:
    """Time (microseconds) for MUFU exponential/softmax work."""
    prec = cfg.normalized_precision
    rate_per_sm = spec.mufu_throughput_per_sm_per_clock[prec]
    total_rate = rate_per_sm * spec.num_sms * spec.peak_sm_clock_mhz * 1e6
    effective_rate = total_rate * occupancy_factor * mufu_efficiency
    return (workload.exp_ops / max(effective_rate, 1.0)) * 1e6


def memory_time_us(
    workload: FA4Workload,
    hbm_factor: float = 1.0,
    l2_factor: float = 1.0,
    smem_factor: float = 1.0,
    tma_factor: float = 1.0,
    spec: B200Spec = B200,
) -> float:
    """Time (microseconds) for memory traffic, taking the dominant bottleneck."""
    hbm_time = workload.hbm_bytes / max(
        effective_hbm_bw(workload.hbm_bytes, spec, hbm_factor), 1.0
    )
    l2_time = workload.l2_bytes / max(
        effective_l2_bw(workload.l2_bytes, spec, l2_factor), 1.0
    )
    smem_time = workload.smem_bytes / max(
        spec.smem_bandwidth_bytes_per_clock_per_sm * spec.peak_sm_clock_mhz * 1e6 * spec.num_sms * smem_factor,
        1.0,
    )
    tma_time = workload.tma_bytes / max(
        effective_tma_bw(workload.tma_bytes, spec, tma_factor), 1.0
    )
    return max(hbm_time, l2_time, smem_time, tma_time) * 1e6


def bottleneck_label(
    cfg: FA4Config,
    workload: FA4Workload,
    hbm_time: float,
    l2_time: float,
    smem_time: float,
    tma_time: float,
    mma_time: float,
    mufu_time: float,
) -> str:
    """Return the dominant bottleneck label."""
    times = {
        "hbm": hbm_time,
        "l2": l2_time,
        "smem": smem_time,
        "tma": tma_time,
        "mma": mma_time,
        "mufu": mufu_time,
    }
    return max(times, key=times.get)  # type: ignore[arg-type]


class Predictor:
    """Base white-box predictor."""

    def __init__(
        self,
        name: str,
        spec: B200Spec = B200,
        hbm_factor: float = 1.0,
        l2_factor: float = 1.0,
        smem_factor: float = 1.0,
        tma_factor: float = 1.0,
        occupancy_factor_override: Optional[float] = None,
        mma_efficiency: float = 1.0,
        mufu_efficiency: float = 1.0,
        launch_overhead_us: float = 0.0,
        overlap_frac: float = 0.0,
    ):
        self.name = name
        self.spec = spec
        self.hbm_factor = hbm_factor
        self.l2_factor = l2_factor
        self.smem_factor = smem_factor
        self.tma_factor = tma_factor
        self.occupancy_factor_override = occupancy_factor_override
        self.mma_efficiency = mma_efficiency
        self.mufu_efficiency = mufu_efficiency
        self.launch_overhead_us = launch_overhead_us
        self.overlap_frac = overlap_frac

    def predict(self, cfg: FA4Config) -> Dict[str, Any]:
        workload = compute_workload(cfg)
        occ = (
            self.occupancy_factor_override
            if self.occupancy_factor_override is not None
            else occupancy_factor(cfg, self.spec)
        )
        mma_t = mma_time_us(cfg, workload, self.spec, occ, self.mma_efficiency)
        mufu_t = mufu_time_us(cfg, workload, self.spec, occ, self.mufu_efficiency)
        mem_t = memory_time_us(
            workload,
            hbm_factor=self.hbm_factor,
            l2_factor=self.l2_factor,
            smem_factor=self.smem_factor,
            tma_factor=self.tma_factor,
            spec=self.spec,
        )
        # White-box roofline: overlap compute and memory where possible.  The
        # slowest domain dominates for large problem sizes, but a fraction of
        # memory traffic can be hidden behind compute warps (async TMA/SMEM).
        # Launch/scheduler overhead is added as a fixed offset for small grids.
        mem_eff = mem_t * (1.0 - self.overlap_frac)
        runtime_ms = (max(mma_t, mufu_t, mem_eff) + self.launch_overhead_us) / 1000.0

        # Per-stage times for bottleneck diagnosis, scaled by the overlap term.
        overlap = 1.0 - self.overlap_frac
        hbm_t = workload.hbm_bytes / max(
            effective_hbm_bw(workload.hbm_bytes, self.spec, self.hbm_factor), 1.0
        )
        l2_t = workload.l2_bytes / max(
            effective_l2_bw(workload.l2_bytes, self.spec, self.l2_factor), 1.0
        )
        smem_t = workload.smem_bytes / max(
            self.spec.smem_bandwidth_bytes_per_clock_per_sm
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * self.spec.num_sms
            * self.smem_factor,
            1.0,
        )
        tma_t = workload.tma_bytes / max(
            effective_tma_bw(workload.tma_bytes, self.spec, self.tma_factor), 1.0
        )

        label = bottleneck_label(
            cfg,
            workload,
            hbm_t * 1e6 * overlap,
            l2_t * 1e6 * overlap,
            smem_t * 1e6 * overlap,
            tma_t * 1e6 * overlap,
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
            "occupancy_fraction": occ,
        }


def baseline_predictor(spec: B200Spec = B200) -> Predictor:
    """FA4 paper roofline baseline: peak bandwidth and compute, no corrections."""
    return Predictor(
        name="baseline_fa4_roofline",
        spec=spec,
        hbm_factor=1.0,
        l2_factor=1.0,
        smem_factor=1.0,
        tma_factor=1.0,
        occupancy_factor_override=1.0,
        mma_efficiency=1.0,
        mufu_efficiency=1.0,
    )


def occupancy_only_predictor(spec: B200Spec = B200) -> Predictor:
    """Baseline + tile-size-dependent occupancy correction."""
    return Predictor(
        name="occupancy_only",
        spec=spec,
        hbm_factor=1.0,
        l2_factor=1.0,
        smem_factor=1.0,
        tma_factor=1.0,
        occupancy_factor_override=None,  # computed per config
        mma_efficiency=1.0,
        mufu_efficiency=1.0,
    )


def tma_l2_predictor(
    spec: B200Spec = B200,
    hbm_factor: float = 0.75,
    l2_factor: float = 0.60,
    tma_factor: float = 0.55,
) -> Predictor:
    """Baseline + effective HBM/L2/TMA bandwidth curves."""
    return Predictor(
        name="tma_l2_effective_bw",
        spec=spec,
        hbm_factor=hbm_factor,
        l2_factor=l2_factor,
        smem_factor=1.0,
        tma_factor=tma_factor,
        occupancy_factor_override=1.0,
        mma_efficiency=1.0,
        mufu_efficiency=1.0,
    )


def precision_only_predictor(spec: B200Spec = B200) -> Predictor:
    """Baseline + precision-specific MMA/MUFU throughput (no occupancy/BW correction)."""
    return Predictor(
        name="precision_only",
        spec=spec,
        hbm_factor=1.0,
        l2_factor=1.0,
        smem_factor=1.0,
        tma_factor=1.0,
        occupancy_factor_override=1.0,
        mma_efficiency=0.90,
        mufu_efficiency=0.90,
    )


def combined_predictor(
    spec: B200Spec = B200,
    hbm_factor: float = 0.80,
    l2_factor: float = 0.70,
    tma_factor: float = 0.65,
    smem_factor: float = 0.90,
    mma_efficiency: float = 0.85,
    mufu_efficiency: float = 0.85,
    launch_overhead_us: float = 2.0,
    overlap_frac: float = 0.0,
) -> Predictor:
    """Combined model: occupancy + effective BW + precision-specific throughput."""
    return Predictor(
        name="combined",
        spec=spec,
        hbm_factor=hbm_factor,
        l2_factor=l2_factor,
        smem_factor=smem_factor,
        tma_factor=tma_factor,
        occupancy_factor_override=None,
        mma_efficiency=mma_efficiency,
        mufu_efficiency=mufu_efficiency,
        launch_overhead_us=launch_overhead_us,
        overlap_frac=overlap_frac,
    )


PREDICTOR_FACTORIES = {
    "baseline_fa4_roofline": baseline_predictor,
    "occupancy_only": occupancy_only_predictor,
    "tma_l2_effective_bw": tma_l2_predictor,
    "precision_only": precision_only_predictor,
    "combined": combined_predictor,
}
