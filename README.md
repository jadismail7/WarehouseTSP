# Warehouse TSP Solver

A modular system for optimizing pick routes in physical warehouses using graph theory and TSP algorithms.

## Quick Start

```bash
# Basic usage - solve TSP on a warehouse with picks
python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt

# With options
python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt \
    --method 2-opt \
    --max-dist 50 \
    --visualize route \
    --stats

# Compare algorithms
python examples/compare_tsp.py data/warehouse_large.json data/picks_sample.txt 50
```

## Project Structure

```
Warehouse TSP/
├── warehouse_tsp.py          # Main CLI entry point
├── physical/                  # Physical warehouse system (CURRENT)
│   ├── physical_layout.py         # Graph construction with obstacles
│   ├── physical_visualization.py  # Visualization functions
│   ├── routing.py                 # Pathfinding and TSP algorithms
│   └── __init__.py
├── legacy/                    # Legacy coordinate-based system
│   ├── warehouse_graph.py
│   ├── visualization.py
│   ├── main.py
│   └── __init__.py
├── examples/                  # Example scripts and demos
│   ├── compare_tsp.py            # Compare TSP algorithms
│   ├── example_large_route.py    # Large warehouse demo
│   ├── example_physical.py       # Basic physical demo
│   └── show_large_warehouse.py   # Display warehouse stats
├── data/                      # Warehouse configs and pick lists
│   ├── warehouse_large.json      # 15 racks, 176 picks
│   ├── warehouse_physical.json   # 6 racks, small warehouse
│   ├── warehouse_locations.json  # Legacy coordinate system
│   ├── picks_sample.txt          # 20 pick locations
│   └── picks_small.txt           # 8 picks (for exhaustive)
├── output/                    # Generated visualizations (git-ignored)
│   ├── warehouse_solution.png
│   └── warehouse_graph.png
└── docs/                      # Documentation
    ├── README_PHYSICAL.md
    ├── PHYSICAL_QUICKSTART.md
    └── PROJECT_INDEX.md
```

## Features

### Physical Warehouse System
- **Obstacle-aware pathfinding**: Uses Shapely for polygon intersection detection
- **Corner waypoints**: Efficient rack navigation without backtracking
- **Mixed orientations**: Handles vertical and horizontal racks
- **Multiple TSP algorithms**: Greedy, 2-opt, exhaustive search

### TSP Algorithms
- **Greedy (O(n²))**: Fast nearest-neighbor heuristic
- **2-opt (O(n²) per iteration)**: Local search improvement, typically 20-30% better than greedy
- **Exhaustive (O(n!))**: Optimal solution for ≤10 picks

### Command-Line Interface
```bash
python warehouse_tsp.py <warehouse_json> <picks_file> [options]

Options:
  --start START         Starting location ID
  --end END             Ending location ID
  --method METHOD       TSP algorithm: greedy, 2-opt, exhaustive (default: 2-opt)
  --max-dist DIST       Maximum connection distance (default: 30)
  --visualize TYPE      Visualization: none, graph, route, both (default: route)
  --output PATH         Save visualization to file (default: output/warehouse_solution.png)
  --no-display          Don't show plot window
  --stats               Show detailed statistics
```

## Usage Examples

### 1. Basic Route Optimization
```bash
python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt \
    --max-dist 50 \
    --no-display
```

### 2. Compare Algorithms
```bash
python examples/compare_tsp.py data/warehouse_large.json data/picks_sample.txt 50
```
Output:
```
COMPARISON
      greedy:    1249.57 units (+89.22 units)
       2-opt:    1160.35 units ← BEST
```

### 3. Visualize Graph Only
```bash
python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt \
    --visualize graph \
    --output output/my_graph.png \
    --no-display
```

### 4. Custom Start/End with Statistics
```bash
python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt \
    --start Staging_Area_West \
    --end Charging_Station_1 \
    --method greedy \
    --stats
```

## Pick List Format

Create a text file with one location ID per line:
```
# picks_sample.txt
# Lines starting with # are comments

A1-7
A1-8
B1-3
C1-10
...
```

## Warehouse JSON Format

See `data/warehouse_large.json` for example. Key structure:
```json
{
  "objects": [
    {
      "id": "Rack_A1",
      "type": "rack",
      "center": {"x": 10, "y": 50},
      "width": 3,
      "depth": 60,
      "traversable": false,
      "pick_points": [
        {"id": "A1-1", "offset": {"x": -2, "y": -28}}
      ]
    }
  ]
}
```

## Algorithm Performance

**Large Warehouse (15 racks, 20 picks):**
- Greedy: 1249.57 units
- 2-opt: 1160.35 units (7.1% improvement)
- Typical improvement: 20-30% for complex routes

## Requirements

```bash
pip install networkx shapely matplotlib numpy pandas scikit-learn
```

## Development

### Legacy System (deprecated)
The original coordinate-based system is in `legacy/`. It uses k-NN connectivity without physical dimensions. Use `physical/` for all new development.

### Adding New TSP Algorithms
Add to `physical/routing.py`:
1. Implement `_solve_tsp_yourmethod()`
2. Add to `solve_tsp_with_endpoints()` method parameter
3. Test with `compare_tsp.py`

## License

MIT
