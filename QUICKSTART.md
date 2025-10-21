# Quick Reference Guide

## Project Organization (Updated)

The project has been reorganized into a clean, modular structure:

```
Warehouse TSP/
├── warehouse_tsp.py          ← Main CLI tool (START HERE)
├── physical/                 ← Core system (current/production)
├── legacy/                   ← Old coordinate-based system (reference only)
├── examples/                 ← Demo scripts
├── data/                     ← Warehouse configs & pick lists
├── output/                   ← Generated visualizations (auto-created)
└── docs/                     ← Documentation
```

## Common Tasks

### 1. Solve a Pick Route
```bash
python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt
```

### 2. Compare Algorithms
```bash
python examples/compare_tsp.py data/warehouse_large.json data/picks_sample.txt 50
```

### 3. Visualize Graph Only
```bash
python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt \
    --visualize graph --no-display
```

### 4. Custom Options
```bash
python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt \
    --start Staging_Area_West \
    --end Charging_Station_1 \
    --method greedy \
    --max-dist 50 \
    --stats \
    --output output/my_route.png
```

## File Locations

### Input Files
- **Warehouse configs**: `data/warehouse_*.json`
- **Pick lists**: `data/picks_*.txt`

### Output Files
- **All visualizations**: `output/*.png` (auto-generated)

### Code Modules
- **Physical system**: `physical/` (USE THIS)
- **Legacy system**: `legacy/` (reference only)

### Documentation
- **Main README**: `README.md` (root)
- **Detailed docs**: `docs/`

## Creating New Pick Lists

Create a text file in `data/`:
```
# data/my_picks.txt
A1-7
A1-8
B1-3
C1-10
```

Then run:
```bash
python warehouse_tsp.py data/warehouse_large.json data/my_picks.txt
```

## Algorithm Choice

- **greedy**: Fast, good for real-time routing
- **2-opt** (default): 20-30% better, still fast
- **exhaustive**: Optimal but slow (≤10 picks only)

## Output Location

All visualizations automatically save to `output/`:
- Default: `output/warehouse_solution.png`
- Custom: `--output output/myfile.png`

## Help

```bash
python warehouse_tsp.py --help
```
