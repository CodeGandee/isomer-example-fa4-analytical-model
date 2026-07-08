#!/usr/bin/env python3
"""Generate a clean SVG for Figure 5 (per-SM execution-unit reservation view)."""
from pathlib import Path

OUT = Path(__file__).with_name("figure5_reservation_execution_system.svg")

W, H = 1500, 460
NODE_W, NODE_H = 150, 46

def rect(x, y, w, h, fill, label, sub="", stroke="#333"):
    rx = 8
    lines = f'<text x="{x+w/2}" y="{y+h/2-3}" text-anchor="middle" font-size="11" font-family="Arial,Helvetica,sans-serif" font-weight="bold" fill="#222">{label}</text>'
    if sub:
        lines += f'<text x="{x+w/2}" y="{y+h/2+12}" text-anchor="middle" font-size="9" font-family="Arial,Helvetica,sans-serif" fill="#444">{sub}</text>'
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>{lines}'

def cluster(x, y, w, h, label, color):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" ry="10" fill="none" stroke="{color}" stroke-width="1.5" stroke-dasharray="4,3"/>' \
           f'<text x="{x+10}" y="{y+22}" text-anchor="start" font-size="12" font-family="Arial,Helvetica,sans-serif" font-weight="bold" fill="{color}">{label}</text>'

def arrow(x1, y1, x2, y2, label="", label_pos=0.5, label_offset=(0,-8), dashed=False):
    color = "#333"
    dash = ' stroke-dasharray="5,3"' if dashed else ""
    marker = ' marker-end="url(#arrowhead)"'
    path = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.2"{marker}{dash}/>'
    text = ""
    if label:
        lx = x1 + (x2 - x1) * label_pos + label_offset[0]
        ly = y1 + (y2 - y1) * label_pos + label_offset[1]
        text = f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="9" font-family="Arial,Helvetica,sans-serif" fill="#222" style="text-shadow: 0 0 2px #fff, 0 0 2px #fff, 0 0 2px #fff;">{label}</text>'
    return path + text

def elbow(points, label="", label_pos=0.5, label_offset=(0,-8), dashed=False):
    pts = " ".join(f"{x},{y}" for x, y in points)
    dash = ' stroke-dasharray="5,3"' if dashed else ""
    marker = ' marker-end="url(#arrowhead)"'
    path = f'<polyline points="{pts}" fill="none" stroke="#333" stroke-width="1.2"{marker}{dash}/>'
    text = ""
    if label:
        i = int(label_pos * (len(points) - 1))
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        lx = (x1 + x2) / 2 + label_offset[0]
        ly = (y1 + y2) / 2 + label_offset[1]
        text = f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="9" font-family="Arial,Helvetica,sans-serif" fill="#222" style="text-shadow: 0 0 2px #fff, 0 0 2px #fff, 0 0 2px #fff;">{label}</text>'
    return path + text

# Positions
mem_x = 95
mem_w = NODE_W
# memory stack: XBAR top, L2 middle, HBM bottom
xbar = (mem_x, 130)
l2   = (mem_x, 250)
hbm  = (mem_x, 370)

# SM pipeline (left-to-right)
sm_y = 200
tma   = (420, sm_y)
tmem  = (600, sm_y)
tc    = (780, sm_y)
sfu   = (960, sm_y)
fp    = (1140, sm_y)
ldst  = (1320, sm_y)

# Scheduler centered above TC/SFU area
sched = (870, 45)

# clusters
mem_cluster = cluster(40, 90, 260, 350, "Memory hierarchy", "#888")
sm_cluster = cluster(340, 90, 1120, 350, "Streaming Multiprocessor (SM) × 176", "#2e7d32")

parts = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
    '<defs>',
    '  <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
    '    <polygon points="0 0, 10 3.5, 0 7" fill="#333"/>',
    '  </marker>',
    '</defs>',
    '<rect width="100%" height="100%" fill="white"/>',
]
parts.append(mem_cluster)
parts.append(sm_cluster)

# Memory nodes
parts.append(rect(hbm[0], hbm[1], NODE_W, NODE_H, "#f4cccc", "HBM3e", "8 TB/s peak"))
parts.append(rect(l2[0], l2[1], NODE_W, NODE_H, "#cfe2f3", "L2 Cache", "64 MB, 24 TB/s"))
parts.append(rect(xbar[0], xbar[1], NODE_W, NODE_H, "#d9ead3", "Crossbar / NoC", ""))

# SM nodes
parts.append(rect(tma[0], tma[1], NODE_W, NODE_H, "#fff2cc", "TMA unit", "async load/store"))
parts.append(rect(tmem[0], tmem[1], NODE_W, NODE_H, "#d9d2e9", "Tensor Memory", "256 KB/SM"))
parts.append(rect(tc[0], tc[1], NODE_W, NODE_H, "#ead1dc", "5th-gen Tensor Cores", "FP16/FP8/FP4 MMA"))
parts.append(rect(sfu[0], sfu[1], NODE_W, NODE_H, "#fce5cd", "SFU", "exp / rsqrt"))
parts.append(rect(fp[0], fp[1], NODE_W, NODE_H, "#fce5cd", "FP32 / INT32", "scale / update"))
parts.append(rect(ldst[0], ldst[1], NODE_W, NODE_H, "#d9ead3", "LD/ST units", "L1 / shared mem"))
parts.append(rect(sched[0], sched[1], NODE_W, NODE_H, "#ddebf7", "Warp Schedulers", "4 per SM"))

# Helpers
def right(n): return (n[0] + NODE_W, n[1] + NODE_H / 2)
def left(n): return (n[0], n[1] + NODE_H / 2)
def top(n): return (n[0] + NODE_W / 2, n[1])
def bottom(n): return (n[0] + NODE_W / 2, n[1] + NODE_H)

# Memory hierarchy arrows (labels on left)
parts.append(arrow(*bottom(xbar), *top(l2), label="miss traffic", label_pos=0.5, label_offset=(-35,0)))
parts.append(arrow(*bottom(l2), *top(hbm), label="miss traffic", label_pos=0.5, label_offset=(-35,0)))

# Crossbar to TMA
parts.append(arrow(*right(xbar), *left(tma), label="coalesced TMA requests", label_pos=0.45, label_offset=(0,-12)))

# Scheduler issue arrows (dashed) from scheduler bottom to unit tops
def sched_arrow(target_x, label):
    x1 = target_x
    y1 = sched[1] + NODE_H
    x2 = target_x
    y2 = sm_y
    return arrow(x1, y1, x2, y2, label=label, dashed=True, label_pos=0.4, label_offset=(7,0))

parts.append(sched_arrow(tc[0] + NODE_W / 2, "issue"))
parts.append(sched_arrow(sfu[0] + NODE_W / 2, "issue"))
parts.append(sched_arrow(fp[0] + NODE_W / 2, "issue"))
parts.append(sched_arrow(ldst[0] + NODE_W / 2, "issue"))

# Pipeline forward arrows (no labels to avoid clutter)
parts.append(arrow(*right(tma), *left(tmem)))
parts.append(arrow(*right(tmem), *left(tc)))
parts.append(arrow(*right(tc), *left(sfu)))
parts.append(arrow(*right(sfu), *left(fp)))
parts.append(arrow(*right(fp), *left(ldst)))

# Feedback paths below the pipeline
parts.append(elbow([(tc[0]+NODE_W/2, tc[1]+NODE_H), (tc[0]+NODE_W/2, tc[1]+NODE_H+24),
                    (tmem[0]+NODE_W/2, tmem[1]+NODE_H+24), (tmem[0]+NODE_W/2, tmem[1]+NODE_H)],
                   label="accumulators", label_pos=0.4, label_offset=(0,14)))
parts.append(elbow([(ldst[0]+NODE_W/2, ldst[1]+NODE_H), (ldst[0]+NODE_W/2, ldst[1]+NODE_H+52),
                    (tma[0]+NODE_W/2, tma[1]+NODE_H+52), (tma[0]+NODE_W/2, tma[1]+NODE_H)],
                   label="async store", label_pos=0.5, label_offset=(0,14)))

# Store path back to memory hierarchy
parts.append(elbow([(tma[0]+NODE_W/2, tma[1]+NODE_H), (tma[0]+NODE_W/2, tma[1]+NODE_H+30),
                    (xbar[0]+NODE_W/2+42, xbar[1]+NODE_H+30), (xbar[0]+NODE_W/2+42, xbar[1]+NODE_H)],
                   label="store O", label_pos=0.75, label_offset=(12,14)))
# XBAR -> L2 -> HBM writeback on right side of memory column
parts.append(arrow(xbar[0]+NODE_W, xbar[1]+NODE_H/2, l2[0]+NODE_W, l2[1]+NODE_H/2,
                   label="writeback", label_pos=0.5, label_offset=(8,0)))
parts.append(arrow(l2[0]+NODE_W, l2[1]+NODE_H/2, hbm[0]+NODE_W, hbm[1]+NODE_H/2,
                   label="dirty evictions", label_pos=0.5, label_offset=(8,0)))

parts.append('</svg>')

OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"wrote {OUT}")
