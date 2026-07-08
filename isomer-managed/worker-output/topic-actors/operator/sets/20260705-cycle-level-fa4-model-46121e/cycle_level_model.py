"""Cycle-level math model for FlashAttention-4 forward pass on NVIDIA B200.

This module implements a deterministic, closed-form cycle-math model (not an
event-driven simulator) of one FA4 forward pass.  It decomposes execution into
per-tile-block phases and, for each memory transfer, estimates the cycle cost of
every hardware hop from HBM row buffer to SMEM/RF and back.

No CUDA execution is performed; the model is pure Python and importable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# -----------------------------------------------------------------------------
# Hardware specification
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class B200CycleLevelModelSpec:
    """Cycle-level hardware parameters for FlashAttention-4 on B200.

    Defaults are calibrated to public B200 rough specs (peak SM clock ~1,965 MHz,
    ~180 SMs, ~4.5 TB/s HBM) and the FA4 white-box predictor constants.  All
    fields are physically scoped so they can be calibrated from measurements.
    """

    # SM / clock
    num_sms: int = 180
    peak_sm_clock_mhz: float = 1965.0
    max_warps_per_sm: int = 64
    threads_per_warp: int = 32
    schedulers_per_sm: int = 4
    warp_inst_issue_per_scheduler_per_cycle: float = 1.0

    # Tensor Core MMA throughput (FLOPs per SM per clock).
    tc_mma_throughput_per_sm_per_clock: Dict[str, float] = field(
        default_factory=lambda: {
            "fp32": 1024.0,
            "fp16": 2048.0,
            "bf16": 2048.0,
            "fp8": 4096.0,
            "fp4": 8192.0,
        }
    )
    tc_latency_cycles: int = 16
    tc_initiation_interval: int = 1
    tc_efficiency: float = 1.0

    # MUFU / SFU throughput (exp per SM per clock).
    mufu_throughput_per_sm_per_clock: Dict[str, float] = field(
        default_factory=lambda: {
            "fp32": 16.0,
            "fp16": 16.0,
            "bf16": 16.0,
            "fp8": 16.0,
            "fp4": 16.0,
        }
    )
    mufu_latency_cycles: int = 4
    mufu_efficiency: float = 1.0

    # Register file / operand collector friction.
    operand_collector_efficiency: float = 0.92

    # Memory hierarchy bandwidths.
    peak_hbm_bw_gbps: float = 4480.0
    peak_l2_bw_gbps: float = 24000.0
    peak_l1_bw_gbps: float = 48000.0
    smem_bandwidth_bytes_per_clock_per_sm: float = 128.0

    # Cache / sector geometry.
    l1_line_bytes: int = 128
    l1_sector_bytes: int = 32
    l2_line_bytes: int = 128
    l1_miss_rate: float = 0.08
    l2_miss_rate: float = 0.25

    # HBM bank / timing.
    hbm_num_banks: int = 16
    hbm_num_bank_groups: int = 4
    hbm_row_buffer_hit_rate: float = 0.65
    hbm_t_rcd_ns: float = 14.0
    hbm_t_cl_ns: float = 14.0
    hbm_t_rp_ns: float = 14.0
    hbm_page_bytes: int = 2048
    hbm_burst_bytes: int = 32
    hbm_efficiency: float = 1.0

    # Interconnect / crossbar.
    num_memory_partitions: int = 16
    xbar_cycles_per_flit: float = 0.1
    xbar_contention_exponent: float = 1.0
    xbar_contention_scale: float = 0.5

    # Occupancy / overlap.
    occupancy_efficiency: float = 1.0
    memory_overlap_factor: float = 0.85
    launch_overhead_us: float = 2.0


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
# Cycle-level model
# -----------------------------------------------------------------------------


class B200CycleLevelModel:
    """Cycle-level math model for one FA4 forward pass on B200.

    Execution is decomposed into per-tile-block phases:

    1. Load Q tile from HBM -> L2 -> xbar -> L1 -> RF/SMEM.
    2. Load K tile from HBM -> L2 -> xbar -> L1 -> RF/SMEM.
    3. Tensor-core MMA Q@K^T -> accumulator registers.
    4. Softmax scaling/exp per row (MUFU/SFU + SMEM reductions).
    5. Load V tile from HBM -> L2 -> xbar -> L1 -> RF/SMEM.
    6. Tensor-core MMA P@V -> output accumulator.
    7. Store O tile back through RF/SMEM -> L1 -> xbar -> L2 -> HBM.

    For each transfer the model estimates bytes moved, slicing into sectors and
    cache lines, and the cycle cost of every hardware hop.  Compute phases model
    tensor-core and MUFU throughput including initiation interval, pipeline
    latency, and operand-collector friction.

    The overall runtime uses deterministic closed-form critical-path logic:
    memory and compute are assumed to overlap via prefetching and pipelining, so
    the dominant side governs, with a tunable memory-overlap factor.
    """

    def __init__(self, spec: Optional[B200CycleLevelModelSpec] = None) -> None:
        self.spec = spec if spec is not None else B200CycleLevelModelSpec()

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
        # Throughput scales roughly with sqrt of occupancy at low occupancy, then
        # saturates; this shape matches the existing predictor's occupancy curve.
        return min(1.0, math.sqrt(max(0.0, frac)) * 0.95 + 0.05)

    def _effective_compute_scale(self, cfg: FA4WorkloadDesc) -> float:
        """Product of occupancy and efficiency scalars for compute units."""
        return self._occupancy_fraction(cfg) * self.spec.occupancy_efficiency

    # -------------------------------------------------------------------------
    # Memory-path cycle model
    # -------------------------------------------------------------------------

    def _ns_to_cycles(self, ns: float) -> float:
        """Convert nanoseconds to SM clock cycles."""
        return ns * self.spec.peak_sm_clock_mhz / 1000.0

    def _memory_path_cycles(
        self, bytes_moved: float, active_sms: int, is_write: bool = False
    ) -> Dict[str, float]:
        """Return per-hop cycle cost for ``bytes_moved`` through the memory path.

        The path is: HBM row buffer -> L2 -> xbar -> L1 -> RF/SMEM (read) or the
        reverse (write).  Each hop is modelled as an independent pipeline stage;
        sustained throughput is the maximum stage latency because the stages are
        streamed.  The returned dictionary also includes the hop-level breakdown
        so callers can diagnose which component dominates.
        """
        spec = self.spec
        if bytes_moved <= 0:
            return {
                "hbm_cycles": 0.0,
                "l2_cycles": 0.0,
                "l1_cycles": 0.0,
                "xbar_cycles": 0.0,
                "total_cycles": 0.0,
            }

        # Peak bytes per SM clock for each level.
        peak_hbm_bytes_per_cycle = (
            spec.peak_hbm_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        )
        peak_l2_bytes_per_cycle = (
            spec.peak_l2_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        )
        peak_l1_bytes_per_cycle = (
            spec.peak_l1_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        )

        # L1: every byte touches L1 on the way into/out of the SM.
        effective_l1_bytes_per_cycle = peak_l1_bytes_per_cycle * (
            active_sms / max(spec.num_sms, 1)
        )
        l1_cycles = bytes_moved / max(effective_l1_bytes_per_cycle, 1.0)

        # L2: only L1 misses reach L2.
        l2_load = active_sms / max(spec.num_memory_partitions, 1)
        l2_contention = 1.0 + math.sqrt(l2_load) * 0.12
        effective_l2_bytes_per_cycle = peak_l2_bytes_per_cycle / l2_contention
        l2_cycles = bytes_moved * spec.l1_miss_rate / max(effective_l2_bytes_per_cycle, 1.0)

        # xbar / NoC: one flit per L1 sector; only L1 misses traverse it.
        flits = bytes_moved / max(spec.l1_sector_bytes, 1)
        xbar_load = active_sms / max(spec.num_memory_partitions, 1)
        xbar_contention = (
            1.0
            + (xbar_load ** spec.xbar_contention_exponent)
            * 0.08
            * spec.xbar_contention_scale
        )
        xbar_cycles = (
            flits
            * spec.l1_miss_rate
            * spec.xbar_cycles_per_flit
            * xbar_contention
            / max(spec.num_memory_partitions, 1)
        )

        # HBM: only L2 misses reach DRAM.
        row_locality_factor = (
            spec.hbm_row_buffer_hit_rate
            + (1.0 - spec.hbm_row_buffer_hit_rate) * 0.35
        )
        blp = min(
            spec.hbm_num_banks,
            active_sms * spec.schedulers_per_sm / max(spec.num_memory_partitions, 1),
        )
        blp_factor = min(1.0, blp / max(spec.hbm_num_banks, 1))
        rw_turnaround = 0.92 if is_write else 1.0
        effective_hbm_bytes_per_cycle = (
            peak_hbm_bytes_per_cycle
            * spec.hbm_efficiency
            * row_locality_factor
            * blp_factor
            * rw_turnaround
        )
        miss_fraction = spec.l1_miss_rate * spec.l2_miss_rate
        hbm_cycles = bytes_moved * miss_fraction / max(effective_hbm_bytes_per_cycle, 1.0)

        # Keep a small residual latency term for very short transfers.
        row_miss_cycles_per_byte = (
            (1.0 - spec.hbm_row_buffer_hit_rate)
            * (spec.hbm_t_rcd_ns + spec.hbm_t_cl_ns + spec.hbm_t_rp_ns)
            * (spec.peak_sm_clock_mhz / 1000.0)
            / max(spec.hbm_page_bytes, 1)
        )
        hbm_cycles += bytes_moved * miss_fraction * row_miss_cycles_per_byte * 0.05

        total_cycles = max(hbm_cycles, l2_cycles, l1_cycles, xbar_cycles)
        return {
            "hbm_cycles": hbm_cycles,
            "l2_cycles": l2_cycles,
            "l1_cycles": l1_cycles,
            "xbar_cycles": xbar_cycles,
            "total_cycles": total_cycles,
        }

    # -------------------------------------------------------------------------
    # Compute-path cycle model
    # -------------------------------------------------------------------------

    def _latency_hiding_penalty(self, active_warps: float) -> float:
        """Inflation when too few warps are resident to hide TC pipeline latency.

        A pipelined tensor core with latency ``L`` and initiation interval ``II``
        needs ``L/II`` independent in-flight instructions.  If resident warps are
        below that, effective throughput drops proportionally.
        """
        needed = math.ceil(
            self.spec.tc_latency_cycles / max(self.spec.tc_initiation_interval, 1)
        )
        efficiency = min(1.0, active_warps / max(needed, 1.0))
        return 1.0 + max(0.0, 1.0 - efficiency) * 0.5

    def _tc_mma_cycles(self, flops: float, cfg: FA4WorkloadDesc) -> float:
        """Cycles for tensor-core MMA ``flops`` at effective occupancy."""
        prec = cfg.normalized_precision
        rate_per_sm = self.spec.tc_mma_throughput_per_sm_per_clock.get(prec, 1024.0)
        active_sms = self._active_sms(cfg)
        scale = self._effective_compute_scale(cfg) * self.spec.tc_efficiency
        peak_flops_per_cycle = rate_per_sm * active_sms * scale
        throughput_cycles = flops / max(peak_flops_per_cycle, 1.0)
        penalty = self._latency_hiding_penalty(self._active_warps(cfg))
        return throughput_cycles * penalty / max(self.spec.operand_collector_efficiency, 1e-6)

    def _mufu_cycles(self, ops: float, cfg: FA4WorkloadDesc) -> float:
        """Cycles for MUFU/SFU ``ops`` (exp / reduction helpers)."""
        prec = cfg.normalized_precision
        rate_per_sm = self.spec.mufu_throughput_per_sm_per_clock.get(prec, 16.0)
        active_sms = self._active_sms(cfg)
        scale = self._effective_compute_scale(cfg) * self.spec.mufu_efficiency
        peak_ops_per_cycle = rate_per_sm * active_sms * scale
        return ops / max(peak_ops_per_cycle, 1.0)

    def _smem_reduction_cycles(
        self, rows: int, cols: int, active_sms: int
    ) -> float:
        """Cycles for row-wise reductions over a block_m x block_n tile.

        Each row performs a tree reduction of ``cols`` elements.  Modern FA4
        kernels use warp-shuffle instructions for most of this work, so the
        cost is much smaller than a full SMEM bandwidth bound.  We keep a
        lightweight term proportional to ``rows * log2(cols)``.
        """
        if rows <= 0 or cols <= 0:
            return 0.0
        steps = max(1, math.ceil(math.log2(cols)))
        # A few fractional cycles per row per step when spread across SMs.
        cycles_per_tile = rows * steps * 0.25 / max(active_sms, 1)
        return cycles_per_tile

    # -------------------------------------------------------------------------
    # Per-tile-block phase breakdown
    # -------------------------------------------------------------------------

    def _per_tile_block_cycles(self, cfg: FA4WorkloadDesc) -> Dict[str, Any]:
        """Return cycle breakdown for one representative tile block.

        A tile block corresponds to one output tile (block_m rows of the output)
        iterating over the KV dimension.  Fixed costs are the Q load and O store;
        per-KV-iteration costs are K load, V load, Q@K^T MMA, softmax, and P@V
        MMA.  The breakdown is returned in cycles and as a concise hop-level
        decomposition for the three memory transfers.
        """
        spec = self.spec
        block_m, block_n = self._tile_size_for_config(cfg)
        bpe = cfg.bytes_per_element
        active_sms = self._active_sms(cfg)

        # Bytes per tile.
        q_tile_bytes = block_m * cfg.head_dim * bpe
        kv_tile_bytes = block_n * cfg.head_dim * bpe
        s_tile_bytes = block_m * block_n * 4  # fp32 accumulator
        o_tile_bytes = block_m * cfg.head_dim * bpe

        # Memory transfers.
        q_load = self._memory_path_cycles(q_tile_bytes, active_sms, is_write=False)
        k_load = self._memory_path_cycles(kv_tile_bytes, active_sms, is_write=False)
        v_load = self._memory_path_cycles(kv_tile_bytes, active_sms, is_write=False)
        o_store = self._memory_path_cycles(o_tile_bytes, active_sms, is_write=True)

        # Compute.
        mma_flops_per_iter = 2.0 * block_m * block_n * cfg.head_dim
        qk_mma = self._tc_mma_cycles(mma_flops_per_iter, cfg)
        pv_mma = self._tc_mma_cycles(mma_flops_per_iter, cfg)

        exp_ops = block_m * block_n
        softmax_exp = self._mufu_cycles(exp_ops, cfg)
        softmax_reduction = self._smem_reduction_cycles(block_m, block_n, active_sms)
        softmax_cycles = max(softmax_exp, softmax_reduction)

        memory_per_iteration = k_load["total_cycles"] + v_load["total_cycles"]
        compute_per_iteration = qk_mma + softmax_cycles + pv_mma

        return {
            "q_load_cycles": q_load,
            "k_load_cycles": k_load,
            "v_load_cycles": v_load,
            "o_store_cycles": o_store,
            "qk_mma_cycles": qk_mma,
            "softmax_exp_cycles": softmax_exp,
            "softmax_reduction_cycles": softmax_reduction,
            "softmax_cycles": softmax_cycles,
            "pv_mma_cycles": pv_mma,
            "memory_per_iteration_cycles": memory_per_iteration,
            "compute_per_iteration_cycles": compute_per_iteration,
            "block_m": block_m,
            "block_n": block_n,
            "q_tile_bytes": q_tile_bytes,
            "kv_tile_bytes": kv_tile_bytes,
            "o_tile_bytes": o_tile_bytes,
        }

    # -------------------------------------------------------------------------
    # Aggregate prediction
    # -------------------------------------------------------------------------

    def predict(self, cfg: FA4WorkloadDesc) -> Dict[str, Any]:
        """Return predicted runtime and per-phase/per-component cycle breakdown."""
        spec = self.spec
        _, tiles_n, total_output_tiles = self._tile_counts(cfg)
        seq_factor = cfg.seq_factor
        # ``total_output_tiles`` counts B*H*tiles_m*tiles_n (m,n) work units.
        # For causal masking only about half of those units are active.
        total_iterations = total_output_tiles * seq_factor
        # Q and O are reused across the N dimension: one load/store per row tile.
        total_row_tiles = cfg.batch * cfg.heads * math.ceil(cfg.seqlen / self._tile_size_for_config(cfg)[0])

        tile = self._per_tile_block_cycles(cfg)
        active_sms = self._active_sms(cfg)

        # Aggregate fixed and per-iteration phases over all tile blocks.
        fixed_memory_cycles = (
            tile["q_load_cycles"]["total_cycles"] + tile["o_store_cycles"]["total_cycles"]
        ) * total_row_tiles
        iteration_memory_cycles = (
            tile["k_load_cycles"]["total_cycles"] + tile["v_load_cycles"]["total_cycles"]
        ) * total_iterations
        total_memory_cycles = fixed_memory_cycles + iteration_memory_cycles

        total_qk_mma_cycles = tile["qk_mma_cycles"] * total_iterations
        total_softmax_cycles = tile["softmax_cycles"] * total_iterations
        total_pv_mma_cycles = tile["pv_mma_cycles"] * total_iterations
        total_compute_cycles = total_qk_mma_cycles + total_softmax_cycles + total_pv_mma_cycles

        # Compute and memory overlap via prefetching; the memory side is only
        # partially hidden when compute is insufficient.
        overlap = spec.memory_overlap_factor
        visible_memory_cycles = total_memory_cycles * (1.0 - overlap)
        critical_path_cycles = max(total_compute_cycles, visible_memory_cycles)

        launch_cycles = spec.launch_overhead_us * spec.peak_sm_clock_mhz
        total_cycles = critical_path_cycles + launch_cycles
        runtime_us = total_cycles / spec.peak_sm_clock_mhz
        runtime_ms = runtime_us / 1000.0

        per_phase = {
            "q_load_cycles": tile["q_load_cycles"]["total_cycles"] * total_row_tiles,
            "k_load_cycles": tile["k_load_cycles"]["total_cycles"] * total_iterations,
            "v_load_cycles": tile["v_load_cycles"]["total_cycles"] * total_iterations,
            "o_store_cycles": tile["o_store_cycles"]["total_cycles"] * total_row_tiles,
            "qk_mma_cycles": total_qk_mma_cycles,
            "softmax_cycles": total_softmax_cycles,
            "pv_mma_cycles": total_pv_mma_cycles,
        }

        per_component = {
            "hbm_cycles": self._aggregate_component(
                tile, "hbm_cycles", total_row_tiles, total_iterations
            ),
            "l2_cycles": self._aggregate_component(
                tile, "l2_cycles", total_row_tiles, total_iterations
            ),
            "l1_cycles": self._aggregate_component(
                tile, "l1_cycles", total_row_tiles, total_iterations
            ),
            "xbar_cycles": self._aggregate_component(
                tile, "xbar_cycles", total_row_tiles, total_iterations
            ),
            "tc_mma_cycles": total_qk_mma_cycles + total_pv_mma_cycles,
            "mufu_cycles": tile["softmax_exp_cycles"] * total_iterations,
            "smem_reduction_cycles": tile["softmax_reduction_cycles"] * total_iterations,
        }

        phase_times = {k: v / spec.peak_sm_clock_mhz for k, v in per_phase.items()}
        component_times = {k: v / spec.peak_sm_clock_mhz for k, v in per_component.items()}

        if total_compute_cycles >= visible_memory_cycles:
            compute_parts = {
                "qk mma": per_phase["qk_mma_cycles"],
                "softmax": per_phase["softmax_cycles"],
                "pv mma": per_phase["pv_mma_cycles"],
            }
            dominant_bottleneck = max(compute_parts, key=compute_parts.get)  # type: ignore[arg-type]
        else:
            memory_parts = {
                "q load": per_phase["q_load_cycles"],
                "k load": per_phase["k_load_cycles"],
                "v load": per_phase["v_load_cycles"],
                "o store": per_phase["o_store_cycles"],
            }
            dominant_bottleneck = max(memory_parts, key=memory_parts.get)  # type: ignore[arg-type]

        return {
            "predicted_runtime_ms": runtime_ms,
            "predicted_runtime_us": runtime_us,
            "total_cycles": total_cycles,
            "critical_path_cycles": critical_path_cycles,
            "total_compute_cycles": total_compute_cycles,
            "total_memory_cycles": total_memory_cycles,
            "visible_memory_cycles": visible_memory_cycles,
            "per_phase_cycles": per_phase,
            "per_component_cycles": per_component,
            "per_phase_us": phase_times,
            "per_component_us": component_times,
            "dominant_bottleneck": dominant_bottleneck,
            "occupancy_fraction": self._occupancy_fraction(cfg),
            "active_warps": self._active_warps(cfg),
            "active_sms": active_sms,
            "total_output_tiles": total_output_tiles,
            "total_iterations": total_iterations,
            "tile_block": tile,
        }

    def _aggregate_component(
        self,
        tile: Dict[str, Any],
        component: str,
        total_output_tiles: float,
        total_iterations: float,
    ) -> float:
        """Sum a hop-level component across Q/K/V/O transfers."""
        q = tile["q_load_cycles"][component] * total_output_tiles
        k = tile["k_load_cycles"][component] * total_iterations
        v = tile["v_load_cycles"][component] * total_iterations
        o = tile["o_store_cycles"][component] * total_output_tiles
        return q + k + v + o


# -----------------------------------------------------------------------------
# Convenience wrappers
# -----------------------------------------------------------------------------


def default_b200_cycle_level_model() -> B200CycleLevelModel:
    """Return a ``B200CycleLevelModel`` with B200-calibrated defaults."""
    return B200CycleLevelModel()


def predict_runtime(
    batch: int,
    heads: int,
    seqlen: int,
    head_dim: int,
    causal: bool,
    precision: str,
    spec: Optional[B200CycleLevelModelSpec] = None,
) -> Dict[str, Any]:
    """One-shot convenience wrapper around ``B200CycleLevelModel.predict``."""
    cfg = FA4WorkloadDesc(
        batch=batch,
        heads=heads,
        seqlen=seqlen,
        head_dim=head_dim,
        causal=causal,
        precision=precision,
    )
    return B200CycleLevelModel(spec=spec).predict(cfg)


if __name__ == "__main__":
    demo = FA4WorkloadDesc(
        batch=2, heads=16, seqlen=2048, head_dim=128, causal=True, precision="fp16"
    )
    result = default_b200_cycle_level_model().predict(demo)
    print(f"demo predicted_runtime_ms = {result['predicted_runtime_ms']:.3f}")
    print(f"demo dominant_bottleneck  = {result['dominant_bottleneck']}")
