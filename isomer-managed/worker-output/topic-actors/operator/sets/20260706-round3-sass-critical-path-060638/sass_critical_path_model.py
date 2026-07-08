"""SASS-level instruction critical-path model for FlashAttention-4 on B200.

Round 3 refines the sub-core partition model by modelling the actual
instruction dependency graph inside one FA4 tile block.  Each node is a
SASS-level instruction class (TMA load, Tensor Core MMA, SFU exp, FP
scale/update, TMA store) with a measured issue rate and result latency.
Edges are read-after-write dependencies.  The critical path through the
DAG, scaled across iterations, gives the predicted runtime.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# -----------------------------------------------------------------------------
# Hardware specification
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class B200SASSCriticalPathModelSpec:
    """SASS instruction-level parameters for FA4 on B200."""

    # SM / clock
    num_sms: int = 176
    partitions_per_sm: int = 4
    peak_sm_clock_mhz: float = 1965.0
    max_warps_per_sm: int = 64
    threads_per_warp: int = 32

    # Per-partition issue throughput (instructions per cycle).
    tma_issues_per_partition_per_cycle: float = 1.0
    tc_issues_per_partition_per_cycle: float = 1.0
    sfu_issues_per_partition_per_cycle: float = 1.0
    fp_issues_per_partition_per_cycle: float = 1.0

    # Instruction latencies (cycles from issue to result ready).
    tma_load_latency_cycles: int = 48
    tc_mma_latency_cycles: int = 16
    sfu_exp_latency_cycles: int = 4
    fp_fma_latency_cycles: int = 6
    tma_store_latency_cycles: int = 24

    # Work per instruction.
    tc_flops_per_mma_inst: float = 4096.0
    sfu_ops_per_inst: float = 32.0
    fp_ops_per_inst: float = 128.0
    mem_bytes_per_transaction: float = 32.0

    # Global memory.
    peak_hbm_bw_gbps: float = 4480.0
    peak_l2_bw_gbps: float = 24000.0
    l2_hit_rate: float = 0.75

    # Occupancy / overlap.
    occupancy_efficiency: float = 1.0
    stage_overlap_factor: float = 0.85
    launch_overhead_us: float = 2.0

    # Efficiency scalars fit to measurements.
    tma_efficiency: float = 1.0
    tc_efficiency: float = 1.0
    sfu_efficiency: float = 1.0
    fp_efficiency: float = 1.0
    dependency_slack_factor: float = 1.0


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
# Instruction DAG node
# -----------------------------------------------------------------------------


@dataclass
class InstructionNode:
    """One SASS instruction class in the FA4 tile-block DAG."""

    name: str
    count: float  # instructions per tile block
    issue_rate_per_partition: float  # instructions per cycle per partition
    latency_cycles: int
    efficiency: float
    dependencies: List[str] = field(default_factory=list)


# -----------------------------------------------------------------------------
# SASS critical-path model
# -----------------------------------------------------------------------------


class B200SASSCriticalPathModel:
    """SASS-level instruction critical-path model for FA4 on B200.

    The model builds a minimal instruction DAG for one FA4 tile block,
    computes the critical path through the DAG accounting for both
    throughput (issue rate) and latency (dependencies), and scales it to
    the full forward pass.
    """

    def __init__(self, spec: Optional[B200SASSCriticalPathModelSpec] = None) -> None:
        self.spec = spec if spec is not None else B200SASSCriticalPathModelSpec()

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
    # Instruction DAG for one tile block
    # -------------------------------------------------------------------------

    def _instruction_dag(self, cfg: FA4WorkloadDesc) -> Dict[str, InstructionNode]:
        """Return the SASS instruction DAG for one representative tile block."""
        spec = self.spec
        block_m, block_n = self._tile_size_for_config(cfg)
        bpe = cfg.bytes_per_element

        # Memory transactions.
        q_trans = block_m * cfg.head_dim * bpe / spec.mem_bytes_per_transaction
        kv_trans = block_n * cfg.head_dim * bpe / spec.mem_bytes_per_transaction
        o_trans = q_trans

        # Compute instructions.
        mma_flops_per_iter = 2.0 * block_m * block_n * cfg.head_dim
        mma_inst = mma_flops_per_iter / spec.tc_flops_per_mma_inst

        exp_ops = block_m * block_n
        exp_inst = exp_ops / spec.sfu_ops_per_inst

        update_ops = block_m * cfg.head_dim * 2
        update_inst = update_ops / spec.fp_ops_per_inst

        return {
            "tma_load_q": InstructionNode(
                name="tma_load_q",
                count=q_trans,
                issue_rate_per_partition=spec.tma_issues_per_partition_per_cycle,
                latency_cycles=spec.tma_load_latency_cycles,
                efficiency=spec.tma_efficiency,
                dependencies=[],
            ),
            "tma_load_k": InstructionNode(
                name="tma_load_k",
                count=kv_trans,
                issue_rate_per_partition=spec.tma_issues_per_partition_per_cycle,
                latency_cycles=spec.tma_load_latency_cycles,
                efficiency=spec.tma_efficiency,
                dependencies=[],
            ),
            "mma_qk": InstructionNode(
                name="mma_qk",
                count=mma_inst,
                issue_rate_per_partition=spec.tc_issues_per_partition_per_cycle,
                latency_cycles=spec.tc_mma_latency_cycles,
                efficiency=spec.tc_efficiency,
                dependencies=["tma_load_q", "tma_load_k"],
            ),
            "sfu_exp": InstructionNode(
                name="sfu_exp",
                count=exp_inst,
                issue_rate_per_partition=spec.sfu_issues_per_partition_per_cycle,
                latency_cycles=spec.sfu_exp_latency_cycles,
                efficiency=spec.sfu_efficiency,
                dependencies=["mma_qk"],
            ),
            "fp_update": InstructionNode(
                name="fp_update",
                count=update_inst,
                issue_rate_per_partition=spec.fp_issues_per_partition_per_cycle,
                latency_cycles=spec.fp_fma_latency_cycles,
                efficiency=spec.fp_efficiency,
                dependencies=["sfu_exp"],
            ),
            "tma_load_v": InstructionNode(
                name="tma_load_v",
                count=kv_trans,
                issue_rate_per_partition=spec.tma_issues_per_partition_per_cycle,
                latency_cycles=spec.tma_load_latency_cycles,
                efficiency=spec.tma_efficiency,
                dependencies=[],
            ),
            "mma_pv": InstructionNode(
                name="mma_pv",
                count=mma_inst,
                issue_rate_per_partition=spec.tc_issues_per_partition_per_cycle,
                latency_cycles=spec.tc_mma_latency_cycles,
                efficiency=spec.tc_efficiency,
                dependencies=["fp_update", "tma_load_v"],
            ),
            "tma_store_o": InstructionNode(
                name="tma_store_o",
                count=o_trans,
                issue_rate_per_partition=spec.tma_issues_per_partition_per_cycle,
                latency_cycles=spec.tma_store_latency_cycles,
                efficiency=spec.tma_efficiency,
                dependencies=["mma_pv"],
            ),
        }

    def _critical_path_cycles(
        self, dag: Dict[str, InstructionNode], cfg: FA4WorkloadDesc
    ) -> Tuple[float, Dict[str, float]]:
        """Compute per-iteration throughput cycles plus latency-chain fill for the DAG."""
        spec = self.spec
        active_sms = self._active_sms(cfg)
        partitions = spec.partitions_per_sm
        scale = self._effective_compute_scale(cfg)

        earliest_start: Dict[str, float] = {name: 0.0 for name in dag}
        earliest_finish: Dict[str, float] = {name: 0.0 for name in dag}

        order = [
            "tma_load_q",
            "tma_load_k",
            "tma_load_v",
            "mma_qk",
            "sfu_exp",
            "fp_update",
            "mma_pv",
            "tma_store_o",
        ]

        for name in order:
            node = dag[name]
            issue_cycles = node.count / max(
                partitions * active_sms * node.issue_rate_per_partition * node.efficiency * scale,
                1e-9,
            )
            dep_finish = 0.0
            for dep in node.dependencies:
                dep_finish = max(dep_finish, earliest_finish[dep])
            start = max(earliest_start[name], dep_finish)
            finish = start + issue_cycles
            earliest_start[name] = start
            earliest_finish[name] = finish

        # Throughput-limited per-iteration critical path.
        throughput_cp = max(earliest_finish.values())

        # One-time latency chain along the longest dependency path.
        latency_chain = 0.0
        for name in order:
            node = dag[name]
            has_pred = any(dep in dag for dep in node.dependencies)
            has_succ = any(name in dag[d].dependencies for d in dag)
            if has_pred or has_succ:
                latency_chain += node.latency_cycles * spec.dependency_slack_factor

        return throughput_cp, latency_chain, earliest_finish

    def _memory_path_cycles(self, bytes_moved: float) -> float:
        """Global memory cycles for TMA/LDST traffic."""
        spec = self.spec
        bytes_per_cycle = spec.peak_hbm_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        miss_bytes = bytes_moved * (1.0 - spec.l2_hit_rate)
        l2_bytes_per_cycle = spec.peak_l2_bw_gbps * 1e9 / (spec.peak_sm_clock_mhz * 1e6)
        hbm_cycles = miss_bytes / max(bytes_per_cycle, 1.0)
        l2_cycles = bytes_moved * spec.l2_hit_rate / max(l2_bytes_per_cycle, 1.0)
        return max(hbm_cycles, l2_cycles)

    # -------------------------------------------------------------------------
    # Aggregate prediction
    # -------------------------------------------------------------------------

    def predict(self, cfg: FA4WorkloadDesc) -> Dict[str, Any]:
        """Return predicted runtime and SASS critical-path breakdown."""
        spec = self.spec
        block_m = self._tile_size_for_config(cfg)[0]
        _, tiles_n, total_output_tiles = self._tile_counts(cfg)
        seq_factor = cfg.seq_factor
        total_iterations = total_output_tiles * seq_factor
        total_row_tiles = cfg.batch * cfg.heads * math.ceil(cfg.seqlen / block_m)

        dag = self._instruction_dag(cfg)
        cp_per_iter, latency_chain, finish_times = self._critical_path_cycles(dag, cfg)

        # Per-iteration compute cycles scaled across all iterations, plus one-time latency chain.
        total_compute_cycles = cp_per_iter * total_iterations + latency_chain

        # Fixed Q load and O store per row tile.
        q_bytes = dag["tma_load_q"].count * spec.mem_bytes_per_transaction
        o_bytes = dag["tma_store_o"].count * spec.mem_bytes_per_transaction
        fixed_mem_cycles = (self._memory_path_cycles(q_bytes) + self._memory_path_cycles(o_bytes)) * total_row_tiles

        # K and V loads per iteration.
        kv_bytes = dag["tma_load_k"].count * spec.mem_bytes_per_transaction
        step_mem_cycles = self._memory_path_cycles(2.0 * kv_bytes) * total_iterations
        visible_memory = (fixed_mem_cycles + step_mem_cycles) * (1.0 - spec.stage_overlap_factor)

        critical_path_cycles = max(total_compute_cycles, visible_memory)
        launch_cycles = spec.launch_overhead_us * spec.peak_sm_clock_mhz
        total_cycles = critical_path_cycles + launch_cycles
        runtime_us = total_cycles / spec.peak_sm_clock_mhz
        runtime_ms = runtime_us / 1000.0

        # Dominant instruction on critical path.
        critical_node = max(finish_times, key=lambda k: finish_times[k])

        return {
            "predicted_runtime_ms": runtime_ms,
            "predicted_runtime_us": runtime_us,
            "total_cycles": total_cycles,
            "critical_path_cycles": critical_path_cycles,
            "total_compute_cycles": total_compute_cycles,
            "visible_memory_cycles": visible_memory,
            "per_instruction_finish_cycles": finish_times,
            "dominant_instruction": critical_node,
            "active_sms": self._active_sms(cfg),
            "total_iterations": total_iterations,
            "total_row_tiles": total_row_tiles,
            "dag": dag,
        }


# -----------------------------------------------------------------------------
# Convenience wrappers
# -----------------------------------------------------------------------------


def default_b200_sass_critical_path_model() -> B200SASSCriticalPathModel:
    return B200SASSCriticalPathModel()


def predict_runtime(
    batch: int,
    heads: int,
    seqlen: int,
    head_dim: int,
    causal: bool,
    precision: str,
    spec: Optional[B200SASSCriticalPathModelSpec] = None,
) -> Dict[str, Any]:
    cfg = FA4WorkloadDesc(
        batch=batch,
        heads=heads,
        seqlen=seqlen,
        head_dim=head_dim,
        causal=causal,
        precision=precision,
    )
    return B200SASSCriticalPathModel(spec=spec).predict(cfg)


if __name__ == "__main__":
    demo = FA4WorkloadDesc(
        batch=2, heads=16, seqlen=2048, head_dim=128, causal=True, precision="fp16"
    )
    result = default_b200_sass_critical_path_model().predict(demo)
    print(f"demo predicted_runtime_ms = {result['predicted_runtime_ms']:.3f}")
    print(f"demo dominant_instruction = {result['dominant_instruction']}")
