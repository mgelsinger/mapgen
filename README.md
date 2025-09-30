# Mapgen — Hex Map Generator

Generate printable, hex‑tiled boards as PDF files with a single command. Ideal for tabletop RPGs, board‑game prototyping, or classroom activities.

- Centred output — Grid is centred on US‑Letter pages with a legend at the bottom.
- Procedural terrain — Dual Perlin noise for elevation and moisture → five biomes.
- Themed boards — Bias toward plains, forest, desert, or mountain.
- Guaranteed diversity — Enforce a minimum number of distinct biomes.
- Self‑contained PDFs — No external assets required.

---

## Quick Start

```bash
# 1) Clone
git clone https://github.com/mgelsinger/mapgen.git
cd mapgen

# 2) (Optional) Create a virtual environment
python -m venv .venv
# Windows
. .venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

# 3) Install dependencies (Python 3.10+)
python -m pip install -r requirements.txt

# 4) Generate a map with default settings
python hex_map_generator.py
```

This writes a timestamped PDF like `hex_map_YYYYMMDD_HHMMSS_<seed>.pdf` in the current directory. Print at 100% scale on US‑Letter.

---

## Usage

Show all options:

```bash
python hex_map_generator.py -h
```

Key options:

- `--hex-size <int>`: Hex radius in points (default: 25)
- `--margin <int>`: Page margin in points (default: 36)
- `--legend-size <int>`: Legend square size in points (default: 12)
- `--bias {plains,forest,desert,mountain}`: Primary biome bias
- `--bias-strength <float>`: Strength of the bias (default: 0.35)
- `--min-biomes <int>`: Minimum number of distinct biomes (default: 3)
- `--seed <int>`: Fixed seed for reproducible maps
- `--attempts <int>`: Max regeneration attempts to meet diversity (default: 5)

Examples:

```bash
# Forest-biased map with default settings
python hex_map_generator.py --bias forest

# Strong mountain bias and fixed seed (reproducible)
python hex_map_generator.py --bias mountain --bias-strength 0.6 --seed 12345

# Larger hexes and margins
python hex_map_generator.py --hex-size 32 --margin 48

# Encourage variety: require at least four biomes
python hex_map_generator.py --min-biomes 4
```

Output details:

- Page size: US‑Letter (`8.5" × 11"`).
- Grid: Centred fully inside page margins.
- Legend: Biome swatches and labels centred at bottom.
- Filename: `hex_map_<timestamp>_<seed>.pdf`.

---

## How It Works

- Elevation and moisture fields are generated with Perlin noise (`noise.pnoise2`).
- Biomes are assigned from elevation/moisture thresholds with optional primary‑biome bias.
- Simple adjacency constraints reduce unlikely borders (e.g., desert directly next to forest becomes plains) and clean up isolated tiles.
- PDFs are rendered with ReportLab.

Biomes: water, plains, forest, desert, mountain.

---

## Requirements

- Python 3.10+
- `pip install -r requirements.txt`
  - `noise`
  - `reportlab`

---

## Troubleshooting

- Module not found (`noise` or `reportlab`): run `python -m pip install -r requirements.txt`.
- Wrong Python version: ensure `python --version` reports 3.10 or newer.
- PDF looks off when printing: print at 100% (no “fit to page”).

---

## Contributing

Issues and pull requests are welcome. If you add options or change defaults, please update this README and keep the CLI help clear and concise.
