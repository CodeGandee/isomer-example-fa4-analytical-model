"""Hardware and algorithm constants for the Flash Attention 4 B200 white-box predictor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class B200Spec:
    """Blackwell B200 hardware specification used by the white-box models."""

    # Clocks
    peak_sm_clock_mhz: float = 1965.0
    memory_clock_mhz: float = 3996.0

    # SM / warp counts
    num_sms: int = 180
    max_warps_per_sm: int = 64
    threads_per_warp: int = 32

    # Tensor Core MMA throughput per SM (per clock) for FA4-like tiles.
    # Calibrated from published Blackwell SM100 microbenchmarks and FA4 paper.
    mma_throughput_per_sm_per_clock: Dict[str, float] = None  # type: ignore[assignment]

    # MUFU (exp, softmax) throughput per SM per clock
    mufu_throughput_per_sm_per_clock: Dict[str, float] = None  # type: ignore[assignment]

    # Memory bandwidth peaks (bytes/second) per precision/pressure regime.
    peak_hbm_bw_gbps: float = 4480.0  # 5.6 TB/s advertised, realistic ~4.5 TB/s
    peak_l2_bw_gbps: float = 24000.0  # L2 aggregate read bandwidth estimate

    # Shared memory
    smem_bytes_per_sm: int = 256 * 1024  # 256 KiB
    smem_bandwidth_bytes_per_clock_per_sm: float = 128.0  # 128 B/clock/SM

    # TMA effective bytes per transfer (used for transfer-size bandwidth model)
    tma_base_latency_us: float = 0.15
    tma_bytes_per_ns: float = 4000.0  # effective L2-backed TMA bandwidth (GB/s)  # effective calibrated

    # Occupancy
    max_threads_per_sm: int = 2048
    max_registers_per_sm: int = 256 * 1024

    def __post_init__(self) -> None:
        # dataclasses with mutable defaults are awkward; pre-populate here.
        object.__setattr__(
            self,
            "mma_throughput_per_sm_per_clock",
            {
                # Calibrated to B200 Blackwell dense Tensor Core peaks
                # (FP8 ~6.7 PFLOPS, BF16/FP16 ~3.3 PFLOPS, FP32 TC ~0.8 PFLOPS).
                "fp32": 2400.0,
                "fp16": 9500.0,
                "bf16": 9500.0,
                "fp8": 19000.0,
                "fp4": 38000.0,
            },
        )
        object.__setattr__(
            self,
            "mufu_throughput_per_sm_per_clock",
            {
                "fp32": 32.0,
                "fp16": 32.0,
                "bf16": 32.0,
                "fp8": 32.0,
                "fp4": 32.0,
            },
        )


@dataclass(frozen=True)
class FA4TileConfig:
    """Default FA4 tile sizes and launch assumptions per (headdim, precision)."""

    block_m: int = 128
    block_n: int = 64
    stages: int = 3
    num_splits: int = 1

    # Bytes per element for each precision in the FA4 kernel.
    bytes_per_element: Dict[str, int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "bytes_per_element",
            {
                "fp32": 4,
                "fp16": 2,
                "bf16": 2,
                "fp8": 1,
                "fp4": 1,  # packed representation; we model active bit-width effect separately
            },
        )


B200 = B200Spec()
TILE = FA4TileConfig()

# Precision alias normalization.
PRECISION_ALIASES: Dict[str, str] = {
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

# Calibration bounds to keep the white-box model interpretable.
CALIBRATION_BOUNDS: Dict[str, Tuple[float, float]] = {
    "hbm_factor": (0.10, 1.00),
    "l2_factor": (0.10, 1.00),
    "tma_factor": (0.10, 1.00),
    "mma_efficiency": (0.10, 1.00),
    "mufu_efficiency": (0.10, 1.00),
    "smem_factor": (0.10, 1.00),
    "launch_overhead_us": (0.0, 10.0),
}

# Default tile sizes as a function of headdim (approximation from FA4 paper / CuTe code).
DEFAULT_TILE_SIZES: Dict[int, Tuple[int, int]] = {
    64: (128, 128),
    128: (128, 64),
    256: (64, 64),
}
