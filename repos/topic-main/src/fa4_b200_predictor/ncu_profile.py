"""NCU hardware-counter profiling helper for a subset of FA4 configs.

Collects the SpeedOfLight section so we can label each profiled config as
compute-bound or memory-bound using real hardware counters, independent of the
white-box model's own bottleneck diagnosis.
"""

from __future__ import annotations

import csv
import io
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fa4_b200_predictor.config_matrix import config_to_dict
from fa4_b200_predictor.predictor import FA4Config


NCU_METRIC_COMPUTE = "Compute (SM) Throughput"
NCU_METRIC_MEMORY = "Memory Throughput"
NCU_METRIC_DURATION = "Duration"


def _python_path() -> str:
    """Return the topic Pixi Python interpreter path.

    The caller may override by ensuring the active ``python`` is the topic env.
    """
    import sys

    return sys.executable


def _parse_number(raw: str) -> Optional[float]:
    """Parse an ncu CSV numeric value, handling 'n/a' and thousands separators."""
    if raw is None:
        return None
    text = raw.strip().replace('"', "").replace(",", "")
    if text.lower() in ("n/a", "", "--"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _write_invocation_script(cfg: FA4Config, device: str, path: Path) -> None:
    """Write a standalone Python script that launches one FA4 kernel."""
    dtype_map = {
        "bf16": "torch.bfloat16",
        "fp16": "torch.float16",
        "fp8": "torch.float8_e4m3fn",
    }
    dtype_expr = dtype_map[cfg.normalized_precision]
    shape = (cfg.batch, cfg.seqlen, cfg.heads, cfg.head_dim)

    if cfg.normalized_precision == "fp8":
        tensor_lines = (
            "q = torch.randn(shape, dtype=torch.bfloat16, device=device).to(dtype)\n"
            "k = torch.randn(shape, dtype=torch.bfloat16, device=device).to(dtype)\n"
            "v = torch.randn(shape, dtype=torch.bfloat16, device=device).to(dtype)\n"
        )
    else:
        tensor_lines = (
            f"q = torch.randn(shape, dtype={dtype_expr}, device=device)\n"
            f"k = torch.randn(shape, dtype={dtype_expr}, device=device)\n"
            f"v = torch.randn(shape, dtype={dtype_expr}, device=device)\n"
        )

    script = (
        "import torch\n"
        "from flash_attn.cute import flash_attn_func\n"
        f"device = torch.device('{device}')\n"
        f"torch.cuda.set_device(device)\n"
        f"shape = {shape}\n"
        f"dtype = {dtype_expr}\n"
        f"{tensor_lines}"
        "torch.cuda.synchronize(device)\n"
        "_ = flash_attn_func(q, k, v, causal={causal})\n"
        "torch.cuda.synchronize(device)\n"
    ).format(causal=cfg.causal)

    path.write_text(script, encoding="utf-8")


def profile_config(
    cfg: FA4Config,
    device: str = "cuda:0",
    timeout: int = 120,
) -> Dict[str, Any]:
    """Profile a single config with NCU and return counter-derived labels."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "invocation.py"
        _write_invocation_script(cfg, device, script_path)

        cmd = [
            "ncu",
            "--target-processes",
            "all",
            "--kernel-name-base",
            "function",
            "--kernel-name",
            "regex:flash_attn",
            "--section",
            "SpeedOfLight",
            "--csv",
            _python_path(),
            str(script_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        profile = _parse_ncu_csv(result.stdout)
        profile["config"] = config_to_dict(cfg)
        profile["ncu_command"] = " ".join(cmd)
        profile["ncu_returncode"] = result.returncode
        if result.returncode != 0 and not profile.get("duration_ns"):
            profile["error"] = result.stderr.strip().splitlines()[-1] if result.stderr else "ncu failed"
        return profile


def _parse_ncu_csv(stdout: str) -> Dict[str, Any]:
    """Extract the first flash_attn kernel's SpeedOfLight metrics from NCU CSV."""
    compute_pct: Optional[float] = None
    memory_pct: Optional[float] = None
    duration_ns: Optional[float] = None

    lines = stdout.splitlines()
    # Find the CSV header; earlier lines are PROF/ERROR diagnostics.
    start = next((i for i, line in enumerate(lines) if line.startswith('"ID"')), None)
    if start is None:
        return {
            "compute_pct": compute_pct,
            "memory_pct": memory_pct,
            "duration_ns": duration_ns,
            "bottleneck": "unknown",
        }

    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    for row in reader:
        name = row.get("Metric Name", "").strip()
        value = row.get("Metric Value", "").strip()
        if name == NCU_METRIC_COMPUTE:
            compute_pct = _parse_number(value)
        elif name == NCU_METRIC_MEMORY:
            memory_pct = _parse_number(value)
        elif name == NCU_METRIC_DURATION:
            duration_ns = _parse_number(value)

    if compute_pct is not None and memory_pct is not None:
        bottleneck = "compute" if compute_pct >= memory_pct else "memory"
    else:
        bottleneck = "unknown"

    return {
        "compute_pct": compute_pct,
        "memory_pct": memory_pct,
        "duration_ns": duration_ns,
        "bottleneck": bottleneck,
    }


def profile_configs(
    configs: List[FA4Config],
    device: str = "cuda:0",
    progress_every: int = 5,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Profile a list of configs and return records plus status counts."""
    records: List[Dict[str, Any]] = []
    counts = {"ok": 0, "error": 0}
    for i, cfg in enumerate(configs):
        rec = profile_config(cfg, device=device)
        records.append(rec)
        if rec.get("bottleneck") == "unknown" or rec.get("error"):
            counts["error"] += 1
        else:
            counts["ok"] += 1
        if (i + 1) % progress_every == 0 or i == len(configs) - 1:
            print(
                f"NCU profiled {i + 1}/{len(configs)} configs "
                f"(ok={counts['ok']}, error={counts['error']})"
            )
    return records, counts


def attach_ncu_labels(
    measurements: List[Dict[str, Any]],
    ncu_records: List[Dict[str, Any]],
) -> None:
    """Attach ncu bottleneck/duration fields to the matching measurement rows."""
    key = lambda d: (  # noqa: E731
        d.get("batch"),
        d.get("heads"),
        d.get("seqlen"),
        d.get("head_dim"),
        d.get("causal"),
        d.get("precision"),
    )
    ncu_by_key: Dict[Any, Dict[str, Any]] = {}
    for rec in ncu_records:
        cfg = rec.get("config")
        if cfg is None:
            continue
        ncu_by_key[key(cfg)] = rec

    for row in measurements:
        rec = ncu_by_key.get(key(row))
        if rec is not None:
            row["ncu_bottleneck"] = rec.get("bottleneck", "unknown")
            row["ncu_compute_pct"] = rec.get("compute_pct")
            row["ncu_memory_pct"] = rec.get("memory_pct")
            row["ncu_duration_ns"] = rec.get("duration_ns")
        else:
            row["ncu_bottleneck"] = "unprofiled"
            row["ncu_compute_pct"] = None
            row["ncu_memory_pct"] = None
            row["ncu_duration_ns"] = None


def coarse_bottleneck(label: str) -> str:
    """Map fine-grained white-box labels to the coarse NCU compute/memory labels."""
    if label in ("mma", "mufu"):
        return "compute"
    return "memory"
