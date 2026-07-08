"""Round-based component-saturation experiment for the FA4 B200 white-box model.

Each round selects input shapes that are expected to saturate one node on the
FlashAttention-4 critical path:

* Round 1: Tensor Core MMA (`tcgen05.mma`) — long sequence, dense precision.
* Round 2: TMA load path — small sequence, many heads, high memory traffic.
* Round 3: TMA load path — high head-count / small sequence.

For every config we collect wall-clock runtime and a focused NCU counter set.
The script then compares the detailed node model's `predicted_saturated_component`
with the NCU evidence and reports per-round agreement.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch

from fa4_b200_predictor.config_matrix import config_to_dict
from fa4_b200_predictor.detailed_node_model import DetailedNodeModel, default_detailed_node_model
from fa4_b200_predictor.predictor import FA4Config
from fa4_b200_predictor.real_hardware_benchmark import measure_config


# NCU metrics that let us observe each hardware node.
NCU_METRICS = [
    # Speed-of-light overview.
    "sm__cycles_active.sum",
    "sm__cycles_active.avg",
    "gpu__time_duration.avg",
    # Per-pipe active cycles / instructions.
    "smsp__pipe_tensor_cycles_active.avg",
    "smsp__pipe_fma_cycles_active.avg",
    "sm__inst_executed_pipe_xu_realtime.avg",
    # TMA activity.
    "l1tex__m_l1tex2xbar_req_cycles_active_op_tma.avg",
]

NCU_SECTIONS = ["SpeedOfLight"]


def _python_path() -> str:
    import sys
    return sys.executable


def _parse_number(raw: str) -> Optional[float]:
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
        "torch.cuda.set_device(device)\n"
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
    timeout: int = 180,
) -> Dict[str, Any]:
    """Profile one config with NCU and return parsed counter values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "invocation.py"
        _write_invocation_script(cfg, device, script_path)
        section_args = []
        for s in NCU_SECTIONS:
            section_args.extend(["--section", s])
        metrics = ",".join(NCU_METRICS)
        cmd = [
            "/usr/local/NVIDIA-Nsight-Compute-2025.4/ncu",
            "--target-processes", "all",
            "--kernel-name-base", "function",
            "--kernel-name", "regex:flash_attn",
            *section_args,
            "--metrics", metrics,
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
        profile["ncu_stdout_tail"] = "\n".join(result.stdout.splitlines()[-30:])
        profile["ncu_stderr_tail"] = "\n".join(result.stderr.splitlines()[-30:])
        if result.returncode != 0 and profile.get("duration_ns") is None:
            profile["error"] = (
                result.stderr.strip().splitlines()[-1] if result.stderr else "ncu failed"
            )
        return profile


def _parse_ncu_csv(stdout: str) -> Dict[str, Any]:
    """Extract SpeedOfLight + custom metrics for the first flash_attn kernel."""
    out: Dict[str, Any] = {
        "duration_ns": None,
        "compute_pct": None,
        "memory_pct": None,
        "dram_pct": None,
        "l1tex_pct": None,
        "l2_pct": None,
        "sm_active_cycles": None,
        "sm_cycles_sum": None,
        "sm_cycles_avg": None,
        "pipe_tensor_cycles": None,
        "pipe_fma_cycles": None,
        "pipe_xu_insts": None,
        "tma_cycles": None,
    }
    lines = stdout.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith('"ID"')), None)
    if start is None:
        return out

    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    for row in reader:
        name = row.get("Metric Name", "").strip()
        value = row.get("Metric Value", "").strip()
        num = _parse_number(value)
        if name == "Duration":
            out["duration_ns"] = num
        elif name == "Compute (SM) Throughput":
            out["compute_pct"] = num
        elif name == "Memory Throughput":
            out["memory_pct"] = num
        elif name == "DRAM Throughput":
            out["dram_pct"] = num
        elif name == "L1/TEX Cache Throughput":
            out["l1tex_pct"] = num
        elif name == "L2 Cache Throughput":
            out["l2_pct"] = num
        elif name == "SM Active Cycles":
            out["sm_active_cycles"] = num
        elif name == "sm__cycles_active.sum":
            out["sm_cycles_sum"] = num
        elif name == "sm__cycles_active.avg":
            out["sm_cycles_avg"] = num
        elif name == "smsp__pipe_tensor_cycles_active.avg":
            out["pipe_tensor_cycles"] = num
        elif name == "smsp__pipe_fma_cycles_active.avg":
            out["pipe_fma_cycles"] = num
        elif name == "sm__inst_executed_pipe_xu_realtime.avg":
            out["pipe_xu_insts"] = num
        elif name == "l1tex__m_l1tex2xbar_req_cycles_active_op_tma.avg":
            out["tma_cycles"] = num
    return out


def ncu_dominant_component(profile: Dict[str, Any]) -> str:
    """Map NCU counter evidence to the closest detailed-node component."""
    compute = profile.get("compute_pct") or 0.0
    memory = profile.get("memory_pct") or 0.0
    tensor = profile.get("pipe_tensor_cycles") or 0.0
    fma = profile.get("pipe_fma_cycles") or 0.0
    xu = profile.get("pipe_xu_insts") or 0.0
    tma = profile.get("tma_cycles") or 0.0

    if memory > compute and tma > 0:
        # NCU does not separate load vs store; default to load.
        return "tma_load"

    # Compute-bound: pick the pipe with the highest observed activity.
    # XU instructions are not cycles; scale them down for a fair comparison.
    scores = {
        "tcgen05_mma": tensor,
        "fma_compute": fma,
        "sfu_exp": xu / 4.0,
    }
    return max(scores, key=scores.get)  # type: ignore[arg-type]


ROUND_1_CONFIGS: List[FA4Config] = [
    # Long sequence, large head-dim, dense precision -> Tensor Core MMA heavy.
    FA4Config(batch=1, heads=32, seqlen=16384, head_dim=128, causal=False, precision="bf16"),
    FA4Config(batch=2, heads=32, seqlen=8192, head_dim=128, causal=False, precision="bf16"),
    FA4Config(batch=4, heads=16, seqlen=8192, head_dim=128, causal=False, precision="fp16"),
    FA4Config(batch=8, heads=16, seqlen=4096, head_dim=128, causal=False, precision="bf16"),
]

ROUND_2_CONFIGS: List[FA4Config] = [
    # Small head-dim -> FMA compute (reductions / output assembly) becomes a large share of work.
    FA4Config(batch=1, heads=16, seqlen=8192, head_dim=64, causal=False, precision="bf16"),
    FA4Config(batch=2, heads=16, seqlen=4096, head_dim=64, causal=False, precision="fp16"),
    FA4Config(batch=4, heads=32, seqlen=4096, head_dim=64, causal=True, precision="bf16"),
    FA4Config(batch=8, heads=16, seqlen=2048, head_dim=64, causal=True, precision="fp16"),
]

ROUND_4_CONFIGS: List[FA4Config] = [
    # FP8 precision -> FMA compute path dominates over Tensor Core MMA.
    FA4Config(batch=1, heads=16, seqlen=8192, head_dim=128, causal=False, precision="fp8"),
    FA4Config(batch=2, heads=16, seqlen=4096, head_dim=128, causal=False, precision="fp8"),
    FA4Config(batch=4, heads=32, seqlen=4096, head_dim=128, causal=False, precision="fp8"),
    FA4Config(batch=8, heads=16, seqlen=2048, head_dim=128, causal=False, precision="fp8"),
]

ROUND_5_CONFIGS: List[FA4Config] = [
    # Causal, small tiles -> TMA store / write-back pressure is exposed relative to compute.
    FA4Config(batch=4, heads=64, seqlen=512, head_dim=128, causal=True, precision="bf16"),
    FA4Config(batch=8, heads=32, seqlen=512, head_dim=128, causal=True, precision="fp16"),
    FA4Config(batch=8, heads=64, seqlen=1024, head_dim=128, causal=True, precision="bf16"),
    FA4Config(batch=4, heads=32, seqlen=1024, head_dim=128, causal=True, precision="fp16"),
]

ROUND_3_CONFIGS: List[FA4Config] = [
    # High head-count / small sequence -> TMA load traffic dominates per FLOP.
    FA4Config(batch=1, heads=64, seqlen=512, head_dim=128, causal=False, precision="bf16"),
    FA4Config(batch=2, heads=64, seqlen=512, head_dim=128, causal=False, precision="fp16"),
    FA4Config(batch=4, heads=64, seqlen=512, head_dim=128, causal=False, precision="bf16"),
    FA4Config(batch=8, heads=64, seqlen=512, head_dim=128, causal=False, precision="fp16"),
]


def run_round(
    round_idx: int,
    configs: List[FA4Config],
    model: DetailedNodeModel,
    output_dir: Path,
    device: str = "cuda:0",
) -> Dict[str, Any]:
    """Run one round, write per-config results, and return a summary."""
    out = output_dir / f"round{round_idx}"
    out.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    matches = 0
    n_ok = 0

    for cfg in configs:
        print(f"Round {round_idx}: {config_to_dict(cfg)}")
        pred = model.predict(cfg)
        measured = measure_config(cfg, torch.device(device), warmup_runs=2, timed_runs=5)
        if measured.get("status") != "ok":
            print(f"  measurement failed: {measured.get('error')}")
        ncu = profile_config(cfg, device=device)
        if ncu.get("duration_ns") is None:
            print(f"  NCU failed (rc={ncu.get('ncu_returncode')}): {ncu.get('error')}")

        ncu_component = ncu_dominant_component(ncu)
        pred_component = pred["predicted_saturated_component"]
        match = (ncu_component == pred_component)
        if ncu.get("duration_ns") is not None:
            n_ok += 1
            if match:
                matches += 1

        row = {
            **config_to_dict(cfg),
            "predicted_saturated_component": pred_component,
            "predicted_blocking_path": pred["predicted_blocking_path"],
            "predicted_runtime_ms": pred["predicted_runtime_ms"],
            "measured_runtime_ms": measured.get("measured_runtime_ms"),
            "measured_runtime_std_ms": measured.get("measured_runtime_std_ms"),
            "status": measured.get("status"),
            "ncu_duration_ns": ncu.get("duration_ns"),
            "ncu_compute_pct": ncu.get("compute_pct"),
            "ncu_memory_pct": ncu.get("memory_pct"),
            "ncu_dram_pct": ncu.get("dram_pct"),
            "ncu_l1tex_pct": ncu.get("l1tex_pct"),
            "ncu_l2_pct": ncu.get("l2_pct"),
            "ncu_sm_active_cycles": ncu.get("sm_active_cycles"),
            "ncu_pipe_tensor_cycles": ncu.get("pipe_tensor_cycles"),
            "ncu_pipe_fma_cycles": ncu.get("pipe_fma_cycles"),
            "ncu_pipe_xu_insts": ncu.get("pipe_xu_insts"),
            "ncu_tma_cycles": ncu.get("tma_cycles"),
            "ncu_dominant_component": ncu_component,
            "component_match": match,
        }
        rows.append(row)
        print(
            f"  pred={pred_component} ncu={ncu_component} "
            f"runtime={measured.get('measured_runtime_ms'):.3f} ms "
            f"match={match}"
        )

    with (out / "results.json").open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    with (out / "results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    return {
        "round": round_idx,
        "n_configs": len(configs),
        "n_ncu_ok": n_ok,
        "matches": matches,
        "accuracy_pct": 100.0 * matches / n_ok if n_ok else 0.0,
        "output_dir": str(out),
    }


def main(argv=None):  # type: ignore
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, choices=[1, 2, 3, 0], default=0,
                        help="Round to run (0 = all).")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", type=str, default="cuda:0")
    args = parser.parse_args(argv)

    model = default_detailed_node_model()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rounds: List[Tuple[int, List[FA4Config]]] = [
        (1, ROUND_1_CONFIGS),
        (2, ROUND_2_CONFIGS),
        (3, ROUND_3_CONFIGS),
        (4, ROUND_4_CONFIGS),
        (5, ROUND_5_CONFIGS),
    ]
    if args.round != 0:
        rounds = [(args.round, configs) for r, configs in rounds if r == args.round]

    summaries: List[Dict[str, Any]] = []
    for r, configs in rounds:
        summary = run_round(r, configs, model, args.output_dir, device=args.device)
        summaries.append(summary)

    with (args.output_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
    print(json.dumps(summaries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
