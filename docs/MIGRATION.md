# Migration Guide: LoadData.py → Modular Architecture

## What Changed?

The monolithic `LoadData.py` has been refactored into a clean, modular architecture for better maintainability and reusability.

## New Structure

**Before (1 file):**
```
LoadData.py (300+ lines)
```

**After (4 focused modules):**
```
main.py             - 112 lines (Application orchestration)
warehouse_graph.py  - 335 lines (Core graph building logic)
visualization.py    -  87 lines (Graph visualization)
routing.py          - 114 lines (Pathfinding and TSP)
```

## Migration Steps

### If you were importing LoadData.py:

**Old:**
```python
from LoadData import *
# Everything was in one file
```

**New:**
```python
# Import only what you need
from warehouse_graph import detect_aisles, build_aisle_graph, create_graph_from_edges
from visualization import visualize_warehouse_graph, print_graph_summary
from routing import find_shortest_path, solve_tsp
```

### If you were running LoadData.py directly:

**Old:**
```bash
python LoadData.py
```

**New:**
```bash
python main.py
```

## What Stayed the Same?

- All functionality is preserved
- Same algorithm and logic
- Same input format (warehouse_locations.json)
- Same output and visualizations
- Same parameters and configuration

## Benefits of New Structure

1. **Separation of Concerns** - Each module has a single, clear responsibility
2. **Reusability** - Import only what you need for your specific use case
3. **Maintainability** - Easier to find, understand, and modify code
4. **Testability** - Each module can be tested independently
5. **Extensibility** - Easy to add new features without touching core logic

## Quick Reference

### Building a Graph
```python
from warehouse_graph import detect_aisles, build_aisle_graph, create_graph_from_edges
import pandas as pd
import json

# Load data
with open("warehouse_locations.json") as f:
    locs = pd.DataFrame(json.load(f))

# Detect aisles
locs = detect_aisles(locs, x_tolerance=3, y_tolerance=3)

# Build graph
edges = build_aisle_graph(locs, 
    max_intra_aisle_dist=20,
    only_connect_intersections=True,
    prevent_cross_aisle_shortcuts=True
)

# Create NetworkX graph
G = create_graph_from_edges(locs, edges)
```

### Finding Paths
```python
from routing import find_shortest_path, solve_tsp

# Shortest path
path, distance = find_shortest_path(G, 'A1-1', 'B2-3')

# TSP optimization
picks = ['A1-1', 'B2-2', 'C1-3']
route = solve_tsp(G, picks, cycle=False)
```

### Visualization
```python
from visualization import visualize_warehouse_graph, print_graph_summary

visualize_warehouse_graph(G, locs)
print_graph_summary(G)
```

## Need Help?

Check `README.md` for full documentation and examples.
