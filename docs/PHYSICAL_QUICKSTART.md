# Physical Warehouse Module - Quick Start

## What We Built

A complete physical warehouse representation system that:
1. ✅ Parses warehouse layouts with actual dimensions (width, depth)
2. ✅ Detects obstacles and blocks paths that pass through racks/walls
3. ✅ Creates graphs with only traversable connections
4. ✅ Integrates with existing TSP/routing code
5. ✅ Visualizes physical layout with obstacles

## New Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `physical_layout.py` | Core module - parses JSON, builds obstacle-aware graphs | ~250 |
| `physical_visualization.py` | Visualizes physical warehouses with dimensions | ~150 |
| `example_physical.py` | Working example with TSP | ~150 |
| `warehouse_physical.json` | Example warehouse layout with 6 racks, 44 picks | ~230 |
| `README_PHYSICAL.md` | Complete documentation | - |

## How It Works

### 1. Physical Objects

Each object has:
```json
{
  "id": "Rack_A1",
  "center": {"x": 25, "y": 35},  
  "width": 3,      // x-dimension
  "depth": 25,     // y-dimension
  "traversable": false,  // Can't walk through racks
  "pick_points": [...]
}
```

### 2. Obstacle Detection

```python
# Automatically checks if path intersects obstacles
if warehouse.is_path_clear(x1, y1, x2, y2):
    graph.add_edge(node1, node2)
# Otherwise, connection is blocked
```

Uses Shapely to test line-rectangle intersection.

### 3. Graph Construction

For each pair of nearby nodes:
- Calculate distance
- Check if straight path is clear
- Add edge only if no obstacles block it

Result: **243 edges added, 1796 blocked by obstacles**

### 4. Integration

Works seamlessly with existing modules:

```python
# Load physical warehouse
graph, warehouse = load_physical_warehouse('warehouse_physical.json')

# Use existing routing functions
from routing import find_shortest_path, solve_tsp

path, dist = find_shortest_path(graph, 'A1-1', 'B2-1')
route, dist = solve_tsp(graph, ['A1-1', 'A1-2', 'B1-1'])
```

## Running the Example

```bash
python example_physical.py
```

Output:
```
Building physical warehouse graph...
  Total nodes: 65
  Obstacles: 12
  Traversable areas: 6
  Edges added: 243
  Edges blocked by obstacles: 1796

Optimized TSP route:
  Route: B1-3 -> B1-2 -> B1-1
  Total distance: 16.00 units
  Racks visited: ['Rack_B1']
```

## Key Classes

### `WarehouseObject`
- Represents physical objects (racks, aisles, docks)
- Creates polygon from center/width/depth
- Checks line-polygon intersection
- Extracts pick points with offset calculations

### `PhysicalWarehouse`  
- Loads JSON file
- Separates obstacles from traversable areas
- Builds obstacle-aware graph
- Connects disconnected components

## Configuration

Key parameters in `build_graph()`:

```python
graph = warehouse.build_graph(
    max_connection_dist=30,  # Max distance to try connecting
    verbose=True             # Print progress
)
```

## Visualization Features

- **Gray rectangles**: Obstacles (racks, docks)
- **Green dashed**: Traversable aisles
- **Blue edges**: Same-rack connections
- **Orange edges**: Cross-rack connections
- **Dark green edges**: Through-aisle connections
- **Red circles**: Pick points
- **Blue squares**: Aisle waypoints

## Current Warehouse Layout

```
Dock_Receiving        Staging       Dock_Shipping
    [===]              [====]           [===]

      Rack_A1   Rack_A2      Rack_B1   Rack_B2      Rack_C1   Rack_C2
      [     ]   [     ]      [     ]   [     ]      [     ]   [     ]
      [  6  ]   [  8  ]      [  6  ]   [  6  ]      [  6  ]   [  8  ]
      [picks]   [picks]      [picks]   [picks]      [picks]   [picks]
        
         MainAisle_A           MainAisle_B           MainAisle_C
      [==============]      [==============]      [==============]
```

## Performance

- **65 nodes**: 44 rack picks + 15 aisle waypoints + 6 aisle centers
- **243 edges**: After obstacle filtering
- **1796 blocked**: Paths through obstacles prevented
- **Graph building**: <1 second
- **TSP (10 nodes)**: <1 second

## Improvements Over Simple Coordinates

| Aspect | Simple Coords | Physical Layout |
|--------|--------------|-----------------|
| Realism | Low - connects through obstacles | High - respects physical barriers |
| Setup | Easy - just x,y points | Medium - need dimensions |
| Accuracy | Poor for real warehouses | Good for real warehouses |
| Visualization | Simple dots | Shows actual layout |
| Flexibility | Limited | Can model any layout |

## Next Steps

To use for your own warehouse:

1. **Measure dimensions** - Get width/depth of racks, aisle widths
2. **Create JSON** - Define all objects with centers and dimensions
3. **Add waypoints** - Put 2-3 waypoints in each aisle
4. **Test connectivity** - Run example, check for disconnected components
5. **Adjust parameters** - Tune max_connection_dist if needed

## Example JSON Template

```json
[
  {
    "id": "Rack_A1",
    "center": {"x": 25, "y": 35},
    "width": 3,
    "depth": 25,
    "type": "rack",
    "traversable": false,
    "pick_points": [
      {"id": "A1-1", "offset": {"x": -2, "y": -10}},
      {"id": "A1-2", "offset": {"x": -2, "y": 0}},
      {"id": "A1-3", "offset": {"x": -2, "y": 10}}
    ]
  },
  {
    "id": "MainAisle_A",
    "center": {"x": 20, "y": 35},
    "width": 6,
    "depth": 30,
    "type": "aisle",
    "traversable": true,
    "pick_points": [
      {"id": "Aisle_A_North", "offset": {"x": 0, "y": -12}},
      {"id": "Aisle_A_Center", "offset": {"x": 0, "y": 0}},
      {"id": "Aisle_A_South", "offset": {"x": 0, "y": 12}}
    ]
  }
]
```

## Dependencies

- `shapely` - Polygon intersection (NEW requirement)
- `networkx` - Graph algorithms  
- `matplotlib` - Visualization
- `numpy` - Numerical operations

Install:
```bash
pip install shapely
```

---

**See `README_PHYSICAL.md` for full documentation.**
