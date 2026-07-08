"""Inner-GPU analytical model for FlashAttention-4 on NVIDIA B200.

This module extends the existing white-box FA4 predictor with per-component
bounds inspired by AccelSim/GPGPU-Sim: warp-scheduler issue throughput,
tensor-core MMA issue rate, execution-unit pipelining/occupancy, L1/L2 cache
traffic, HBM row-locality/bank-level-parallelism, and crossbar contention.

It is intentionally *not* a cycle-accurate simulator.  All bounds are closed-form
or simple queueing approximations so the model stays interpretable and fast.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# -----------------------------------------------------------------------------
# Hardware specification
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class B200InnerGPUModelSpec:
    """Hardware parameters for the inner-GPU analytical model.

    Defaults are calibrated to public B200 rough specs and the host spec in
    ``host-b200-spec.md`` (peak SM clock 1,965 MHz, ~180 SMs).  They can be
    overridden for sensitivity studies.
    """

    # SM / clock
    num_sms: int = 180
    peak_sm_clock_mhz: float = 1965.0
    max_warps_per_sm: int = 64
    threads_per_warp: int = 32

    # Warp scheduler: maximum warp instructions issued per scheduler per cycle.
    # Volta-and-later GPUs issue one warp instruction per scheduler per cycle.
    schedulers_per_sm: int = 4
    warp_inst_issue_per_scheduler_per_cycle: float = 1.0

    # Tensor Core MMA throughput (FLOPs per SM per clock) for FA4-like tiles.
    mma_throughput_per_sm_per_clock: Dict[str, float] = field(
        default_factory=lambda: {
            "fp32": 1024.0,
            "fp16": 2048.0,
            "bf16": 2048.0,
            "fp8": 4096.0,
            "fp4": 8192.0,
        }
    )

    # MUFU (exp / softmax) throughput per SM per clock.
    mufu_throughput_per_sm_per_clock: Dict[str, float] = field(
        default_factory=lambda: {
            "fp32": 16.0,
            "fp16": 16.0,
            "bf16": 16.0,
            "fp8": 16.0,
            "fp4": 16.0,
        }
    )

    # Tensor-core pipeline: latency and initiation interval.  A deeply pipelined
    # Blackwell TC unit can accept a new warp instruction every cycle while the
    # previous results drain after ``tc_latency`` cycles.
    tc_latency_cycles: int = 16
    tc_initiation_interval: int = 1

    # MUFU/SFU pipeline latency (cycles).
    mufu_latency_cycles: int = 4

    # Register / operand-collector backpressure.  Each warp instruction needs at
    # least one scheduler slot and enough free operand-collector/register-file
    # bandwidth.  We capture residual friction with a scalar efficiency.
    operand_collector_efficiency: float = 0.92

    # Memory hierarchy
    peak_hbm_bw_gbps: float = 4480.0  # ~4.5 TB/s sustained on B200
    peak_l2_bw_gbps: float = 24000.0  # aggregate L2 read bandwidth estimate
    peak_l1_bw_gbps: float = 48000.0  # aggregate L1 read bandwidth estimate

    # Cache geometry and miss rates (configurable; defaults are FA4-oriented).
    l1_line_bytes: int = 128
    l1_sector_bytes: int = 32
    l1_miss_rate: float = 0.08
    l2_miss_rate: float = 0.25

    # HBM bank/timing parameters used by the DRAM bandwidth model.
    hbm_num_banks: int = 16
    hbm_num_bank_groups: int = 4
    hbm_row_buffer_hit_rate: float = 0.65
    hbm_read_fraction: float = 0.75
    # Average read/write turnaround penalty expressed as a bandwidth tax.
    hbm_rw_turnaround_tax: float = 0.10

    # Interconnect / crossbar contention.
    num_memory_partitions: int = 16
    xbar_ideal_cycles_per_flit: float = 1.0
    xbar_contention_exponent: float = 1.5

    # Fixed kernel-launch and per-tile dispatch overheads.
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
# Model
# -----------------------------------------------------------------------------


class B200InnerGPUModel:
    """Analytical inner-GPU runtime model for FlashAttention-4 on B200.

    The model replaces the coarse ``max(FLOPs/peak, bytes/bandwidth)`` roofline
    with per-component bounds:

    1. **Compute-issue bound** — warp-scheduler instruction issue throughput.
    2. **Tensor-core throughput bound** — MMA FLOPs / effective tensor-core rate.
    3. **Execution-pipeline / occupancy bound** — latency hiding limited by
       resident warps.
    4. **Memory-pipeline bound** — L1/L2/HBM traffic with configurable miss
       rates and HBM row-locality / bank-level-parallelism effects.
    5. **Interconnect bound** — crossbar contention when many SMs miss together.

    The predicted runtime is the maximum of the bounds plus a small launch
    overhead.  This mirrors the ``max(compute, memory)`` overlap assumption used
    by the existing predictor, but exposes the inner-GPU mechanisms that produce
    each bound.

    Example::

        model = B200InnerGPUModel()
        result = model.predict(FA4WorkloadDesc(
            batch=4, heads=32, seqlen=4096, head_dim=128,
            causal=True, precision="fp16",
        ))
        print(result["predicted_runtime_ms"], result["dominant_bottleneck"])
    """

    def __init__(self, spec: Optional[B200InnerGPUModelSpec] = None) -> None:
        self.spec = spec if spec is not None else B200InnerGPUModelSpec()

    # -------------------------------------------------------------------------
    # Workload decomposition
    # -------------------------------------------------------------------------

    def workload_quantities(self, cfg: FA4WorkloadDesc) -> Dict[str, float]:
        """Return white-box algorithmic quantities for ``cfg``."""
        b, h, s, d = cfg.batch, cfg.heads, cfg.seqlen, cfg.head_dim
        bpe = cfg.bytes_per_element
        seq_factor = cfg.seq_factor

        # FA4 forward FLOPs: Q@K^T + P@V, each is 2*B*H*S^2*D.
        mma_flops = 4.0 * b * h * (s * s) * d * seq_factor

        # Softmax exp ops plus row reductions.
        exp_ops = 2.0 * b * h * (s * s) * seq_factor

        # HBM traffic: Q, K, V reads and O write.
        hbm_bytes = bpe * b * h * s * d * 4.0

        # L2 traffic: tiles streamed through L2.
        l2_bytes = bpe * b * h * s * d * 6.0 * seq_factor

        # L1 traffic: repeated accesses to tile fragments.
        l1_bytes = bpe * b * h * s * d * 12.0 * seq_factor

        # Shared-memory traffic: inter-SMEM traffic inside a kernel.
        smem_bytes = b * h * s * d * 8.0 * seq_factor

        # TMA traffic.
        tma_bytes = bpe * b * h * s * d * 2.5 * seq_factor

        # Number of output tiles.  Assumes default FA4 tiles.
        block_m, block_n = self._tile_size_for_config(cfg)
        tiles_m = math.ceil(s / block_m)
        tiles_n = math.ceil(s / block_n)
        total_tiles = b * h * tiles_m * tiles_n

        # Warp instruction counts (approximate).
        # Each output tile performs a sequence of MMA, softmax, and memory ops.
        mma_inst_per_tile = max(1.0, (s * s * d * seq_factor) / (block_m * block_n * 64.0))
        mem_inst_per_tile = max(1.0, hbm_bytes / (bpe * total_tiles * 64.0)) if total_tiles else 1.0
        mufu_inst_per_tile = max(1.0, exp_ops / total_tiles / 32.0) if total_tiles else 1.0

        total_mma_insts = total_tiles * mma_inst_per_tile
        total_mem_insts = total_tiles * mem_inst_per_tile
        total_mufu_insts = total_tiles * mufu_inst_per_tile

        return {
            "mma_flops": mma_flops,
            "exp_ops": exp_ops,
            "hbm_bytes": hbm_bytes,
            "l2_bytes": l2_bytes,
            "l1_bytes": l1_bytes,
            "smem_bytes": smem_bytes,
            "tma_bytes": tma_bytes,
            "total_tiles": total_tiles,
            "warps_per_tile": 4,
            "total_mma_insts": total_mma_insts,
            "total_mem_insts": total_mem_insts,
            "total_mufu_insts": total_mufu_insts,
        }

    def _tile_size_for_config(self, cfg: FA4WorkloadDesc) -> tuple[int, int]:
        """Return (block_m, block_n) heuristics for ``cfg``."""
        defaults: Dict[int, tuple[int, int]] = {
            64: (128, 128),
            128: (128, 64),
            256: (64, 64),
        }
        return defaults.get(cfg.head_dim, (128, 64))

    # -------------------------------------------------------------------------
    # Occupancy and parallelism helpers
    # -------------------------------------------------------------------------

    def active_warps(self, cfg: FA4WorkloadDesc, workload: Dict[str, float]) -> float:
        """Resident warps across the device, limited by tile geometry."""
        required = workload["total_tiles"] * workload["warps_per_tile"]
        max_device_warps = self.spec.num_sms * self.spec.max_warps_per_sm
        return max(1.0, min(required, max_device_warps))

    def occupancy_fraction(self, cfg: FA4WorkloadDesc, workload: Dict[str, float]) -> float:
        """Fraction of theoretical throughput reachable given occupancy."""
        active = self.active_warps(cfg, workload)
        max_warps = self.spec.num_sms * self.spec.max_warps_per_sm
        frac = active / max_warps
        # Throughput scales roughly with sqrt of occupancy at low occupancy, then
        # saturates.  This matches the existing predictor's shape.
        return min(1.0, math.sqrt(max(0.0, frac)) * 0.95 + 0.05)

    # -------------------------------------------------------------------------
    # Compute bounds
    # -------------------------------------------------------------------------

    def compute_issue_bound_us(
        self, cfg: FA4WorkloadDesc, workload: Dict[str, float]
    ) -> float:
        """Time bounded by warp-scheduler issue throughput (instructions/cycle).

        AccelSim's ``scheduler_unit::cycle`` issues at most one warp instruction
        per scheduler per cycle.  The bound is therefore total warp instructions
        divided by ``schedulers_per_sm * issue_rate * num_sms * clock``.
        """
        total_insts = (
            workload["total_mma_insts"]
            + workload["total_mem_insts"]
            + workload["total_mufu_insts"]
        )
        issue_rate_per_sm = (
            self.spec.schedulers_per_sm
            * self.spec.warp_inst_issue_per_scheduler_per_cycle
        )
        total_issue_rate = (
            issue_rate_per_sm
            * self.spec.num_sms
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * self.spec.operand_collector_efficiency
        )
        return (total_insts / max(total_issue_rate, 1.0)) * 1e6

    def tensor_core_throughput_bound_us(
        self, cfg: FA4WorkloadDesc, workload: Dict[str, float]
    ) -> float:
        """Time bounded by tensor-core MMA FLOP throughput."""
        prec = cfg.normalized_precision
        rate_per_sm = self.spec.mma_throughput_per_sm_per_clock.get(prec, 1024.0)
        occ = self.occupancy_fraction(cfg, workload)
        total_rate = (
            rate_per_sm
            * self.spec.num_sms
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * occ
        )
        return (workload["mma_flops"] / max(total_rate, 1.0)) * 1e6

    def mufu_throughput_bound_us(
        self, cfg: FA4WorkloadDesc, workload: Dict[str, float]
    ) -> float:
        """Time bounded by MUFU (exp/softmax) throughput."""
        prec = cfg.normalized_precision
        rate_per_sm = self.spec.mufu_throughput_per_sm_per_clock.get(prec, 16.0)
        occ = self.occupancy_fraction(cfg, workload)
        total_rate = (
            rate_per_sm
            * self.spec.num_sms
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * occ
        )
        return (workload["exp_ops"] / max(total_rate, 1.0)) * 1e6

    def execution_pipeline_bound_us(
        self, cfg: FA4WorkloadDesc, workload: Dict[str, float]
    ) -> float:
        """Latency-hiding bound from pipelined execution units.

        A pipelined unit with latency ``L`` and initiation interval ``II`` needs
        at least ``L / II`` independent in-flight instructions to hide latency.
        If occupancy is lower, the effective throughput is scaled by the ratio of
        resident warps to the latency-hiding requirement.
        """
        occ = self.occupancy_fraction(cfg, workload)
        # Latency-hiding requirement approximated from the TC pipeline.
        needed_warps_for_latency_hiding = math.ceil(
            self.spec.tc_latency_cycles / max(self.spec.tc_initiation_interval, 1)
        )
        active = self.active_warps(cfg, workload)
        # Fraction of ideal throughput reachable from latency hiding alone.
        latency_hiding_efficiency = min(
            1.0, active / max(needed_warps_for_latency_hiding, 1.0)
        )
        # Combine occupancy and latency-hiding effects; the pipeline bound is
        # expressed as an inflation over the pure throughput bound.
        inflation = 1.0 + max(0.0, 1.0 - latency_hiding_efficiency) * 0.5
        tc_time = self.tensor_core_throughput_bound_us(cfg, workload)
        return tc_time * inflation

    # -------------------------------------------------------------------------
    # Memory bounds
    # -------------------------------------------------------------------------

    def l1_cache_traffic(self, cfg: FA4WorkloadDesc, workload: Dict[str, float]) -> float:
        """Estimated L1 traffic including sector misses."""
        # Fraction of L1 accesses that miss and must be forwarded to L2.
        miss_bytes = workload["l1_bytes"] * self.spec.l1_miss_rate
        # Each sector miss fetches a full sector (32 B by default).
        sector_overfetch = math.ceil(self.spec.l1_sector_bytes / max(cfg.bytes_per_element, 1))
        return miss_bytes * (1.0 + (sector_overfetch - 1.0) * 0.25)

    def l2_cache_traffic(self, cfg: FA4WorkloadDesc, workload: Dict[str, float]) -> float:
        """Estimated L2 traffic forwarded to HBM."""
        l1_miss_bytes = self.l1_cache_traffic(cfg, workload)
        return l1_miss_bytes * self.spec.l2_miss_rate

    def hbm_effective_bw_bytes_per_s(
        self, cfg: FA4WorkloadDesc, workload: Dict[str, float]
    ) -> float:
        """HBM effective bandwidth with row locality, BLP, and R/W turnaround."""
        peak = self.spec.peak_hbm_bw_gbps * 1e9

        # Row-locality factor: open-row hits need no ACT/PRE.
        row_locality_factor = (
            self.spec.hbm_row_buffer_hit_rate
            + (1.0 - self.spec.hbm_row_buffer_hit_rate) * 0.35
        )

        # Bank-level parallelism factor.  With many independent requests the
        # memory controller can keep more banks busy; with few requests BLP
        # collapses.  We approximate with a saturating curve over the number of
        # active SMs and banks.
        active_sms = min(self.spec.num_sms, workload["total_tiles"])
        blp = min(
            self.spec.hbm_num_banks * self.spec.num_memory_partitions / 2.0,
            active_sms * self.spec.schedulers_per_sm,
        )
        blp_factor = min(1.0, blp / self.spec.hbm_num_banks)

        # Read/write turnaround tax.  Writes are a minority in FA4 forward pass.
        rw = self.spec.hbm_read_fraction
        rw_factor = 1.0 - self.spec.hbm_rw_turnaround_tax * (1.0 - abs(rw - (1.0 - rw)))

        return peak * row_locality_factor * blp_factor * rw_factor

    def memory_pipeline_bound_us(
        self, cfg: FA4WorkloadDesc, workload: Dict[str, float]
    ) -> float:
        """Dominant memory-pipeline bound (L1/L2/HBM)."""
        l1_miss_bytes = self.l1_cache_traffic(cfg, workload)
        l2_miss_bytes = self.l2_cache_traffic(cfg, workload)
        hbm_bytes = workload["hbm_bytes"]

        l1_time = l1_miss_bytes / max(self.spec.peak_l1_bw_gbps * 1e9, 1.0)
        l2_time = l2_miss_bytes / max(self.spec.peak_l2_bw_gbps * 1e9, 1.0)
        hbm_bw = self.hbm_effective_bw_bytes_per_s(cfg, workload)
        hbm_time = hbm_bytes / max(hbm_bw, 1.0)

        return max(l1_time, l2_time, hbm_time) * 1e6

    # -------------------------------------------------------------------------
    # Interconnect / crossbar bound
    # -------------------------------------------------------------------------

    def interconnect_contention_factor(
        self, cfg: FA4WorkloadDesc, workload: Dict[str, float]
    ) -> float:
        """Crossbar/NoC contention factor when many SMs miss simultaneously.

        GPGPU-Sim's ``local_interconnect`` uses input-queued routers with
        round-robin / iSLIP arbitration.  When many SMs inject misses into few
        memory partitions, output-port conflicts serialize traffic.  We model
        this with a simple queueing approximation: contention grows as
        ``(active_sms / partitions) ** exponent`` up to a cap.
        """
        active_sms = min(self.spec.num_sms, max(1, workload["total_tiles"]))
        load = active_sms / max(self.spec.num_memory_partitions, 1)
        factor = 1.0 + (load ** self.spec.xbar_contention_exponent) * 0.08
        return min(factor, 2.0)

    def interconnect_bound_us(
        self, cfg: FA4WorkloadDesc, workload: Dict[str, float]
    ) -> float:
        """Additional latency from crossbar/NoC contention.

        This bound is expressed as an additive latency on top of the HBM time,
        proportional to the number of miss-causing flits and the contention
        factor.  It is usually small compared with HBM transfer time for large
        FA4 kernels but becomes visible for small batches.
        """
        contention = self.interconnect_contention_factor(cfg, workload)
        # Flit count: one flit per cache line / sector miss to each partition.
        l2_miss_bytes = self.l2_cache_traffic(cfg, workload)
        flits = l2_miss_bytes / max(self.spec.l1_sector_bytes, 1)
        # Aggregate ideal crossbar throughput (flits/cycle) across partitions.
        ideal_flit_rate = (
            self.spec.num_memory_partitions
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * self.spec.xbar_ideal_cycles_per_flit
        )
        return (flits / max(ideal_flit_rate / contention, 1.0)) * 1e6

    # -------------------------------------------------------------------------
    # Top-level prediction
    # -------------------------------------------------------------------------

    def predict(self, cfg: FA4WorkloadDesc) -> Dict[str, Any]:
        """Return predicted runtime and per-component bound breakdown."""
        workload = self.workload_quantities(cfg)

        compute_issue_us = self.compute_issue_bound_us(cfg, workload)
        tc_throughput_us = self.tensor_core_throughput_bound_us(cfg, workload)
        mufu_us = self.mufu_throughput_bound_us(cfg, workload)
        pipeline_us = self.execution_pipeline_bound_us(cfg, workload)
        memory_us = self.memory_pipeline_bound_us(cfg, workload)
        interconnect_us = self.interconnect_bound_us(cfg, workload)

        # The effective compute and memory bounds are the maxima of their
        # constituent components; overall runtime is the max of compute and
        # memory plus the crossbar/interconnect latency tax.
        compute_bound_us = max(compute_issue_us, tc_throughput_us, mufu_us, pipeline_us)
        memory_bound_us = max(memory_us, interconnect_us)

        base_us = max(compute_bound_us, memory_bound_us)
        runtime_ms = (base_us + self.spec.launch_overhead_us) / 1000.0

        components = {
            "compute_issue_us": compute_issue_us,
            "tensor_core_throughput_us": tc_throughput_us,
            "mufu_throughput_us": mufu_us,
            "execution_pipeline_us": pipeline_us,
            "memory_pipeline_us": memory_us,
            "interconnect_us": interconnect_us,
        }
        dominant = max(components, key=components.get)  # type: ignore[arg-type]
        dominant_bottleneck = dominant.replace("_us", "").replace("_", " ")

        return {
            "predicted_runtime_ms": runtime_ms,
            "predicted_runtime_us": base_us + self.spec.launch_overhead_us,
            "dominant_bottleneck": dominant_bottleneck,
            "compute_bound_us": compute_bound_us,
            "memory_bound_us": memory_bound_us,
            **components,
            "occupancy_fraction": self.occupancy_fraction(cfg, workload),
            "active_warps": self.active_warps(cfg, workload),
            "hbm_effective_bw_gbps": self.hbm_effective_bw_bytes_per_s(cfg, workload)
            / 1e9,
            "l1_miss_bytes": self.l1_cache_traffic(cfg, workload),
            "l2_miss_bytes": self.l2_cache_traffic(cfg, workload),
            "interconnect_contention_factor": self.interconnect_contention_factor(
                cfg, workload
            ),
            "workload": workload,
        }


# -----------------------------------------------------------------------------
# Convenience defaults
# -----------------------------------------------------------------------------


def default_b200_inner_gpu_model() -> B200InnerGPUModel:
    """Return a ``B200InnerGPUModel`` with B200-calibrated defaults."""
    return B200InnerGPUModel()


def predict_runtime(
    batch: int,
    heads: int,
    seqlen: int,
    head_dim: int,
    causal: bool,
    precision: str,
    spec: Optional[B200InnerGPUModelSpec] = None,
) -> Dict[str, Any]:
    """One-shot convenience wrapper around ``B200InnerGPUModel.predict``."""
    cfg = FA4WorkloadDesc(
        batch=batch,
        heads=heads,
        seqlen=seqlen,
        head_dim=head_dim,
        causal=causal,
        precision=precision,
    )
    return B200InnerGPUModel(spec=spec).predict(cfg)


if __name__ == "__main__":
    # Smoke test: does not require CUDA/GPU.
    demo = FA4WorkloadDesc(
        batch=2, heads=16, seqlen=2048, head_dim=128, causal=True, precision="fp16"
    )
    result = default_b200_inner_gpu_model().predict(demo)
    print(f"demo predicted_runtime_ms = {result['predicted_runtime_ms']:.3f}")
    print(f"demo dominant_bottleneck  = {result['dominant_bottleneck']}")
