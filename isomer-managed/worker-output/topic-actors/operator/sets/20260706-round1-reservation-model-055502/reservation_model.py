"""Per-SM execution-unit reservation model for FlashAttention-4 on B200.

This module refines the earlier closed-form cycle-level model by treating each
SM as a collection of specialized execution units (Tensor Cores, SFU, FP/INT,
TMA/LD-ST memory pipes, and TMEM) and modeling a FA4 tile block as a sequence
of reservations on those units.  The critical path is the unit with the largest
reservation across the active SMs, adjusted for the limited overlap between
explicit Blackwell pipeline stages (TMA -> TMEM -> TC -> SFU -> TMEM).

The model is still deterministic and closed-form (not event-driven), but it
exposes which unit saturates first and how data movement between components
contributes to the bound.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# -----------------------------------------------------------------------------
# Hardware specification
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class B200ReservationModelSpec:
    """Per-SM unit reservation parameters for FA4 on B200.

    Defaults are grounded in public B200 specs and the microbenchmark
    characterisation in Jarmusch et al. (arXiv:2507.10789, 2512.02189) and the
    stage-centric Blackwell model in arXiv:2605.04178.
    """

    # SM / clock
    num_sms: int = 176
    peak_sm_clock_mhz: float = 1965.0
    max_warps_per_sm: int = 64
    threads_per_warp: int = 32
    schedulers_per_sm: int = 4

    # Per-SM execution unit counts and raw throughputs.
    # Throughputs are "operations per SM per clock" where an "operation" is the
    # natural unit for that pipe (one MMA instruction for TC, one exp for SFU,
    # one 32-bit FMA for FP/INT, one 32-byte TMA transaction for MEM).
    tc_mma_throughput_per_sm_per_clock: Dict[str, float] = field(
        default_factory=lambda: {
            # Calibrated to B200 sustained peaks (~2250 TFLOPS FP16 at 176 SMs).
            "fp32": 3072.0,
            "fp16": 6144.0,
            "bf16": 6144.0,
            "fp8": 12288.0,
            "fp4": 24576.0,
        }
    )
    tc_latency_cycles: int = 16
    tc_initiation_interval: int = 1

    sfu_throughput_per_sm_per_clock: Dict[str, float] = field(
        default_factory=lambda: {
            "fp32": 16.0,
            "fp16": 16.0,
            "bf16": 16.0,
            "fp8": 16.0,
            "fp4": 16.0,
        }
    )
    sfu_latency_cycles: int = 4

    fp32_throughput_per_sm_per_clock: float = 128.0
    fp32_latency_cycles: int = 6

    # TMA (Tensor Memory Accelerator) memory pipe.
    tma_peak_bw_gbps: float = 8000.0
    tma_latency_cycles: int = 48
    tma_transaction_bytes: int = 32

    # TMEM (Tensor Memory) on-SM storage for tensor operands/accumulators.
    tmem_capacity_kb_per_sm: float = 256.0
    tmem_peak_bw_gbps: float = 24000.0
    tmem_latency_cycles: int = 8

    # L2 / HBM path for TMA misses.
    peak_hbm_bw_gbps: float = 4480.0
    peak_l2_bw_gbps: float = 24000.0
    l2_hit_rate: float = 0.75

    # Occupancy / overlap / cluster.
    max_cluster_size_sms: int = 2
    cluster_efficiency: float = 1.0
    occupancy_efficiency: float = 1.0
    stage_overlap_factor: float = 0.85
    launch_overhead_us: float = 2.0

    # Efficiency scalars that are fit to measurements.
    tc_efficiency: float = 1.0
    sfu_efficiency: float = 1.0
    fp_efficiency: float = 1.0
    tma_efficiency: float = 1.0
    tmem_efficiency: float = 1.0
    tmem_spill_coefficient: float = 0.0


# -----------------------------------------------------------------------------
# Workload description
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class FA4WorkloadDesc:
    """Algorithmic workload quantities for one FA4 forward pass."""

    batch: int
    heads: int
    seqlen: int
    head_dim: int
    causal: bool
    precision: str

    @property
    def normalized_precision(self) -> str:
        aliases: Dict[str, str] = {
            "f32": "fp32",
            "float32": "fp32",
            "f16": "fp16",
            "float16": "fp16",
            "bf16": "bf16",
            "bfloat16": "bf16",
            "fp8": "fp8",
            "fp8_e4m3": "fp8",
            "fp4": "fp4",
        }
        return aliases.get(self.precision.lower(), self.precision.lower())

    @property
    def bytes_per_element(self) -> int:
        bpe: Dict[str, int] = {
            "fp32": 4,
            "fp16": 2,
            "bf16": 2,
            "fp8": 1,
            "fp4": 1,
        }
        return bpe[self.normalized_precision]

    @property
    def seq_factor(self) -> float:
        return 0.5 if self.causal else 1.0


# -----------------------------------------------------------------------------
# Reservation model
# -----------------------------------------------------------------------------


class B200ReservationModel:
    """Per-SM execution-unit reservation model for one FA4 forward pass.

    A tile block is modelled as a sequence of reservations on the SM's
    execution units.  For each unit we compute the total cycles that unit must
    be busy, then take the busiest unit (adjusted for stage overlap) as the
    per-step critical path.  The total runtime is ``K_steps * T_step`` plus
    launch overhead.
    """

    def __init__(self, spec: Optional[B200ReservationModelSpec] = None) -> None:
        self.spec = spec if spec is not None else B200ReservationModelSpec()

    # -------------------------------------------------------------------------
    # Tile geometry and parallelism
    # -------------------------------------------------------------------------

    def _tile_size_for_config(self, cfg: FA4WorkloadDesc) -> tuple[int, int]:
        """Return (block_m, block_n) heuristics for ``cfg``."""
        defaults: Dict[int, tuple[int, int]] = {
            64: (128, 128),
            128: (128, 64),
            256: (64, 64),
        }
        return defaults.get(cfg.head_dim, (128, 64))

    def _tile_counts(self, cfg: FA4WorkloadDesc) -> tuple[int, int, int]:
        """Return (tiles_m, tiles_n, total_output_tiles)."""
        block_m, block_n = self._tile_size_for_config(cfg)
        tiles_m = math.ceil(cfg.seqlen / block_m)
        tiles_n = math.ceil(cfg.seqlen / block_n)
        total_output_tiles = cfg.batch * cfg.heads * tiles_m * tiles_n
        return tiles_m, tiles_n, total_output_tiles

    def _active_sms(self, cfg: FA4WorkloadDesc) -> int:
        """Number of SMs that participate, limited by the output grid."""
        _, _, total_output_tiles = self._tile_counts(cfg)
        return min(self.spec.num_sms, max(1, total_output_tiles))

    def _cluster_size(self, cfg: FA4WorkloadDesc) -> int:
        """Use 2-SM clusters for larger head dimensions."""
        if cfg.head_dim >= 128 and self.spec.max_cluster_size_sms >= 2:
            return 2
        return 1

    def _effective_active_sms(self, cfg: FA4WorkloadDesc) -> int:
        """Active SMs (cluster cooperation is absorbed by cluster_efficiency)."""
        return self._active_sms(cfg)

    def _active_warps(self, cfg: FA4WorkloadDesc) -> float:
        """Resident warps across the device, limited by tile geometry."""
        _, _, total_output_tiles = self._tile_counts(cfg)
        warps_per_tile = 4
        required = total_output_tiles * warps_per_tile
        max_device_warps = self.spec.num_sms * self.spec.max_warps_per_sm
        return max(1.0, min(required, max_device_warps))

    def _occupancy_fraction(self, cfg: FA4WorkloadDesc) -> float:
        """Fraction of theoretical throughput reachable given occupancy."""
        active = self._active_warps(cfg)
        max_warps = self.spec.num_sms * self.spec.max_warps_per_sm
        frac = active / max_warps
        return min(1.0, math.sqrt(max(0.0, frac)) * 0.95 + 0.05)

    def _effective_compute_scale(self, cfg: FA4WorkloadDesc) -> float:
        """Product of occupancy and cluster efficiency."""
        return (
            self._occupancy_fraction(cfg)
            * self.spec.occupancy_efficiency
            * self.spec.cluster_efficiency
        )

    # -------------------------------------------------------------------------
    # Unit reservation helpers
    # -------------------------------------------------------------------------

    def _ns_to_cycles(self, ns: float) -> float:
        return ns * self.spec.peak_sm_clock_mhz / 1000.0

    def _tc_cycles(self, flops: float, cfg: FA4WorkloadDesc) -> float:
        """Cycles reserving the tensor-core pipe for ``flops``."""
        prec = cfg.normalized_precision
        rate_per_sm = self.spec.tc_mma_throughput_per_sm_per_clock.get(prec, 1024.0)
        active = self._effective_active_sms(cfg)
        scale = self._effective_compute_scale(cfg) * self.spec.tc_efficiency
        peak_flops_per_cycle = rate_per_sm * active * scale
        throughput_cycles = flops / max(peak_flops_per_cycle, 1.0)
        # Latency-hiding penalty when too few warps are resident.
        needed = math.ceil(
            self.spec.tc_latency_cycles / max(self.spec.tc_initiation_interval, 1)
        )
        active_warps = self._active_warps(cfg)
        efficiency = min(1.0, active_warps / max(needed, 1.0))
        penalty = 1.0 + max(0.0, 1.0 - efficiency) * 0.5
        return throughput_cycles * penalty

    def _tmem_cycles(self, bytes_moved: float, cfg: FA4WorkloadDesc) -> float:
        """Cycles reserving the TMEM read/write pipe."""
        spec = self.spec
        bytes_per_cycle = (
            spec.tmem_peak_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        )
        active = self._effective_active_sms(cfg)
        effective_bw = bytes_per_cycle * active * spec.tmem_efficiency
        return bytes_moved / max(effective_bw, 1.0)

    def _sfu_cycles(self, ops: float, cfg: FA4WorkloadDesc) -> float:
        """Cycles reserving the SFU pipe (exp, log, rsqrt, ...)."""
        prec = cfg.normalized_precision
        rate_per_sm = self.spec.sfu_throughput_per_sm_per_clock.get(prec, 16.0)
        active = self._effective_active_sms(cfg)
        scale = self._effective_compute_scale(cfg) * self.spec.sfu_efficiency
        peak_ops_per_cycle = rate_per_sm * active * scale
        return ops / max(peak_ops_per_cycle, 1.0)

    def _fp_cycles(self, ops: float, cfg: FA4WorkloadDesc) -> float:
        """Cycles reserving the FP32/INT32 pipe for scale/update arithmetic."""
        active = self._effective_active_sms(cfg)
        scale = self._effective_compute_scale(cfg) * self.spec.fp_efficiency
        peak_ops_per_cycle = self.spec.fp32_throughput_per_sm_per_clock * active * scale
        return ops / max(peak_ops_per_cycle, 1.0)

    def _tma_cycles(self, bytes_moved: float, cfg: FA4WorkloadDesc) -> float:
        """Cycles reserving the global TMA async memory pipe for ``bytes_moved``."""
        spec = self.spec
        # TMA bandwidth is a GPU-wide resource; do not scale by active SMs.
        bytes_per_cycle = spec.tma_peak_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        effective_bw = bytes_per_cycle * spec.tma_efficiency
        # Sustained throughput is also limited by L2/HBM for misses.
        miss_bytes = bytes_moved * (1.0 - spec.l2_hit_rate)
        l2_bytes_per_cycle = spec.peak_l2_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        hbm_bytes_per_cycle = spec.peak_hbm_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        tma_cycles = bytes_moved / max(effective_bw, 1.0)
        l2_cycles = miss_bytes * spec.l2_hit_rate / max(l2_bytes_per_cycle, 1.0)
        hbm_cycles = miss_bytes * (1.0 - spec.l2_hit_rate) / max(hbm_bytes_per_cycle, 1.0)
        return max(tma_cycles, l2_cycles, hbm_cycles)

    def _tmem_spill_penalty(self, cfg: FA4WorkloadDesc) -> float:
        """Penalty if accumulator working set exceeds TMEM capacity per SM."""
        block_m, block_n = self._tile_size_for_config(cfg)
        # One accumulator tile (fp32) plus two input tiles per SM cluster.
        acc_bytes = block_m * block_n * 4
        q_bytes = block_m * cfg.head_dim * cfg.bytes_per_element
        kv_bytes = block_n * cfg.head_dim * cfg.bytes_per_element
        working_set = acc_bytes + q_bytes + 2 * kv_bytes
        capacity = self.spec.tmem_capacity_kb_per_sm * 1024
        if working_set <= capacity:
            return 0.0
        excess_ratio = (working_set - capacity) / capacity
        return self.spec.tmem_spill_coefficient * excess_ratio

    # -------------------------------------------------------------------------
    # Per-step reservation table
    # -------------------------------------------------------------------------

    def _per_step_reservations(self, cfg: FA4WorkloadDesc) -> Dict[str, Any]:
        """Return per-unit reservation cycles for one KV step of a tile block.

        One step loads a K and V tile, performs Q@K^T and P@V MMAs, and runs the
        online softmax update.  Loads are via TMA; MMA operands/accumulators use
        TMEM.  The Q tile is loaded once per output row tile and reused across
        steps, so it is accounted for separately.
        """
        spec = self.spec
        block_m, block_n = self._tile_size_for_config(cfg)
        bpe = cfg.bytes_per_element
        active_sms = self._effective_active_sms(cfg)

        # Bytes per tile.
        q_tile_bytes = block_m * cfg.head_dim * bpe
        kv_tile_bytes = block_n * cfg.head_dim * bpe
        s_tile_bytes = block_m * block_n * 4  # fp32 accumulator
        o_tile_bytes = block_m * cfg.head_dim * bpe

        # Memory reservations (TMA loads for K and V, one per step).
        k_load_tma = self._tma_cycles(kv_tile_bytes, cfg)
        v_load_tma = self._tma_cycles(kv_tile_bytes, cfg)
        mem_cycles = k_load_tma + v_load_tma

        # Q is loaded once per row tile; amortize over steps.
        q_load_tma = self._tma_cycles(q_tile_bytes, cfg)
        o_store_tma = self._tma_cycles(o_tile_bytes, cfg)

        # MMA reservations.
        # The TC and TMEM pipes are tightly coupled; the QK/PV pipelines are
        # bound by the slower of compute and TMEM traffic.
        mma_flops_per_iter = 2.0 * block_m * block_n * cfg.head_dim
        qk_tc = self._tc_cycles(mma_flops_per_iter, cfg)
        pv_tc = self._tc_cycles(mma_flops_per_iter, cfg)
        qk_tmem = self._tmem_cycles(q_tile_bytes + kv_tile_bytes + s_tile_bytes, cfg)
        pv_tmem = self._tmem_cycles(s_tile_bytes + kv_tile_bytes + o_tile_bytes, cfg)
        tc_cycles = max(qk_tc, qk_tmem) + max(pv_tc, pv_tmem)

        # Softmax reservations.
        # Exp over the score matrix (one per element) plus row-wise reductions.
        exp_ops = block_m * block_n
        scale_update_ops = block_m * cfg.head_dim * 2  # scale + update per row
        softmax_sfu = self._sfu_cycles(exp_ops, cfg)
        softmax_fp = self._fp_cycles(scale_update_ops, cfg)
        softmax_cycles = softmax_sfu + softmax_fp

        # TMEM spill penalty is applied to TC reservation.
        spill_penalty = self._tmem_spill_penalty(cfg)
        tc_cycles_with_spill = tc_cycles * (1.0 + spill_penalty)

        return {
            "mem_cycles": mem_cycles,
            "tc_cycles": tc_cycles_with_spill,
            "softmax_cycles": softmax_cycles,
            "q_load_tma": q_load_tma,
            "o_store_tma": o_store_tma,
            "k_load_tma": k_load_tma,
            "v_load_tma": v_load_tma,
            "qk_tc": qk_tc,
            "pv_tc": pv_tc,
            "qk_tmem": qk_tmem,
            "pv_tmem": pv_tmem,
            "softmax_sfu": softmax_sfu,
            "softmax_fp": softmax_fp,
            "spill_penalty": spill_penalty,
            "block_m": block_m,
            "block_n": block_n,
        }

    # -------------------------------------------------------------------------
    # Aggregate prediction
    # -------------------------------------------------------------------------

    def predict(self, cfg: FA4WorkloadDesc) -> Dict[str, Any]:
        """Return predicted runtime and per-unit reservation breakdown."""
        spec = self.spec
        _, tiles_n, total_output_tiles = self._tile_counts(cfg)
        seq_factor = cfg.seq_factor
        total_iterations = total_output_tiles * seq_factor
        total_row_tiles = cfg.batch * cfg.heads * math.ceil(
            cfg.seqlen / self._tile_size_for_config(cfg)[0]
        )

        step = self._per_step_reservations(cfg)

        # Steady-state step time: max of the busy units, with limited overlap.
        # TMA loads can overlap with prior compute, but the next MMA cannot start
        # until its operands are in TMEM, so compute and memory are only partially
        # concurrent.  We model this with stage_overlap_factor.
        step_compute = step["tc_cycles"] + step["softmax_cycles"]
        step_memory = step["mem_cycles"]
        visible_memory_cycles = step_memory * (1.0 - spec.stage_overlap_factor)
        step_cycles = max(step_compute, visible_memory_cycles)

        # Amortized Q load / O store over all row tiles.
        fixed_io_cycles = (step["q_load_tma"] + step["o_store_tma"]) * total_row_tiles
        step_io_cycles = step_memory * total_iterations

        # Total compute reservations across all iterations.
        total_tc_cycles = step["tc_cycles"] * total_iterations
        total_softmax_cycles = step["softmax_cycles"] * total_iterations
        total_compute_cycles = total_tc_cycles + total_softmax_cycles

        total_memory_cycles = fixed_io_cycles + step_io_cycles
        visible_total_memory = total_memory_cycles * (1.0 - spec.stage_overlap_factor)

        critical_path_cycles = max(total_compute_cycles, visible_total_memory)
        launch_cycles = spec.launch_overhead_us * spec.peak_sm_clock_mhz
        total_cycles = critical_path_cycles + launch_cycles
        runtime_us = total_cycles / spec.peak_sm_clock_mhz
        runtime_ms = runtime_us / 1000.0

        per_unit_cycles = {
            "tc_mma_cycles": total_tc_cycles,
            "softmax_sfu_cycles": step["softmax_sfu"] * total_iterations,
            "softmax_fp_cycles": step["softmax_fp"] * total_iterations,
            "tma_load_cycles": step_io_cycles + step["q_load_tma"] * total_row_tiles,
            "tma_store_cycles": step["o_store_tma"] * total_row_tiles,
            "tmem_cycles": (step["qk_tmem"] + step["pv_tmem"]) * total_iterations,
        }

        unit_utilizations = {
            "tc_util": total_tc_cycles / max(critical_path_cycles, 1.0),
            "sfu_util": per_unit_cycles["softmax_sfu_cycles"] / max(critical_path_cycles, 1.0),
            "fp_util": per_unit_cycles["softmax_fp_cycles"] / max(critical_path_cycles, 1.0),
            "tma_util": total_memory_cycles / max(critical_path_cycles, 1.0),
            "tmem_util": per_unit_cycles["tmem_cycles"] / max(critical_path_cycles, 1.0),
        }

        # Determine bottleneck unit.
        bottleneck_reservations = {
            "tc_mma": total_tc_cycles,
            "softmax": total_softmax_cycles,
            "tma_memory": total_memory_cycles,
        }
        dominant_bottleneck = max(bottleneck_reservations, key=bottleneck_reservations.get)  # type: ignore[arg-type]

        return {
            "predicted_runtime_ms": runtime_ms,
            "predicted_runtime_us": runtime_us,
            "total_cycles": total_cycles,
            "critical_path_cycles": critical_path_cycles,
            "total_compute_cycles": total_compute_cycles,
            "total_memory_cycles": total_memory_cycles,
            "visible_memory_cycles": visible_total_memory,
            "per_unit_cycles": per_unit_cycles,
            "per_unit_us": {
                k: v / spec.peak_sm_clock_mhz for k, v in per_unit_cycles.items()
            },
            "unit_utilizations": unit_utilizations,
            "dominant_bottleneck": dominant_bottleneck,
            "active_sms": self._active_sms(cfg),
            "effective_active_sms": self._effective_active_sms(cfg),
            "cluster_size": self._cluster_size(cfg),
            "total_iterations": total_iterations,
            "total_row_tiles": total_row_tiles,
            "step": step,
        }


# -----------------------------------------------------------------------------
# Convenience wrappers
# -----------------------------------------------------------------------------


def default_b200_reservation_model() -> B200ReservationModel:
    """Return a ``B200ReservationModel`` with B200-calibrated defaults."""
    return B200ReservationModel()


def predict_runtime(
    batch: int,
    heads: int,
    seqlen: int,
    head_dim: int,
    causal: bool,
    precision: str,
    spec: Optional[B200ReservationModelSpec] = None,
) -> Dict[str, Any]:
    """One-shot convenience wrapper around ``B200ReservationModel.predict``."""
    cfg = FA4WorkloadDesc(
        batch=batch,
        heads=heads,
        seqlen=seqlen,
        head_dim=head_dim,
        causal=causal,
        precision=precision,
    )
    return B200ReservationModel(spec=spec).predict(cfg)


if __name__ == "__main__":
    demo = FA4WorkloadDesc(
        batch=2, heads=16, seqlen=2048, head_dim=128, causal=True, precision="fp16"
    )
    result = default_b200_reservation_model().predict(demo)
    print(f"demo predicted_runtime_ms = {result['predicted_runtime_ms']:.3f}")
    print(f"demo dominant_bottleneck  = {result['dominant_bottleneck']}")
