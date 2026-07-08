"""Configuration matrix generation and dataset splitting."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from fa4_b200_predictor.predictor import FA4Config


DEFAULT_BATCHES = [1, 2, 4, 8, 16]
DEFAULT_HEADS = [8, 16]
DEFAULT_SEQLENS = [512, 1024, 2048, 4096, 8192]
DEFAULT_HEAD_DIMS = [64, 128]
DEFAULT_CAUSAL = [False, True]
DEFAULT_PRECISIONS = ["fp16", "bf16", "fp8", "fp4"]


def build_config_matrix(
    batches: Iterable[int] = DEFAULT_BATCHES,
    heads: Iterable[int] = DEFAULT_HEADS,
    seqlens: Iterable[int] = DEFAULT_SEQLENS,
    head_dims: Iterable[int] = DEFAULT_HEAD_DIMS,
    causal_vals: Iterable[bool] = DEFAULT_CAUSAL,
    precisions: Iterable[str] = DEFAULT_PRECISIONS,
) -> List[FA4Config]:
    """Generate a synthetic but realistic FA4 configuration matrix."""
    configs: List[FA4Config] = []
    for b in batches:
        for h in heads:
            for s in seqlens:
                for d in head_dims:
                    for causal in causal_vals:
                        for p in precisions:
                            # Skip configurations likely to exceed B200 HBM for the emulator.
                            total_qkv_gb = (
                                3 * b * h * s * d * 2 / 1e9
                            )  # bf16 bytes, upper bound
                            if total_qkv_gb > 160:
                                continue
                            configs.append(
                                FA4Config(
                                    batch=b,
                                    heads=h,
                                    seqlen=s,
                                    head_dim=d,
                                    causal=causal,
                                    precision=p,
                                )
                            )
    return configs


def split_configs(
    configs: List[FA4Config],
    calibration_frac: float = 0.20,
    validation_frac: float = 0.20,
    seed: int = 20260704,
) -> Tuple[List[FA4Config], List[FA4Config], List[FA4Config]]:
    """Split configs into calibration, validation, and query sets deterministically."""
    import random

    rng = random.Random(seed)
    shuffled = configs[:]
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_cal = int(round(n * calibration_frac))
    n_val = int(round(n * validation_frac))

    cal = shuffled[:n_cal]
    val = shuffled[n_cal : n_cal + n_val]
    query = shuffled[n_cal + n_val :]
    return cal, val, query


def config_to_dict(cfg: FA4Config) -> Dict[str, Any]:
    return {
        "batch": cfg.batch,
        "heads": cfg.heads,
        "seqlen": cfg.seqlen,
        "head_dim": cfg.head_dim,
        "causal": cfg.causal,
        "precision": cfg.normalized_precision,
    }


def dict_to_config(d: Dict[str, Any]) -> FA4Config:
    return FA4Config(
        batch=int(d["batch"]),
        heads=int(d["heads"]),
        seqlen=int(d["seqlen"]),
        head_dim=int(d["head_dim"]),
        causal=bool(d["causal"]),
        precision=str(d["precision"]),
    )


def save_split(
    cal: List[FA4Config],
    val: List[FA4Config],
    query: List[FA4Config],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, split in [("calibration", cal), ("validation", val), ("query", query)]:
        path = out_dir / f"{name}_configs.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump([config_to_dict(c) for c in split], f, indent=2)
        csv_path = out_dir / f"{name}_configs.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["batch", "heads", "seqlen", "head_dim", "causal", "precision"],
            )
            writer.writeheader()
            for c in split:
                writer.writerow(config_to_dict(c))
