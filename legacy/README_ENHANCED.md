# Enhanced Warehouse Graph Construction

## Overview

This directory contains an **enhanced version** of the warehouse graph construction algorithm that leverages the new physical properties (`width`, `depth`, `traversable`) added to location data.

## Key Improvements

### 1. **Automatic Rack Inference** 🏭
The enhanced algorithm automatically detects rack structures by clustering picking locations (bins) that are close together. This eliminates the need to manually specify rack information.

```python
# Bins with similar coordinates are grouped into racks
locs = infer_racks_from_bins(locs, bin_spacing_tolerance=3)
# Each bin gets a 'rack_id' automatically
```

**Benefits:**
- No manual rack definition needed
- Racks are inferred from bin layout
- More accurate representation of physical storage

### 2. **Traversability-Aware Routing** 🚫
The algorithm respects the `traversable` flag to distinguish between:
- **Traversable areas**: Aisles, intersections, staging areas (robots can move through)
- **Non-traversable obstacles**: Offices, packing stations, racks (robots must go around)

```python
# Only traversable locations are used for routing
traversable_locs = locs[locs['traversable'] == True]
```

**Benefits:**
- More realistic paths that respect physical barriers
- Prevents impossible routes through walls/racks
- Better separation of movement areas vs. work areas

### 3. **Physical Obstacle Detection** 📐
Uses `width` and `depth` properties to check if paths intersect with physical obstacles:

```python
# Check if line from A to B passes through any obstacle
if is_path_blocked(point_a, point_b, locs, min_clearance=1.0):
    # Don't create this connection
```

**Benefits:**
- Prevents connections that would require passing through obstacles
- Accounts for physical dimensions, not just center points
- Configurable clearance buffer for safety

### 4. **Dimension-Aware Aisle Detection** 📏
Enhanced aisle detection considers physical dimensions:

```python
# Detect aisles using physical properties
locs = detect_aisles_with_dimensions(locs, x_tolerance=5, y_tolerance=5)
```

**Benefits:**
- Better clustering of locations into aisles
- Accounts for the actual footprint of locations
- More accurate aisle boundaries

## File Structure

```
legacy/
├── warehouse_graph.py              # Original graph construction
├── warehouse_graph_enhanced.py     # ⭐ Enhanced with physical properties
├── main.py                         # Original main script
├── main_enhanced.py               # ⭐ Enhanced main script
├── routing.py                     # Routing utilities (TSP, shortest path)
├── compare_graphs.py              # ⭐ Compare legacy vs enhanced
└── visualization.py               # Graph visualization
```

## Usage

### Run Enhanced Version

```bash
# Basic usage with large warehouse
python legacy/main_enhanced.py

# Specify custom data file
python legacy/main_enhanced.py --data data/warehouse_locations.json

# Save visualization to file
python legacy/main_enhanced.py --output output/enhanced_graph.png

# Quiet mode (less verbose)
python legacy/main_enhanced.py --quiet

# Skip demos
python legacy/main_enhanced.py --no-demo
```

### Compare Legacy vs Enhanced

```bash
# Run side-by-side comparison
python legacy/compare_graphs.py

# Use custom data file
python legacy/compare_graphs.py data/warehouse_locations_large.json
```

## Data Format Requirements

The enhanced algorithm requires location data with these properties:

```json
{
  "id": "A1-1",
  "x": 50,
  "y": 50,
  "type": "picking",
  "zone": "A",
  "width": 2,        // ⭐ Required: physical width
  "depth": 2,        // ⭐ Required: physical depth
  "traversable": true // ⭐ Required: can robots move here?
}
```

### Property Guidelines

| Location Type | Width | Depth | Traversable | Notes |
|--------------|-------|-------|-------------|-------|
| Picking bins | 2 | 2 | true | Small points, accessible |
| Docks | 15 | 8 | false | Loading areas, blocked |
| Staging | 20 | 10 | true | Open areas for movement |
| Aisles | 8-240 | 6-200 | true | Corridors for navigation |
| Intersections | 8 | 8 | true | Junction points |
| Offices | 20 | 15 | false | Buildings, blocked |
| Packing stations | 12 | 8 | false | Work areas, blocked |
| Charging | 12 | 8 | true | Service points |

## Algorithm Comparison

### Legacy Approach
1. Cluster locations by coordinates (DBSCAN)
2. Connect nodes in same aisle
3. Add cross-aisle connections at intersections
4. Prevent opposite shelf shortcuts

**Limitations:**
- Doesn't consider physical obstacles
- All locations treated as points
- Manual rack specification needed
- May create impossible paths through obstacles

### Enhanced Approach
1. ✅ Infer racks from bin clustering
2. ✅ Filter to traversable locations only
3. ✅ Cluster traversable locations into aisles
4. ✅ Check line-of-sight for obstacle blocking
5. ✅ Create connections only where physically possible
6. ✅ Use dimensions for clearance calculations

**Improvements:**
- Automatic rack detection
- Respects physical barriers
- Dimension-aware path validation
- More accurate graph representation

## Example Output

```
===================================================================
ENHANCED WAREHOUSE TSP - Physical Layout Aware
===================================================================

Loading warehouse data from: data/warehouse_locations_large.json
Loaded 175 locations
  - Traversable: 165
  - Obstacles: 10

Detecting aisle structures and inferring racks...
  - Vertical aisles: 6
  - Horizontal aisles: 5
  - Inferred racks from bins: 24

Building enhanced warehouse graph...
Graph building: 165 traversable nodes, 10 obstacles
Detected 24 rack structure(s) from bin locations
Found 23 intersection points

============================================================
GRAPH QUALITY ANALYSIS
============================================================
Nodes: 175 (165 traversable, 10 obstacles)
Edges: 312
Average degree: 3.57
Connected: True (1 component(s))
Inferred racks: 24
============================================================
```

## Performance Considerations

### Memory
- Enhanced approach uses similar memory to legacy
- Additional properties per node: ~24 bytes
- Obstacle checking adds negligible overhead

### Speed
- Graph construction: ~10-50ms for typical warehouses
- Obstacle checking: O(n×m) where n=edges, m=obstacles
- TSP solving: Same as legacy (depends on algorithm)

### Scalability
- Handles 1000+ locations efficiently
- Obstacle checking is the main bottleneck
- Consider spatial indexing for very large warehouses (1000+ obstacles)

## Tuning Parameters

```python
# Aisle detection sensitivity
x_tolerance=5      # Horizontal clustering tolerance
y_tolerance=5      # Vertical clustering tolerance
min_aisle_size=3   # Minimum nodes to form an aisle

# Connection distances
max_intra_aisle_dist=25   # Max distance within same aisle
max_cross_aisle_dist=20   # Max distance across aisles

# Obstacle avoidance
min_clearance=1.0  # Minimum clearance from obstacles (units)
```

## Future Enhancements

Potential improvements for consideration:

1. **Spatial Indexing**: Use R-tree or quadtree for faster obstacle queries
2. **Dynamic Obstacles**: Support moving obstacles (other robots)
3. **Multi-level Warehouses**: Handle vertical dimensions (z-coordinate)
4. **Traffic Rules**: One-way aisles, priority lanes
5. **Path Smoothing**: Post-process paths to reduce sharp turns
6. **Visibility Graphs**: More sophisticated obstacle avoidance

## References

- DBSCAN Clustering: Ester et al., 1996
- TSP Approximations: Christofides, 1976
- NetworkX Documentation: https://networkx.org/
- Obstacle Avoidance: Line-Rectangle Intersection

## License

Same as parent project.
