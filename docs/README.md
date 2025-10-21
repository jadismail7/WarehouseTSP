# Warehouse TSP - Intelligent Graph-Based Routing

Automatic warehouse graph construction with intelligent aisle detection, opposite shelf routing, and TSP optimization.

## Features

✅ **Automatic Aisle Detection** - Uses DBSCAN clustering to detect vertical and horizontal aisles from coordinates alone  
✅ **Opposite Shelf Detection** - Identifies paired aisles and prevents illegal shortcuts through shelves  
✅ **Smart Intersection Routing** - Only allows cross-aisle connections at designated intersection points  
✅ **Aisle-End Connections** - Allows going around aisle ends to reach opposite sides  
✅ **Full Connectivity** - Automatically ensures all warehouse zones are reachable  
✅ **TSP Optimization** - Solves traveling salesman problems for pick route optimization  
✅ **Visual Graph Analysis** - Color-coded visualization showing aisle structure and edge types  

## Project Structure

```
Warehouse TSP/
├── main.py                    # Main application entry point
├── warehouse_graph.py         # Core graph building and aisle detection
├── visualization.py           # Graph visualization utilities
├── routing.py                 # Pathfinding and TSP optimization
├── warehouse_locations.json   # Warehouse location data
└── LoadData.py               # (Legacy - can be removed)
```

## Module Overview

### `warehouse_graph.py`
Core graph construction logic:
- `detect_aisles()` - Detects vertical/horizontal aisles and opposite shelf pairs using DBSCAN
- `build_aisle_graph()` - Constructs edges with intelligent connection rules
- `create_graph_from_edges()` - Creates NetworkX graph with node attributes

### `visualization.py`
Graph visualization and analysis:
- `visualize_warehouse_graph()` - Displays graph with color-coded edges and nodes
- `print_graph_summary()` - Prints connectivity statistics

### `routing.py`
Pathfinding and optimization:
- `find_shortest_path()` - A* shortest path between two locations
- `solve_tsp()` - TSP optimization for pick routes
- `demonstrate_opposite_shelf_routing()` - Shows routing examples

### `main.py`
Application orchestration:
- Loads warehouse data
- Builds graph with configured parameters
- Runs examples and demonstrations

## Quick Start

```bash
# Run the main application
python main.py
```

This will:
1. Load warehouse locations from JSON
2. Detect aisle structures automatically
3. Build the warehouse graph
4. Show visualizations
5. Run pathfinding examples
6. Demonstrate opposite shelf routing

## Configuration

Key parameters in `main.py`:

```python
# Aisle detection sensitivity
detect_aisles(locs, 
    x_tolerance=3,        # Clustering tolerance for vertical aisles
    y_tolerance=3,        # Clustering tolerance for horizontal aisles
    min_aisle_size=3      # Minimum nodes to form an aisle
)

# Graph building rules
build_aisle_graph(locs,
    max_intra_aisle_dist=20,           # Max distance within aisle
    max_cross_aisle_dist=15,           # Max distance for cross-aisle connections
    only_connect_intersections=True,   # Only connect at intersections (prevents shortcuts)
    prevent_cross_aisle_shortcuts=True # Prevent walking through shelves
)
```

## Input Data Format

JSON file with location data:

```json
[
  {
    "id": "A1-1",
    "x": 25,
    "y": 30,
    "type": "picking",
    "zone": "A"
  },
  ...
]
```

**Required fields:**
- `id` - Unique location identifier
- `x` - X coordinate
- `y` - Y coordinate

**Optional fields:**
- `type` - Location type (picking, dock, staging, etc.)
- `zone` - Zone identifier

## Example Output

```
Detecting aisle structures...
Detected 5 vertical aisles
Detected 3 horizontal aisles

Detected aisle pairs (opposite shelves):
  Pair 0: LEFT=['A1-1', 'A1-2', 'A1-3'] | RIGHT=['A2-1', 'A2-2', 'A2-3']
  Pair 1: LEFT=['B1-1', 'B1-2', 'B1-3', 'B1-4'] | RIGHT=['B2-1', 'B2-2', 'B2-3', 'B2-4']

Graph has 27 nodes and 34 edges
Graph is connected: True

Edge breakdown:
  Intra-aisle edges: 26 (within same aisle)
  Cross-aisle edges: 2 (at intersection points ONLY)
  Connector edges: 6 (to isolated nodes)
```

## Use Cases

### 1. Basic Pathfinding
```python
from routing import find_shortest_path

path, distance = find_shortest_path(G, 'Dock_Receiving', 'B1-1')
print(f"Path: {' -> '.join(path)}")
print(f"Distance: {distance:.2f} units")
```

### 2. Pick Route Optimization
```python
from routing import solve_tsp

picks = ['A1-1', 'A2-2', 'C1-1', 'B1-2']
route = solve_tsp(G, picks, cycle=False)
print(f"Optimal route: {' -> '.join(route)}")
```

### 3. Custom Graph Building
```python
from warehouse_graph import detect_aisles, build_aisle_graph

locs = detect_aisles(locs, x_tolerance=5, min_aisle_size=2)
edges = build_aisle_graph(locs, 
    only_connect_intersections=False,  # Allow more connections
    prevent_cross_aisle_shortcuts=False # Allow direct cross-aisle paths
)
```

## Key Concepts

### Opposite Shelf Routing
Items on opposite sides of the same aisle (e.g., A1-2 and A2-2) appear close but require going around the aisle end. The system:
- Detects paired aisles automatically
- Blocks direct connections in the middle
- Allows connections at aisle ends
- Routes around obstacles realistically

### Intersection-Only Connections
Cross-aisle connections only occur at designated intersection points (nodes belonging to both vertical and horizontal aisles), preventing unrealistic mid-aisle shortcuts.

## Dependencies

- `pandas` - Data manipulation
- `networkx` - Graph algorithms
- `scikit-learn` - DBSCAN clustering
- `matplotlib` - Visualization
- `numpy` - Numerical operations

Install with:
```bash
pip install pandas networkx scikit-learn matplotlib numpy
```

## Troubleshooting

**No aisles detected:**
- Reduce `x_tolerance` or `y_tolerance`
- Lower `min_aisle_size` to 2

**Disconnected graph:**
- Increase `max_cross_aisle_dist`
- Set `only_connect_intersections=False`

**Too many cross-shelf shortcuts:**
- Set `prevent_cross_aisle_shortcuts=True`
- Verify aisle pairs are detected correctly

## License

MIT License - Feel free to use and modify for your warehouse routing needs!
