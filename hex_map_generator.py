#!/usr/bin/env python3
"""
hex_map_generator.py - centered PDF hex-board generator

• US-Letter (8.5×11″) output with timestamped filename
• Dual-layer Perlin noise → elevation + moisture → five biomes
• Optional primary-biome bias for themed boards
• Guarantees ≥ --min-biomes distinct biomes (default 3)
• Hex grid is fully centred **inside the page margins**; legend sits at bottom

Dependencies
------------
    pip install noise reportlab
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from noise import pnoise2
except ImportError:
    sys.exit("Missing 'noise' – install with: pip install noise")
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas as pdfcanvas
except ImportError:
    sys.exit("Missing 'reportlab' – install with: pip install reportlab")

PAGE_W, PAGE_H = letter  # 612 × 792 pt   (1 pt ≈ 0.3528 mm)

# ───────────────────────────────────── data ──────────────────────────────────
@dataclass(frozen=True)
class Biome:
    name: str
    color: colors.Color


BIOMES: Dict[str, Biome] = {
    "water":    Biome("Water",    colors.Color(0.29, 0.47, 0.78)),
    "plains":   Biome("Plains",   colors.Color(0.55, 0.74, 0.46)),
    "forest":   Biome("Forest",   colors.Color(0.11, 0.34, 0.20)),
    "desert":   Biome("Desert",   colors.Color(0.93, 0.83, 0.47)),
    "mountain": Biome("Mountain", colors.Color(0.40, 0.34, 0.27)),
}
PRIMARY_OPTIONS = [b for b in BIOMES if b != "water"]

# ────────────────────────────────── geometry ─────────────────────────────────
def axial_to_pixel(q: int, r: int, s: float) -> Tuple[float, float]:
    """Axial → Cartesian (pointy-top orientation)."""
    return s * 1.5 * q, s * math.sqrt(3) * (r + 0.5 * (q & 1))


def hex_corners(cx: float, cy: float, s: float) -> List[Tuple[float, float]]:
    """Return the six corner points of a hex centred at (cx, cy)."""
    return [
        (cx + s * math.cos(math.radians(60 * i)),
         cy + s * math.sin(math.radians(60 * i)))
        for i in range(6)
    ]

# ───────────────────────────────── generator ────────────────────────────────
class HexMapGenerator:
    _DIRS = [(+1, 0), (-1, 0), (+1, -1), (-1, +1), (0, +1), (0, -1)]

    def __init__(
        self,
        *,
        hex_size: int = 25,
        margin: int = 36,
        legend_size: int = 12,
        bias: str | None = None,
        bias_strength: float = 0.35,
        max_attempts: int = 5,
        seed: int | None = None,
        min_biomes: int = 3,
    ) -> None:
        if bias and bias not in PRIMARY_OPTIONS:
            raise ValueError(f"bias must be one of {PRIMARY_OPTIONS}")
        self.hex_size, self.margin, self.legend_size = hex_size, margin, legend_size
        self.bias = bias or random.choice(PRIMARY_OPTIONS)
        self.bias_strength = bias_strength
        self.max_attempts, self.min_biomes = max_attempts, max(1, min_biomes)
        self.seed = seed or random.randrange(1 << 30)
        random.seed(self.seed)
        self.elev_noise_scale, self.moist_noise_scale = (
            random.uniform(0.9, 2.0),
            random.uniform(0.9, 2.0),
        )
        self.tiles: Dict[Tuple[int, int], str] = {}
        self._calc_grid()

    # ───────────────────────────── layout math ─────────────────────────────
    def _calc_grid(self) -> None:
        """
        Calculate column/row counts and centring offsets.

        • Leaves a double bottom margin (≈ legend height) so legend never
          collides with grid.
        • Ensures the grid's **outer hex edges** are inside the margins,
          then centres that bounding box.
        """
        s = self.hex_size
        h = 1.5 * s              # centre-to-centre horizontal step
        v = math.sqrt(3) * s     # centre-to-centre vertical step

        avail_w = PAGE_W - 2 * self.margin          # within L/R margins
        avail_h = PAGE_H - 3 * self.margin          # top margin + avail_h + double bottom margin

        self.n_cols = int(avail_w // h)
        self.n_rows = int(avail_h // v)

        self.grid_w = h * (self.n_cols - 1) + 2 * s  # full bounding width
        self.grid_h = v * (self.n_rows - 1) + 2 * s  # full bounding height

        # Offsets so outer hex edges sit centred in the available rectangle.
        self.off_x = self.margin + s + (avail_w - self.grid_w) / 2
        self.off_y = self.margin + s + (avail_h - self.grid_h) / 2

    # ───────────────────────────── generation ──────────────────────────────
    def run(self) -> Path:
        for _ in range(self.max_attempts):
            self._generate()
            self._enforce()
            if len(set(self.tiles.values())) >= self.min_biomes:
                pdf = self._render()
                self._summary(pdf)
                return pdf
        raise RuntimeError("Couldn’t hit biome-diversity target.")

    def _generate(self) -> None:
        self.tiles.clear()
        for q in range(self.n_cols):
            for r in range(self.n_rows):
                nx = q / self.n_cols * self.elev_noise_scale
                ny = r / self.n_rows * self.elev_noise_scale
                elev = pnoise2(nx, ny, octaves=4, repeatx=1024, repeaty=1024)
                moist = pnoise2(nx + 100, ny + 100, octaves=4, repeatx=1024, repeaty=1024)
                elev, moist = self._bias(elev, moist)
                self.tiles[(q, r)] = self._biome(elev, moist)

    def _bias(self, e: float, m: float) -> Tuple[float, float]:
        if self.bias == "desert":
            m -= self.bias_strength
        elif self.bias == "forest":
            m += self.bias_strength
        elif self.bias == "mountain":
            e += self.bias_strength
        elif self.bias == "plains":
            e -= 0.2 * self.bias_strength
            m += 0.1 * self.bias_strength
        return e, m

    @staticmethod
    def _biome(e: float, m: float) -> str:
        if e < -0.05:
            return "water"
        if e > 0.55:
            return "mountain"
        if m < -0.1:
            return "desert"
        if m > 0.25:
            return "forest"
        return "plains"

    # ───────────────────────────── constraints ─────────────────────────────
    def _nbrs(self, q: int, r: int):
        return [(q + dq, r + dr) for dq, dr in self._DIRS if (q + dq, r + dr) in self.tiles]

    def _enforce(self) -> None:
        # Desert next to forest → plains
        for (q, r), b in list(self.tiles.items()):
            if b == "desert" and any(self.tiles[n] == "forest" for n in self._nbrs(q, r)):
                self.tiles[(q, r)] = "plains"
        # Desert next to water → plains
        for (q, r), b in list(self.tiles.items()):
            if b == "desert" and any(self.tiles[n] not in ("plains", "mountain", "desert")
                                     for n in self._nbrs(q, r)):
                self.tiles[(q, r)] = "plains"
        # Isolated mountain/desert → convert to majority neighbour
        for (q, r), b in list(self.tiles.items()):
            if b in ("mountain", "desert") and all(self.tiles[n] != b for n in self._nbrs(q, r)):
                nb = [self.tiles[n] for n in self._nbrs(q, r)]
                self.tiles[(q, r)] = max(set(nb), key=nb.count)

    # ────────────────────────────── drawing ────────────────────────────────
    @staticmethod
    def _hex(c: pdfcanvas.Canvas, pts: List[Tuple[float, float]], col: colors.Color) -> None:
        p = c.beginPath()
        p.moveTo(*pts[0])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        p.close()
        c.setFillColor(col)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.3)
        c.drawPath(p, stroke=1, fill=1)

    def _render(self) -> Path:
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        out = Path(f"hex_map_{ts}_{self.seed}.pdf").resolve()
        c = pdfcanvas.Canvas(str(out), pagesize=letter)

        # Draw hexes
        for (q, r), b in self.tiles.items():
            px, py = axial_to_pixel(q, r, self.hex_size)
            self._hex(c, hex_corners(px + self.off_x, py + self.off_y, self.hex_size),
                      BIOMES[b].color)

        # Legend (horizontally centred at bottom)
        order = list(BIOMES.keys())
        c.setFont("Helvetica", 9)
        label_w = [c.stringWidth(BIOMES[k].name, "Helvetica", 9) for k in order]
        total = sum(self.legend_size + 14 + w + 12 for w in label_w) - 12
        lx, ly = (PAGE_W - total) / 2, self.margin / 2 + 8
        for k, w in zip(order, label_w):
            biome = BIOMES[k]
            c.setFillColor(biome.color)
            c.rect(lx, ly, self.legend_size, self.legend_size, fill=1, stroke=1)
            c.setFillColor(colors.black)
            c.drawString(lx + self.legend_size + 14, ly + 2, biome.name)
            lx += self.legend_size + 14 + w + 12

        # Footer debug/info line
        c.setFont("Helvetica", 6)
        info = " | ".join(
            [
                f"Seed:{self.seed}",
                f"Primary:{self.bias}({self.bias_strength:.2f})",
                f"ElevScale:{self.elev_noise_scale:.2f}",
                f"MoistScale:{self.moist_noise_scale:.2f}",
                f"Hex:{self.hex_size}px",
                f"Grid:{self.n_cols}x{self.n_rows}",
                f"MinBiomes:{self.min_biomes}",
            ]
        )
        c.drawString(self.margin, self.margin / 4, info)

        c.showPage()
        c.save()
        return out

    # ────────────────────────────── summary ────────────────────────────────
    def _summary(self, path: Path) -> None:
        print("Generated PDF:", path)
        print("Re-run with: --seed", self.seed)

# ─────────────────────────────────── CLI ────────────────────────────────────
def cli() -> None:
    p = argparse.ArgumentParser(
        description="Generate centred printable hex-grid PDF maps"
    )
    p.add_argument("--hex-size", type=int, default=25, help="hex radius (pt)")
    p.add_argument("--margin", type=int, default=36, help="page margin (pt)")
    p.add_argument("--legend-size", type=int, default=12, help="legend square size (pt)")
    p.add_argument("--bias", choices=PRIMARY_OPTIONS, help="primary biome bias")
    p.add_argument("--bias-strength", type=float, default=0.35, help="bias strength")
    p.add_argument("--min-biomes", type=int, default=3, help="minimum distinct biomes")
    p.add_argument("--seed", type=int, help="force seed for reproducibility")
    p.add_argument("--attempts", type=int, default=5, help="max regeneration attempts")
    args = p.parse_args()

    gen = HexMapGenerator(
        hex_size=args.hex_size,
        margin=args.margin,
        legend_size=args.legend_size,
        bias=args.bias,
        bias_strength=args.bias_strength,
        min_biomes=args.min_biomes,
        seed=args.seed,
        max_attempts=args.attempts,
    )
    gen.run()

if __name__ == "__main__":
    cli()
