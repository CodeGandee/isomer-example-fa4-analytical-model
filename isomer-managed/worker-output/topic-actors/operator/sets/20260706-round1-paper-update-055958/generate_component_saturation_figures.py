#!/usr/bin/env python3
"""Generate component-saturation figures from v3 NCU evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


ROUND_LABELS = {
    1: "R1: Tensor Core MMA",
    2: "R2: FMA compute",
    3: "R3: TMA load",
    4: "R4: FP32 update",
    5: "R5: TMA store",
}

COMPONENT_LABELS = {
    "tcgen05_mma": "Tensor Core",
    "fma_compute": "FMA compute",
    "sfu_exp": "SFU/XU",
    "tma_load": "TMA load",
    "tma_store": "TMA store",
}

COLORS = {
    "tcgen05_mma": "#1f77b4",
    "fma_compute": "#ff7f0e",
    "sfu_exp": "#2ca02c",
    "tma_load": "#d62728",
    "tma_store": "#9467bd",
}


def load_rounds(data_dir: Path) -> List[Tuple[int, List[Dict[str, Any]]]]:
    rounds: List[Tuple[int, List[Dict[str, Any]]]] = []
    for round_dir in sorted(data_dir.glob("round*")):
        round_idx = int(round_dir.name.replace("round", ""))
        results_path = round_dir / "results.json"
        if results_path.exists():
            with results_path.open() as f:
                rounds.append((round_idx, json.load(f)))
    return rounds


def svg_start(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="sans-serif" font-size="12">\n'
    )


def svg_end() -> str:
    return "</svg>\n"


def generate_figure6(rounds: List[Tuple[int, List[Dict[str, Any]]]], out_path: Path) -> None:
    """Stacked bar chart of mean NCU pipe-activity fractions per round."""
    W, H = 1000, 520
    margin = dict(top=90, right=180, bottom=140, left=90)
    plot_w = W - margin["left"] - margin["right"]
    plot_h = H - margin["top"] - margin["bottom"]

    # Aggregate mean fractions per round.
    components = ["tcgen05_mma", "fma_compute", "sfu_exp", "tma_load"]
    round_names: List[str] = []
    fractions: Dict[str, List[float]] = {c: [] for c in components}
    for round_idx, rows in sorted(rounds):
        round_names.append(ROUND_LABELS.get(round_idx, f"R{round_idx}"))
        total_cycles = 0.0
        sums = {c: 0.0 for c in components}
        for r in rows:
            sm_active = r.get("ncu_sm_active_cycles") or 1.0
            tensor = r.get("ncu_pipe_tensor_cycles") or 0.0
            fma = r.get("ncu_pipe_fma_cycles") or 0.0
            xu = r.get("ncu_pipe_xu_insts") or 0.0
            tma = r.get("ncu_tma_cycles") or 0.0
            sums["tcgen05_mma"] += tensor / sm_active
            sums["fma_compute"] += fma / sm_active
            sums["sfu_exp"] += (xu / 4.0) / sm_active
            sums["tma_load"] += tma / sm_active
        n = len(rows)
        for c in components:
            fractions[c].append(sums[c] / n if n else 0.0)

    n_rounds = len(round_names)
    bar_w = plot_w / (n_rounds + 1) * 0.85
    group_w = plot_w / (n_rounds + 1)

    lines: List[str] = []
    lines.append(svg_start(W, H))
    lines.append(f'<rect width="{W}" height="{H}" fill="white"/>')

    # y grid and ticks
    for v in np.linspace(0, 1, 6):
        y = margin["top"] + plot_h * (1 - v)
        lines.append(
            f'<line x1="{margin["left"]}" y1="{y}" x2="{W - margin["right"]}" y2="{y}" stroke="#e0e0e0" stroke-width="1"/>'
        )
        lines.append(f'<text x="{margin["left"] - 12}" y="{y + 4}" text-anchor="end" font-size="12" fill="#333">{int(v * 100)}%</text>')

    # bars
    for i, name in enumerate(round_names):
        x = margin["left"] + (i + 0.5) * group_w - bar_w / 2
        y0 = margin["top"] + plot_h
        for c in components:
            frac = fractions[c][i]
            h = frac * plot_h
            y1 = y0 - h
            lines.append(
                f'<rect x="{x}" y="{y1}" width="{bar_w}" height="{h}" fill="{COLORS[c]}" stroke="white" stroke-width="1"/>'
            )
            # segment percentage label (only if large enough)
            if h > 22:
                lines.append(
                    f'<text x="{x + bar_w / 2}" y="{y1 + h / 2 + 4}" text-anchor="middle" font-size="11" fill="white" font-weight="bold">{int(round(frac * 100))}%</text>'
                )
            y0 = y1
        # x label (rotated -45 deg for readability)
        label_x = x + bar_w / 2
        label_y = H - margin["bottom"] + 30
        lines.append(
            f'<text x="{label_x}" y="{label_y}" text-anchor="end" font-size="12" fill="#333" transform="rotate(-45,{label_x},{label_y})">{name}</text>'
        )

    # labels
    lines.append(
        f'<text x="{margin["left"] + plot_w / 2}" y="{H - 18}" text-anchor="middle" font-size="14" fill="#333" font-weight="bold">Intended saturation round</text>'
    )
    lines.append(
        f'<text x="{26}" y="{margin["top"] + plot_h / 2}" text-anchor="middle" transform="rotate(-90,26,{margin["top"] + plot_h / 2})" font-size="14" fill="#333">Mean fraction of SM active cycles</text>'
    )
    lines.append(
        f'<text x="{margin["left"] + plot_w / 2}" y="{30}" text-anchor="middle" font-size="17" font-weight="bold" fill="#222">NCU-reported pipe activity fractions by round</text>'
    )

    # legend
    lx = W - margin["right"] + 20
    ly = margin["top"] + 20
    for i, c in enumerate(components):
        lines.append(f'<rect x="{lx}" y="{ly + i * 26}" width="16" height="16" fill="{COLORS[c]}" stroke="white" stroke-width="1"/>')
        lines.append(f'<text x="{lx + 24}" y="{ly + i * 26 + 12}" font-size="13" fill="#333">{COMPONENT_LABELS[c]}</text>')

    lines.append(svg_end())
    out_path.write_text("\n".join(lines))


def generate_table3(rounds: List[Tuple[int, List[Dict[str, Any]]]], out_path: Path) -> None:
    """Markdown summary table for Section 5.4."""
    lines: List[str] = []
    lines.append("| Round | Intended node | N | Model matches NCU | Accuracy |")
    lines.append("|-------|---------------|---|-------------------|----------|")
    for round_idx, rows in sorted(rounds):
        intended = ROUND_LABELS[round_idx]
        matches = sum(1 for r in rows if r.get("component_match"))
        n = len(rows)
        acc = 100.0 * matches / n if n else 0.0
        lines.append(f"| {round_idx} | {intended} | {n} | {matches} / {n} | {acc:.0f}% |")
    out_path.write_text("\n".join(lines))


def main() -> int:
    paper_dir = Path(__file__).resolve().parent
    data_dir = paper_dir.parent / "20260706-component-saturation-v3"
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}", file=__import__("sys").stderr)
        return 1

    rounds = load_rounds(data_dir)
    if not rounds:
        print("No round data found.", file=__import__("sys").stderr)
        return 1

    figures_dir = paper_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    generate_figure6(rounds, figures_dir / "ncu_activity_by_round.svg")
    generate_table3(rounds, paper_dir / "table3_component_saturation.md")
    print(f"Wrote component-saturation figures and table from {data_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
