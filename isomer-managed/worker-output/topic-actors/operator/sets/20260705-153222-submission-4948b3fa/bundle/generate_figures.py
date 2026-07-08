#!/usr/bin/env python3
"""Generate SVG figures for the real-hardware FA4 B200 paper bundle."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


def load_rows(csv_path: Path) -> List[Dict[str, float | str]]:
    rows: List[Dict[str, float | str]] = []
    with csv_path.open(newline="") as f:
        for r in csv.DictReader(f):
            if r["measured_runtime_ms"] == "":
                continue
            rows.append(
                {
                    "batch": int(r["batch"]),
                    "heads": int(r["heads"]),
                    "seqlen": int(r["seqlen"]),
                    "head_dim": int(r["head_dim"]),
                    "causal": r["causal"],
                    "precision": r["precision"],
                    "predicted_runtime_ms": float(r["predicted_runtime_ms"]),
                    "measured_runtime_ms": float(r["measured_runtime_ms"]),
                    "predicted_bottleneck": r["predicted_bottleneck"],
                    "split": csv_path.stem.split("_")[1],  # validation or query
                }
            )
    return rows


def svg_start(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="sans-serif" font-size="12">\n'
    )


def svg_end() -> str:
    return "</svg>\n"


def log_ticks(min_val: float, max_val: float) -> List[float]:
    ticks: List[float] = []
    start = 10 ** math.floor(math.log10(max(min_val, 1e-6)))
    v = start
    while v <= max_val * 1.1:
        ticks.append(v)
        v *= 10
    return ticks


def fmt_ms(v: float) -> str:
    if v >= 1:
        return f"{v:.1f}"
    if v >= 0.1:
        return f"{v:.2f}"
    return f"{v:.3f}"


def generate_figure1(rows: List[Dict[str, float | str]], out_path: Path) -> None:
    W, H = 600, 520
    margin = dict(top=40, right=40, bottom=70, left=70)
    plot_w = W - margin["left"] - margin["right"]
    plot_h = H - margin["top"] - margin["bottom"]

    preds = np.array([float(r["predicted_runtime_ms"]) for r in rows])
    meas = np.array([float(r["measured_runtime_ms"]) for r in rows])
    min_val = max(min(preds.min(), meas.min()), 1e-4)
    max_val = max(preds.max(), meas.max()) * 1.05

    def tx(v: float) -> float:
        return margin["left"] + plot_w * (math.log10(max(v, min_val / 10)) - math.log10(min_val)) / (
            math.log10(max_val) - math.log10(min_val)
        )

    def ty(v: float) -> float:
        return margin["top"] + plot_h * (
            1 - (math.log10(max(v, min_val / 10)) - math.log10(min_val)) / (math.log10(max_val) - math.log10(min_val))
        )

    colors = {"bf16": "#1f77b4", "fp16": "#ff7f0e", "fp8": "#2ca02c"}

    lines: List[str] = []
    lines.append(svg_start(W, H))
    lines.append(f'<rect width="{W}" height="{H}" fill="white"/>')

    # 30% bands
    band_min = np.linspace(min_val, max_val, 200)
    upper = band_min * 1.30
    lower = band_min / 1.30
    pts_upper = " ".join(f"{tx(x)},{ty(y)}" for x, y in zip(band_min, upper))
    pts_lower = " ".join(f"{tx(x)},{ty(y)}" for x, y in zip(band_min, lower))
    lines.append(
        f'<polygon points="{pts_upper} {pts_lower[::-1]}" fill="#eeeeee" stroke="none"/>'
    )

    # identity line
    lines.append(
        f'<line x1="{tx(min_val)}" y1="{ty(min_val)}" x2="{tx(max_val)}" y2="{ty(max_val)}" '
        'stroke="#333" stroke-width="1.5"/>'
    )

    # grid ticks
    for t in log_ticks(min_val, max_val):
        x = tx(t)
        y = ty(t)
        lines.append(f'<line x1="{x}" y1="{margin["top"]}" x2="{x}" y2="{H - margin["bottom"]}" stroke="#ddd"/>')
        lines.append(f'<line x1="{margin["left"]}" y1="{y}" x2="{W - margin["right"]}" y2="{y}" stroke="#ddd"/>')
        lines.append(f'<text x="{x}" y="{H - margin["bottom"] + 18}" text-anchor="middle">{fmt_ms(t)}</text>')
        lines.append(f'<text x="{margin["left"] - 10}" y="{y + 4}" text-anchor="end">{fmt_ms(t)}</text>')

    # points
    for r in rows:
        px = tx(float(r["predicted_runtime_ms"]))
        py = ty(float(r["measured_runtime_ms"]))
        c = colors.get(str(r["precision"]), "#333")
        lines.append(f'<circle cx="{px}" cy="{py}" r="2.5" fill="{c}" opacity="0.6"/>')

    # labels
    lines.append(
        f'<text x="{margin["left"] + plot_w / 2}" y="{H - 20}" text-anchor="middle" font-size="13">Predicted runtime (ms)</text>'
    )
    lines.append(
        f'<text x="{20}" y="{margin["top"] + plot_h / 2}" text-anchor="middle" transform="rotate(-90,20,{margin["top"] + plot_h / 2})" font-size="13">Measured runtime (ms)</text>'
    )
    lines.append(
        f'<text x="{margin["left"]}" y="{25}" font-size="14" font-weight="bold">Figure 1: Predicted vs. measured runtime (real B200)</text>'
    )

    # legend
    lx = W - margin["right"] - 80
    ly = margin["top"] + 10
    for i, (label, color) in enumerate(colors.items()):
        lines.append(f'<rect x="{lx}" y="{ly + i * 18}" width="10" height="10" fill="{color}"/>')
        lines.append(f'<text x="{lx + 15}" y="{ly + i * 18 + 9}" font-size="11">{label}</text>')
    lines.append(f'<text x="{lx}" y="{ly + 60}" font-size="10" fill="#666">Shaded band = \u00b130%</text>')

    lines.append(svg_end())
    out_path.write_text("\n".join(lines))


def generate_figure2(rows: List[Dict[str, float | str]], out_path: Path) -> None:
    W, H = 600, 420
    margin = dict(top=50, right=40, bottom="80", left=70)
    plot_w = W - margin["left"] - int(margin["right"])
    plot_h = H - margin["top"] - int(margin["bottom"])

    residuals = [(float(r["predicted_runtime_ms"]) - float(r["measured_runtime_ms"])) / float(r["measured_runtime_ms"]) * 100 for r in rows]
    labels = [str(r["predicted_bottleneck"]) for r in rows]
    groups: Dict[str, List[float]] = {}
    for lab, res in zip(labels, residuals):
        groups.setdefault(lab, []).append(res)
    # order by count desc
    ordered = sorted(groups.keys(), key=lambda k: -len(groups[k]))
    y_min = min(residuals) - 5
    y_max = max(residuals) + 5
    y_range = y_max - y_min

    def tx(i: int) -> float:
        return margin["left"] + (i + 0.5) * (plot_w / len(ordered))

    def ty(v: float) -> float:
        return margin["top"] + plot_h * (1 - (v - y_min) / y_range)

    lines: List[str] = []
    lines.append(svg_start(W, H))
    lines.append(f'<rect width="{W}" height="{H}" fill="white"/>')

    # zero line
    lines.append(
        f'<line x1="{margin["left"]}" y1="{ty(0)}" x2="{W - margin["right"]}" y2="{ty(0)}" stroke="#333" stroke-width="1.5"/>'
    )

    # y grid
    for v in np.linspace(round(y_min / 10) * 10, round(y_max / 10) * 10, 9):
        if y_min <= v <= y_max:
            lines.append(
                f'<line x1="{margin["left"]}" y1="{ty(v)}" x2="{W - margin["right"]}" y2="{ty(v)}" stroke="#eee"/>'
            )
            lines.append(f'<text x="{margin["left"] - 8}" y="{ty(v) + 4}" text-anchor="end" font-size="10">{int(v)}</text>')

    colors = {"bf16": "#1f77b4", "fp16": "#ff7f0e", "fp8": "#2ca02c"}
    for i, lab in enumerate(ordered):
        vals = np.array(groups[lab])
        med = float(np.median(vals))
        q1 = float(np.percentile(vals, 25))
        q3 = float(np.percentile(vals, 75))
        x = tx(i)
        # box
        lines.append(
            f'<rect x="{x - 15}" y="{ty(q3)}" width="30" height="{ty(q1) - ty(q3)}" fill="#ddd" stroke="#333"/>'
        )
        # median line
        lines.append(f'<line x1="{x - 15}" y1="{ty(med)}" x2="{x + 15}" y2="{ty(med)}" stroke="#333" stroke-width="2"/>')
        # points jittered
        for r, res in zip(rows, residuals):
            if str(r["predicted_bottleneck"]) != lab:
                continue
            jitter = (hash(str(r["seqlen"]) + str(r["batch"])) % 21) - 10
            c = colors.get(str(r["precision"]), "#333")
            lines.append(
                f'<circle cx="{x + jitter}" cy="{ty(res)}" r="2" fill="{c}" opacity="0.5"/>'
            )
        lines.append(f'<text x="{x}" y="{H - int(margin["bottom"]) + 18}" text-anchor="middle" font-size="11">{lab}</text>')
        lines.append(f'<text x="{x}" y="{H - int(margin["bottom"]) + 34}" text-anchor="middle" font-size="9" fill="#666">n={len(vals)}</text>')

    lines.append(
        f'<text x="{margin["left"] + plot_w / 2}" y="{H - 15}" text-anchor="middle" font-size="13">Predicted bottleneck</text>'
    )
    lines.append(
        f'<text x="{18}" y="{margin["top"] + plot_h / 2}" text-anchor="middle" transform="rotate(-90,18,{margin["top"] + plot_h / 2})" font-size="13">Residual (%)</text>'
    )
    lines.append(
        f'<text x="{margin["left"]}" y="{25}" font-size="14" font-weight="bold">Figure 2: Residual distribution by predicted bottleneck</text>'
    )

    # legend
    lx = W - margin["right"] - 80
    ly = margin["top"] + 10
    for i, (label, color) in enumerate(colors.items()):
        lines.append(f'<rect x="{lx}" y="{ly + i * 18}" width="10" height="10" fill="{color}"/>')
        lines.append(f'<text x="{lx + 15}" y="{ly + i * 18 + 9}" font-size="11">{label}</text>')

    lines.append(svg_end())
    out_path.write_text("\n".join(lines))


def main() -> int:
    base = Path(__file__).resolve().parent
    val_csv = base / "refined_validation_predictions.csv"
    query_csv = base / "refined_query_predictions.csv"
    rows: List[Dict[str, float | str]] = []
    for p in [val_csv, query_csv]:
        if p.exists():
            rows.extend(load_rows(p))
    if not rows:
        print("No prediction rows found.", file=sys.stderr)
        return 1

    generate_figure1(rows, base / "figure1_predicted_vs_measured.svg")
    generate_figure2(rows, base / "figure2_residuals_by_bottleneck.svg")
    print(f"Wrote {len(rows)} points to figures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
