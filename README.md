# mapgen
# Hex Map Generator

Generate printable, hex-tiled boards as PDF files with a single command—ideal for tabletop RPGs, board-game prototyping, or classroom geography activities.

* **Centred output** – Hex grid is automatically centred on US-Letter pages, with a legend neatly tucked at the bottom.
* **Procedural terrain** – Dual-layer Perlin noise maps elevation and moisture to five distinct biomes.
* **Themed boards** – Bias toward a primary biome (plains, forest, desert, or mountain) for quick flavour tweaks.
* **Guaranteed diversity** – Specify a minimum number of biomes to avoid monotone maps.
* **Self-contained PDF** – No external assets; share or print right away.

---

## Quick Start

```bash
# 1. Clone
[git clone https://github.com/your-username/hex-map-generator.git](https://github.com/mgelsinger/mapgen.git)
cd mapgen

# 2. Install deps (Python 3.10+)
python -m pip install -r requirements.txt

# 3. Generate a map with default settings
python hex_map_generator.py
