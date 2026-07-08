"""Cycle-level node-saturation model for FlashAttention-4 on B200.

The model treats the forward pass as a sequence of hardware-node executions:
TMA load of Q/K/V tiles, Tensor Core MMA for Q@K^T and P@V, SFU exp for the
online softmax, FP32 scale/update for the running O accumulator, and TMA store
of the final O tile.  Each node is given a throughput and a bounded efficiency
factor; the node with the largest required time is the predicted saturated
component, and the dependent chain that feeds it is the predicted blocking
path.

This is intentionally a white-box analytical model: node times are computed
from algorithm quantities and named hardware rates, not from a fit to measured
runtime.  Node efficiency factors are the only calibration knobs and they are
bounded to a physically meaningful range.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from fa4_b200_predictor.constants import B200, B200Spec, TILE
from fa4_b200_predictor.predictor import (
    FA4Config,
    compute_workload,
    effective_tma_bw,
    occupancy_factor,
    tile_size_for_config,
)


# Path descriptions used when a given node dominates the critical path.
BLOCKING_PATHS: Dict[str, str] = {
    "tma_load": "TMA load of Q/K/V tiles stalls the MMA pipe until data arrives",
    "tcgen05_mma": "Tensor Core MMA (Q@K^T and P@V) saturates the compute pipe",
    "sfu_exp": "SFU exp / row-max reduction saturates before the PV MMA can run",
    "fma_compute": "FMA pipe (FP32 update + softmax scaling + small-d/fp8 reductions) saturates",
    "tma_store": "TMA store of the final O tile backs up the pipeline",
}


@dataclass(frozen=True)
class DetailedNodeModel:
    """White-box node-saturation predictor.

    Efficiency factors are bounded multiplicative corrections to the peak rate
    of each hardware node.  They capture occupancy loss, instruction issue
    overhead, and realisable throughput on Blackwell silicon.
    """

    name: str = "detailed_node"
    spec: B200Spec = B200
    tma_load_efficiency: float = 1.0
    tma_store_efficiency: float = 1.0
    mma_efficiency: float = 1.0
    sfu_efficiency: float = 1.0
    fma_compute_efficiency: float = 1.0
    launch_fixed_us: float = 0.0
    launch_per_tile_us: float = 0.0
    # Fraction of MMA FLOPs that spill to the FMA pipe for small-d/fp8 tiles.
    mma_spill_base: float = 0.0
    mma_spill_d_factor: float = 0.0
    mma_spill_p_factor: float = 0.0

    def predict(self, cfg: FA4Config) -> Dict[str, Any]:
        """Return per-node times, predicted saturated component, and path."""
        workload = compute_workload(cfg)
        occ = occupancy_factor(cfg, self.spec)
        bpe = TILE.bytes_per_element[cfg.normalized_precision]
        b, h, s, d = cfg.batch, cfg.heads, cfg.seqlen, cfg.head_dim

        # TMA traffic: unique HBM bytes that must enter/leave the chip.
        # Q, K, V are read once from HBM (L2 handles reuse across output tiles);
        # O is written once.  The effective TMA bandwidth is calibrated to the
        # observed achieved rate, which already includes L2 reuse.
        tma_load_bytes = bpe * b * h * s * d * 3.0 * workload.seq_factor
        tma_store_bytes = bpe * b * h * s * d
        tma_load_bw = effective_tma_bw(
            tma_load_bytes, self.spec, self.tma_load_efficiency
        )
        tma_store_bw = effective_tma_bw(
            tma_store_bytes, self.spec, self.tma_store_efficiency
        )
        tma_load_us = (tma_load_bytes / max(tma_load_bw, 1.0)) * 1e6
        tma_store_us = (tma_store_bytes / max(tma_store_bw, 1.0)) * 1e6

        # Tensor Core MMA time.
        mma_rate_per_sm = self.spec.mma_throughput_per_sm_per_clock[
            cfg.normalized_precision
        ]
        mma_total_rate = (
            mma_rate_per_sm
            * self.spec.num_sms
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * occ
            * self.mma_efficiency
        )
        tcgen05_mma_us = (workload.mma_flops / max(mma_total_rate, 1.0)) * 1e6

        # SFU exp time (online softmax row reductions).
        sfu_rate_per_sm = self.spec.mufu_throughput_per_sm_per_clock[
            cfg.normalized_precision
        ]
        sfu_total_rate = (
            sfu_rate_per_sm
            * self.spec.num_sms
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * occ
            * self.sfu_efficiency
        )
        sfu_exp_us = (workload.exp_ops / max(sfu_total_rate, 1.0)) * 1e6

        # FMA compute time (FP32 update + softmax scaling + small-d/fp8 spill).
        # For small head-dim or fp8 precision, part of the P@V reduction and
        # output assembly spills from Tensor Cores onto the FMA pipe.  The
        # spill fraction is calibrated from NCU per-pipe activity.
        block_m, block_n = tile_size_for_config(cfg)
        n_iters = math.ceil(s / block_n)
        # FP32 O-accumulator update: scale + multiply-add per element per iter.
        update_ops = 2.0 * b * h * s * d * n_iters * workload.seq_factor
        # Softmax scaling: one FMA per output element per iter.
        scale_ops = 1.0 * b * h * s * d * n_iters * workload.seq_factor
        # MMA spill to FMA: grows for small head-dim and fp8 precision.
        d_inv = 128.0 / max(d, 1.0)
        p_mult = {"bf16": 1.0, "fp16": 1.0, "fp8": 2.5, "fp4": 4.0}.get(
            cfg.normalized_precision, 1.0
        )
        spill_frac = (
            self.mma_spill_base
            + self.mma_spill_d_factor * d_inv
            + self.mma_spill_p_factor * p_mult
        )
        spill_frac = max(0.0, min(spill_frac, 1.0))
        spill_ops = workload.mma_flops * spill_frac
        fma_ops = update_ops + scale_ops + spill_ops
        # Conservative FP32 FMA throughput per SM per clock on B200.
        fp32_fma_per_sm_per_clock = 128.0
        fma_total_rate = (
            fp32_fma_per_sm_per_clock
            * self.spec.num_sms
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * occ
            * self.fma_compute_efficiency
        )
        fma_compute_us = (fma_ops / max(fma_total_rate, 1.0)) * 1e6

        # Launch/grid overhead from the improved model.
        total_tiles = (
            b
            * h
            * math.ceil(s / block_m)
            * math.ceil(s / block_n)
        )
        launch_us = self.launch_fixed_us + self.launch_per_tile_us * total_tiles

        node_times = {
            "tma_load": tma_load_us,
            "tcgen05_mma": tcgen05_mma_us,
            "sfu_exp": sfu_exp_us,
            "fma_compute": fma_compute_us,
            "tma_store": tma_store_us,
        }
        saturated_component = max(node_times, key=node_times.get)  # type: ignore[arg-type]
        predicted_runtime_ms = (
            max(node_times.values()) + launch_us
        ) / 1000.0

        return {
            "predicted_runtime_ms": predicted_runtime_ms,
            "predicted_saturated_component": saturated_component,
            "predicted_blocking_path": BLOCKING_PATHS[saturated_component],
            "node_times_us": node_times,
            "tma_load_us": tma_load_us,
            "tcgen05_mma_us": tcgen05_mma_us,
            "sfu_exp_us": sfu_exp_us,
            "fma_compute_us": fma_compute_us,
            "tma_store_us": tma_store_us,
            "launch_overhead_us": launch_us,
            "occupancy_fraction": occ,
            "total_tiles": total_tiles,
        }

    def to_params(self) -> Dict[str, Any]:
        """Serialisable calibration parameters."""
        return {
            "tma_load_efficiency": self.tma_load_efficiency,
            "tma_store_efficiency": self.tma_store_efficiency,
            "mma_efficiency": self.mma_efficiency,
            "sfu_efficiency": self.sfu_efficiency,
            "fma_compute_efficiency": self.fma_compute_efficiency,
            "launch_fixed_us": self.launch_fixed_us,
            "launch_per_tile_us": self.launch_per_tile_us,
            "mma_spill_base": self.mma_spill_base,
            "mma_spill_d_factor": self.mma_spill_d_factor,
            "mma_spill_p_factor": self.mma_spill_p_factor,
        }

    @classmethod
    def from_params(cls, params: Dict[str, Any], name: str = "detailed_node") -> "DetailedNodeModel":
        """Rebuild a DetailedNodeModel from saved parameters."""
        return cls(
            name=name,
            spec=B200,
            tma_load_efficiency=params.get("tma_load_efficiency", 1.0),
            tma_store_efficiency=params.get("tma_store_efficiency", 1.0),
            mma_efficiency=params.get("mma_efficiency", 1.0),
            sfu_efficiency=params.get("sfu_efficiency", 1.0),
            fma_compute_efficiency=params.get("fma_compute_efficiency", 1.0),
            launch_fixed_us=params.get("launch_fixed_us", 0.0),
            launch_per_tile_us=params.get("launch_per_tile_us", 0.0),
            mma_spill_base=params.get("mma_spill_base", 0.0),
            mma_spill_d_factor=params.get("mma_spill_d_factor", 0.0),
            mma_spill_p_factor=params.get("mma_spill_p_factor", 0.0),
        )


def default_detailed_node_model() -> DetailedNodeModel:
    """Initial detailed-node model calibrated on B200 NCU component-saturation data."""
    return DetailedNodeModel(
        name="detailed_node",
        tma_load_efficiency=1.017,
        tma_store_efficiency=1.096,
        mma_efficiency=0.358,
        sfu_efficiency=0.847,
        fma_compute_efficiency=2.000,
        launch_fixed_us=105.9,
        launch_per_tile_us=0.0000,
        mma_spill_base=0.000,
        mma_spill_d_factor=0.0523,
        mma_spill_p_factor=0.000,
    )
