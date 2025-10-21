# Physical Warehouse Layout Module

This module extends the warehouse routing system to support **physical dimensions and obstacle detection**. Instead of just using coordinates, you can define racks, aisles, and other warehouse objects with actual width and depth, and the system will automatically:

- ✅ Detect which paths are blocked by obstacles
- ✅ Only create connections that don't pass through non-traversable objects
- ✅ Connect disconnected components intelligently
- ✅ Visualize the physical layout with obstacles

## Files

- **`physical_layout.py`**: Core module for parsing physical warehouse layouts and building obstacle-aware graphs
- **`physical_visualization.py`**: Visualization specifically for physical warehouses with dimensions
- **`example_physical.py`**: Complete working example demonstrating TSP on a physical warehouse
- **`warehouse_physical.json`**: Example warehouse layout with dimensions

## Warehouse JSON Format

The physical warehouse JSON defines objects with:

```json
{
  "id": "Rack_A1",
  "center": {"x": 25, "y": 35},
  "width": 3,
  "depth": 25,
  "type": "rack",
  "traversable": false,
  "pick_points": [
    {"id": "A1-1", "offset": {"x": -2, "y": -10}},
    {"id": "A1-2", "offset": {"x": -2, "y": 0}}
  ]
}
```

### Object Properties

- **`id`**: Unique identifier
- **`center`**: Center coordinates `{x, y}`
- **`width`**: Width of the object (x-dimension)
- **`depth`**: Depth of the object (y-dimension)
- **`type`**: Object type (`rack`, `aisle`, `dock`, `staging`, etc.)
- **`traversable`**: Boolean - whether this area can be traversed
- **`pick_points`**: (Optional) Array of pick locations with offsets from center

### Pick Points

Pick points are defined relative to their parent object's center:

```json
"pick_points": [
  {"id": "A1-1", "offset": {"x": -2, "y": -10}}
]
```

The actual coordinate is calculated as: `parent_center + offset`

## Usage

### Basic Usage

```python
from physical_layout import load_physical_warehouse
from physical_visualization import visualize_physical_warehouse, print_physical_warehouse_summary
from routing import solve_tsp

# Load warehouse and build graph
graph, warehouse = load_physical_warehouse('warehouse_physical.json')

# Print summary
print_physical_warehouse_summary(warehouse, graph)

# Solve TSP for some picks
picks = ['A1-1', 'A1-2', 'B1-1', 'B2-1']
route, distance = solve_tsp(graph, picks)

print(f"Route: {' -> '.join(route)}")
print(f"Distance: {distance:.2f} units")

# Visualize
visualize_physical_warehouse(warehouse, graph)
```

### Advanced: Custom Connection Distance

```python
# Build graph with custom max connection distance
warehouse = PhysicalWarehouse('warehouse_physical.json')
graph = warehouse.build_graph(max_connection_dist=30)
```

## Key Features

### 1. Obstacle Detection

The system automatically detects when a straight-line path between two nodes would pass through a non-traversable object (rack, wall, etc.) and blocks that connection.

```python
# This is done automatically
if warehouse.is_path_clear(x1, y1, x2, y2):
    graph.add_edge(node1, node2)
```

### 2. Smart Component Connection

If the graph ends up with disconnected components (e.g., racks isolated from aisles), the system tries to connect them by finding the shortest clear paths.

### 3. Mixed Node Types

The graph supports multiple node types:
- **Pick points**: Actual inventory locations (red circles in visualization)
- **Aisle waypoints**: Strategic points in aisles for routing (blue squares)

### 4. Visualization

The visualization shows:
- **Gray rectangles**: Non-traversable obstacles (racks, docks, etc.)
- **Green dashed rectangles**: Traversable areas (aisles)
- **Blue edges**: Same-rack connections
- **Orange edges**: Cross-rack connections  
- **Dark green edges**: Through-aisle connections
- **Red circles**: Pick points
- **Blue squares**: Aisle waypoints

## Example Output

```
Building physical warehouse graph...
  Total nodes: 65
  Obstacles: 12
  Traversable areas: 6
  Edges added: 243
  Edges blocked by obstacles: 1796
  Graph connected: False

Optimized TSP route:
  Route: A1-1 -> A1-2 -> A1-3 -> Aisle_A_Center -> B1-1 -> B1-2
  Total distance: 45.23 units
  Racks visited: ['Rack_A1', 'Rack_B1']
```

## Creating Your Own Warehouse

1. **Define the layout structure** - Where are racks, aisles, docks?
2. **Set dimensions** - Width and depth for each object
3. **Mark traversability** - Which areas can be traveled through?
4. **Add pick points** - Where are the inventory locations?
5. **Add aisle waypoints** - Strategic points for routing (optional but recommended)

### Tips

- **Aisle waypoints** greatly improve connectivity - add 2-3 per aisle
- **Cross aisles** should be wide enough to overlap with main aisles
- **Pick points** should be offset from rack centers to be accessible from aisles
- **Max connection distance** of 30 units works well for most warehouses
- **Test connectivity** - the summary will warn if components are disconnected

## Integration with Existing Modules

The physical warehouse module is compatible with existing routing modules:

```python
# Works with find_shortest_path
from routing import find_shortest_path
path, distance = find_shortest_path(graph, 'A1-1', 'B2-3')

# Works with solve_tsp  
from routing import solve_tsp
route, distance = solve_tsp(graph, pick_list)
```

## Troubleshooting

### Disconnected Components

If you see "⚠ Warning: X disconnected components":

1. **Add more aisle waypoints** - Increase coverage
2. **Increase max_connection_dist** - Default is 30, try 40
3. **Widen aisles** - Make sure aisles overlap enough to connect
4. **Check pick point offsets** - Ensure they're accessible from aisles

### Paths Blocked

If many edges are blocked:

1. **Check aisle placement** - Should be between/around racks
2. **Adjust rack dimensions** - Make sure there's space to navigate
3. **Review traversable flags** - Ensure aisles are marked traversable

### Visualization Issues

- Close the plot window to continue program execution
- Use `show_blocked_paths=True` to see what connections were attempted but blocked

## Performance

- **Graph building**: O(n²) where n = number of nodes
- **Obstacle checking**: Uses Shapely for efficient polygon intersection
- **TSP solving**: Uses NetworkX approximation algorithm

For large warehouses (100+ nodes), consider:
- Reducing `max_connection_dist`
- Limiting pick points to specific zones
- Using spatial indexing for obstacle checks (not currently implemented)

## Future Enhancements

Potential improvements:
- [ ] Support for one-way aisles
- [ ] Congestion/traffic modeling
- [ ] Dynamic obstacles (forklifts, pallets)
- [ ] Multi-floor warehouses
- [ ] Equipment size constraints (narrow aisles)
- [ ] Pathfinding with turning costs

---

**See `example_physical.py` for a complete working demonstration.**
