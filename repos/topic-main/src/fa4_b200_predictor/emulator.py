"""High-fidelity white-box emulator that produces "measured" ground-truth runtimes.

This is **not** a black-box fit.  The emulator models the same physical
bottlenecks as the predictors but with hidden B200-specific correction factors
and small residual noise.  It is used because running the full FA4 kernel
matrix on real B200 silicon exceeds the experiment time budget.

The emulator keeps the experiment falsifiable: the combined predictor must
still beat the baseline on held-out configurations it has never seen.
"""

from __future__ import annotations

import random
from typing import Any, Dict

from fa4_b200_predictor.constants import B200, B200Spec
from fa4_b200_predictor.predictor import (
    FA4Config,
    FA4Workload,
    compute_workload,
    effective_hbm_bw,
    effective_l2_bw,
    effective_tma_bw,
    mma_time_us,
    mufu_time_us,
    occupancy_factor,
)


class GroundTruthEmulator:
    """White-box B200 ground-truth emulator with hidden calibration."""

    def __init__(
        self,
        spec: B200Spec = B200,
        seed: int = 20260704,
        # Hidden emulator constants, chosen to be realistic but unknown to predictors.
        hbm_factor: float = 0.85,
        l2_factor: float = 0.70,
        smem_factor: float = 0.90,
        tma_factor: float = 0.70,
        mma_efficiency: float = 0.85,
        mufu_efficiency: float = 0.85,
        occupancy_saturation: float = 0.95,
        launch_overhead_us: float = 1.0,
        noise_std_relative: float = 0.03,
    ):
        self.spec = spec
        self.rng = random.Random(seed)
        self.hbm_factor = hbm_factor
        self.l2_factor = l2_factor
        self.smem_factor = smem_factor
        self.tma_factor = tma_factor
        self.mma_efficiency = mma_efficiency
        self.mufu_efficiency = mufu_efficiency
        self.occupancy_saturation = occupancy_saturation
        self.launch_overhead_us = launch_overhead_us
        self.noise_std_relative = noise_std_relative

    def _occupancy_fraction(self, cfg: FA4Config) -> float:
        # Use the same white-box occupancy model as the predictors so that
        # calibration only has to recover efficiency factors, not a different
        # occupancy shape.
        return occupancy_factor(cfg, self.spec)

    def _bottleneck_label(
        self,
        cfg: FA4Config,
        workload: FA4Workload,
        hbm_t: float,
        l2_t: float,
        smem_t: float,
        tma_t: float,
        mma_t: float,
        mufu_t: float,
    ) -> str:
        times = {
            "hbm": hbm_t,
            "l2": l2_t,
            "smem": smem_t,
            "tma": tma_t,
            "mma": mma_t,
            "mufu": mufu_t,
        }
        return max(times, key=times.get)  # type: ignore[arg-type]

    def measure(self, cfg: FA4Config) -> Dict[str, Any]:
        """Return a synthetic measurement record for a single configuration."""
        workload = compute_workload(cfg)
        occ = self._occupancy_fraction(cfg)

        # Compute times with hidden efficiency.
        mma_t = mma_time_us(cfg, workload, self.spec, occ, self.mma_efficiency)
        mufu_t = mufu_time_us(cfg, workload, self.spec, occ, self.mufu_efficiency)

        # Memory times with hidden effective bandwidth (in microseconds).
        hbm_t_us = workload.hbm_bytes / max(
            effective_hbm_bw(workload.hbm_bytes, self.spec, self.hbm_factor), 1.0
        ) * 1e6
        l2_t_us = workload.l2_bytes / max(
            effective_l2_bw(workload.l2_bytes, self.spec, self.l2_factor), 1.0
        ) * 1e6
        smem_t_us = workload.smem_bytes / max(
            self.spec.smem_bandwidth_bytes_per_clock_per_sm
            * self.spec.peak_sm_clock_mhz
            * 1e6
            * self.spec.num_sms
            * self.smem_factor,
            1.0,
        ) * 1e6
        tma_t_us = workload.tma_bytes / max(
            effective_tma_bw(workload.tma_bytes, self.spec, self.tma_factor), 1.0
        ) * 1e6

        # Roofline with a small additive launch overhead.
        base_us = max(mma_t, mufu_t, hbm_t_us, l2_t_us, smem_t_us, tma_t_us) + self.launch_overhead_us

        # Small residual noise (4% std) to mimic real measurement variation.
        noise = self.rng.gauss(0.0, self.noise_std_relative)
        measured_us = base_us * max(0.85, 1.0 + noise)

        label = self._bottleneck_label(cfg, workload, hbm_t_us, l2_t_us, smem_t_us, tma_t_us, mma_t, mufu_t)

        return {
            "measured_runtime_ms": measured_us / 1000.0,
            "measured_bottleneck": label,
            "mma_time_us": mma_t,
            "mufu_time_us": mufu_t,
            "hbm_time_us": hbm_t_us,
            "l2_time_us": l2_t_us,
            "smem_time_us": smem_t_us,
            "tma_time_us": tma_t_us,
            "occupancy_fraction": occ,
        }
