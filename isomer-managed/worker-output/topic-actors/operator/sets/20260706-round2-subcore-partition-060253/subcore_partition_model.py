"""Sub-core partition scheduling model for FlashAttention-4 on B200.

Round 2 refines the per-SM reservation model by modelling each SM as four
independent sub-core partitions.  Each partition has its own warp scheduler and
can issue one instruction per cycle to one of its execution units.  Warps are
distributed across partitions, and the SM is bottlenecked by the busiest
partition.  This captures intra-SM scheduling constraints that the single-pool
reservation model cannot represent.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# -----------------------------------------------------------------------------
# Hardware specification
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class B200SubcorePartitionModelSpec:
    """Sub-core partition scheduling parameters for FA4 on B200."""

    # SM / clock
    num_sms: int = 176
    partitions_per_sm: int = 4
    peak_sm_clock_mhz: float = 1965.0
    max_warps_per_sm: int = 64
    threads_per_warp: int = 32

    # Per-partition issue throughput (instructions per cycle per partition).
    # One partition can issue one warp instruction per cycle to one unit.
    tc_issues_per_partition_per_cycle: float = 1.0
    sfu_issues_per_partition_per_cycle: float = 1.0
    fp_issues_per_partition_per_cycle: float = 1.0
    mem_issues_per_partition_per_cycle: float = 1.0

    # Work per instruction.
    tc_flops_per_mma_inst: float = 4096.0  # one warp-group mma.sync
    sfu_ops_per_inst: float = 32.0  # one warp exp
    fp_ops_per_inst: float = 128.0  # four warp FMAs
    mem_bytes_per_transaction: float = 32.0  # one 32-byte TMA/LDST transaction

    # Pipeline latencies (used only for small-grid fill/drain overhead).
    tc_latency_cycles: int = 16
    sfu_latency_cycles: int = 4
    fp_latency_cycles: int = 6
    mem_latency_cycles: int = 48

    # Memory hierarchy (global).
    peak_hbm_bw_gbps: float = 4480.0
    peak_l2_bw_gbps: float = 24000.0
    l2_hit_rate: float = 0.75

    # Occupancy / overlap.
    occupancy_efficiency: float = 1.0
    stage_overlap_factor: float = 0.85
    launch_overhead_us: float = 2.0

    # Efficiency scalars fit to measurements.
    tc_efficiency: float = 1.0
    sfu_efficiency: float = 1.0
    fp_efficiency: float = 1.0
    mem_efficiency: float = 1.0
    partition_imbalance_factor: float = 0.0


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
# Sub-core partition model
# -----------------------------------------------------------------------------


class B200SubcorePartitionModel:
    """Sub-core partition scheduling model for FA4 on B200.

    Each SM is modelled as ``partitions_per_sm`` independent schedulers.
    Instructions are distributed across partitions according to warp
    assignment, and the SM runtime is the busiest partition's makespan.
    """

    def __init__(self, spec: Optional[B200SubcorePartitionModelSpec] = None) -> None:
        self.spec = spec if spec is not None else B200SubcorePartitionModelSpec()

    # -------------------------------------------------------------------------
    # Tile geometry and parallelism
    # -------------------------------------------------------------------------

    def _tile_size_for_config(self, cfg: FA4WorkloadDesc) -> tuple[int, int]:
        defaults: Dict[int, tuple[int, int]] = {
            64: (128, 128),
            128: (128, 64),
            256: (64, 64),
        }
        return defaults.get(cfg.head_dim, (128, 64))

    def _tile_counts(self, cfg: FA4WorkloadDesc) -> tuple[int, int, int]:
        block_m, block_n = self._tile_size_for_config(cfg)
        tiles_m = math.ceil(cfg.seqlen / block_m)
        tiles_n = math.ceil(cfg.seqlen / block_n)
        total_output_tiles = cfg.batch * cfg.heads * tiles_m * tiles_n
        return tiles_m, tiles_n, total_output_tiles

    def _active_sms(self, cfg: FA4WorkloadDesc) -> int:
        _, _, total_output_tiles = self._tile_counts(cfg)
        return min(self.spec.num_sms, max(1, total_output_tiles))

    def _active_warps(self, cfg: FA4WorkloadDesc) -> float:
        _, _, total_output_tiles = self._tile_counts(cfg)
        warps_per_tile = 4
        required = total_output_tiles * warps_per_tile
        max_device_warps = self.spec.num_sms * self.spec.max_warps_per_sm
        return max(1.0, min(required, max_device_warps))

    def _occupancy_fraction(self, cfg: FA4WorkloadDesc) -> float:
        active = self._active_warps(cfg)
        max_warps = self.spec.num_sms * self.spec.max_warps_per_sm
        frac = active / max_warps
        return min(1.0, math.sqrt(max(0.0, frac)) * 0.95 + 0.05)

    def _effective_compute_scale(self, cfg: FA4WorkloadDesc) -> float:
        return self._occupancy_fraction(cfg) * self.spec.occupancy_efficiency

    # -------------------------------------------------------------------------
    # Instruction counts and partition scheduling
    # -------------------------------------------------------------------------

    def _latency_hiding_penalty(self, active_warps: float) -> float:
        needed = math.ceil(
            self.spec.tc_latency_cycles / max(self.spec.tc_issues_per_partition_per_cycle, 1)
        )
        efficiency = min(1.0, active_warps / max(needed, 1.0))
        return 1.0 + max(0.0, 1.0 - efficiency) * 0.5

    def _per_step_instructions(self, cfg: FA4WorkloadDesc) -> Dict[str, float]:
        """Return instruction counts for one KV step of a representative tile."""
        spec = self.spec
        block_m, block_n = self._tile_size_for_config(cfg)
        bpe = cfg.bytes_per_element

        # MMA instructions: one warp-group MMA per block_m x block_n x head_dim tile.
        mma_flops_per_iter = 2.0 * block_m * block_n * cfg.head_dim
        mma_inst = mma_flops_per_iter / spec.tc_flops_per_mma_inst

        # Softmax instructions.
        exp_ops = block_m * block_n
        exp_inst = exp_ops / spec.sfu_ops_per_inst
        update_ops = block_m * cfg.head_dim * 2
        update_inst = update_ops / spec.fp_ops_per_inst

        # Memory transactions: K and V loads per step.
        kv_tile_bytes = block_n * cfg.head_dim * bpe
        mem_inst_per_kv = kv_tile_bytes / spec.mem_bytes_per_transaction

        return {
            "mma_inst": mma_inst,
            "exp_inst": exp_inst,
            "update_inst": update_inst,
            "mem_inst": 2.0 * mem_inst_per_kv,  # K + V
            "q_load_inst": (block_m * cfg.head_dim * bpe) / spec.mem_bytes_per_transaction,
            "o_store_inst": (block_m * cfg.head_dim * bpe) / spec.mem_bytes_per_transaction,
        }

    def _partition_cycles_for_instructions(
        self, instructions: Dict[str, float], cfg: FA4WorkloadDesc
    ) -> Dict[str, float]:
        """Compute per-partition cycles assuming balanced warp distribution."""
        spec = self.spec
        active_sms = self._active_sms(cfg)
        scale = self._effective_compute_scale(cfg)
        partitions = spec.partitions_per_sm

        # Total instructions across all SMs for this step.
        total_mma = instructions["mma_inst"]
        total_exp = instructions["exp_inst"]
        total_update = instructions["update_inst"]
        total_mem = instructions["mem_inst"]

        # Instructions per partition per SM.
        mma_per_part = total_mma / (active_sms * partitions * spec.tc_efficiency)
        exp_per_part = total_exp / (active_sms * partitions * spec.sfu_efficiency)
        update_per_part = total_update / (active_sms * partitions * spec.fp_efficiency)
        mem_per_part = total_mem / (active_sms * partitions * spec.mem_efficiency)

        # Each partition serializes its instructions through one scheduler.
        mma_cycles = mma_per_part / spec.tc_issues_per_partition_per_cycle
        exp_cycles = exp_per_part / spec.sfu_issues_per_partition_per_cycle
        update_cycles = update_per_part / spec.fp_issues_per_partition_per_cycle
        mem_cycles = mem_per_part / spec.mem_issues_per_partition_per_cycle

        # Latency-hiding penalty for small grids.
        penalty = self._latency_hiding_penalty(self._active_warps(cfg))
        mma_cycles *= penalty

        return {
            "mma_cycles": mma_cycles,
            "exp_cycles": exp_cycles,
            "update_cycles": update_cycles,
            "mem_cycles": mem_cycles,
            "partition_total_cycles": mma_cycles + exp_cycles + update_cycles + mem_cycles,
        }

    def _memory_path_cycles(self, bytes_moved: float) -> float:
        """Global memory cycles for TMA/LDST traffic."""
        spec = self.spec
        bytes_per_cycle = spec.peak_hbm_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        miss_bytes = bytes_moved * (1.0 - spec.l2_hit_rate)
        l2_bytes_per_cycle = spec.peak_l2_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        hbm_cycles = miss_bytes / max(bytes_per_cycle, 1.0)
        l2_cycles = bytes_moved * spec.l2_hit_rate / max(l2_bytes_per_cycle, 1.0)
        return max(hbm_cycles, l2_cycles)

    def _per_step_cycles(self, cfg: FA4WorkloadDesc) -> Dict[str, Any]:
        """Return per-step cycles and component breakdown."""
        spec = self.spec
        inst = self._per_step_instructions(cfg)
        part = self._partition_cycles_for_instructions(inst, cfg)

        # Global memory bandwidth cycles for the K+V loads in this step.
        mem_bw_cycles = self._memory_path_cycles(
            inst["mem_inst"] * spec.mem_bytes_per_transaction
        )

        # The compute side is the busiest partition across all SMs.
        compute_cycles = part["partition_total_cycles"]

        # Imbalance penalty: if instructions do not split evenly across partitions,
        # the busiest partition may be up to (partitions - 1) extra instructions.
        imbalance = 1.0 + spec.partition_imbalance_factor * (
            1.0 - 1.0 / max(partitions := spec.partitions_per_sm, 1)
        )
        compute_cycles *= imbalance

        return {
            "compute_cycles": compute_cycles,
            "mem_bw_cycles": mem_bw_cycles,
            "partition_cycles": part,
            "instructions": inst,
        }

    # -------------------------------------------------------------------------
    # Aggregate prediction
    # -------------------------------------------------------------------------

    def predict(self, cfg: FA4WorkloadDesc) -> Dict[str, Any]:
        """Return predicted runtime and per-partition scheduling breakdown."""
        spec = self.spec
        block_m = self._tile_size_for_config(cfg)[0]
        _, tiles_n, total_output_tiles = self._tile_counts(cfg)
        seq_factor = cfg.seq_factor
        total_iterations = total_output_tiles * seq_factor
        total_row_tiles = cfg.batch * cfg.heads * math.ceil(cfg.seqlen / block_m)

        step = self._per_step_cycles(cfg)

        # Fixed Q load / O store per row tile.
        fixed_mem_cycles = (
            self._memory_path_cycles(
                self._per_step_instructions(cfg)["q_load_inst"] * spec.mem_bytes_per_transaction
            )
            + self._memory_path_cycles(
                self._per_step_instructions(cfg)["o_store_inst"] * spec.mem_bytes_per_transaction
            )
        ) * total_row_tiles

        step_compute = step["compute_cycles"] * total_iterations
        step_memory = step["mem_bw_cycles"] * total_iterations
        visible_memory = (fixed_mem_cycles + step_memory) * (1.0 - spec.stage_overlap_factor)

        critical_path_cycles = max(step_compute, visible_memory)
        launch_cycles = spec.launch_overhead_us * spec.peak_sm_clock_mhz
        total_cycles = critical_path_cycles + launch_cycles
        runtime_us = total_cycles / spec.peak_sm_clock_mhz
        runtime_ms = runtime_us / 1000.0

        per_partition = step["partition_cycles"]
        bottleneck = max(
            {
                "mma": per_partition["mma_cycles"],
                "sfu": per_partition["exp_cycles"],
                "fp": per_partition["update_cycles"],
                "mem": per_partition["mem_cycles"],
            },
            key=lambda k: {
                "mma": per_partition["mma_cycles"],
                "sfu": per_partition["exp_cycles"],
                "fp": per_partition["update_cycles"],
                "mem": per_partition["mem_cycles"],
            }[k],
        )

        return {
            "predicted_runtime_ms": runtime_ms,
            "predicted_runtime_us": runtime_us,
            "total_cycles": total_cycles,
            "critical_path_cycles": critical_path_cycles,
            "total_compute_cycles": step_compute,
            "visible_memory_cycles": visible_memory,
            "per_partition_cycles": per_partition,
            "dominant_partition_bottleneck": bottleneck,
            "active_sms": self._active_sms(cfg),
            "total_iterations": total_iterations,
            "total_row_tiles": total_row_tiles,
            "step": step,
        }


# -----------------------------------------------------------------------------
# Convenience wrappers
# -----------------------------------------------------------------------------


def default_b200_subcore_partition_model() -> B200SubcorePartitionModel:
    return B200SubcorePartitionModel()


def predict_runtime(
    batch: int,
    heads: int,
    seqlen: int,
    head_dim: int,
    causal: bool,
    precision: str,
    spec: Optional[B200SubcorePartitionModelSpec] = None,
) -> Dict[str, Any]:
    cfg = FA4WorkloadDesc(
        batch=batch,
        heads=heads,
        seqlen=seqlen,
        head_dim=head_dim,
        causal=causal,
        precision=precision,
    )
    return B200SubcorePartitionModel(spec=spec).predict(cfg)


if __name__ == "__main__":
    demo = FA4WorkloadDesc(
        batch=2, heads=16, seqlen=2048, head_dim=128, causal=True, precision="fp16"
    )
    result = default_b200_subcore_partition_model().predict(demo)
    print(f"demo predicted_runtime_ms = {result['predicted_runtime_ms']:.3f}")
    print(f"demo dominant_partition_bottleneck = {result['dominant_partition_bottleneck']}")
