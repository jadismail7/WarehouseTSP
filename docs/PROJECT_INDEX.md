# Warehouse TSP Project - Complete File Index

## Project Structure

```
Warehouse TSP/
├── Core Modules (Original - Coordinate-Based)
│   ├── main.py                      # Entry point for coordinate-based system
│   ├── warehouse_graph.py           # DBSCAN clustering, aisle detection
│   ├── visualization.py             # Graph visualization
│   ├── routing.py                   # Pathfinding and TSP
│   └── warehouse_locations.json     # Simple coordinate data (27 nodes)
│
├── Physical Layout Modules (NEW - Dimension-Based)
│   ├── physical_layout.py           # Obstacle-aware graph construction
│   ├── physical_visualization.py    # Physical warehouse visualization  
│   ├── example_physical.py          # Physical warehouse demo
│   └── warehouse_physical.json      # Physical layout with dimensions
│
├── Documentation
│   ├── README.md                    # Original modular system docs
│   ├── MIGRATION.md                 # Migration from monolithic to modular
│   ├── README_PHYSICAL.md           # Physical layout comprehensive guide
│   └── PHYSICAL_QUICKSTART.md       # Quick start for physical system
│
└── Examples
    └── example_quiet.py             # Minimal output example
```

## Module Comparison

### Coordinate-Based System (Original)

**Use when:** You have simple x,y coordinates without physical dimensions

**Modules:**
- `warehouse_graph.py` - Automatic aisle detection via DBSCAN
- `visualization.py` - Color-coded graph visualization
- `routing.py` - Shortest path and TSP
- `main.py` - Orchestration and entry point

**Data Format:**
```json
{
  "id": "A1-1",
  "x": 25,
  "y": 35,
  "type": "pick",
  "zone": "A"
}
```

**Key Features:**
- ✅ DBSCAN automatic aisle clustering
- ✅ Opposite shelf detection  
- ✅ Intersection-only connections
- ✅ Configurable verbosity

**Run:**
```bash
python main.py
```

### Physical Layout System (NEW)

**Use when:** You have actual warehouse dimensions and need obstacle awareness

**Modules:**
- `physical_layout.py` - Polygon-based obstacle detection
- `physical_visualization.py` - Shows physical dimensions
- `example_physical.py` - Complete demo with TSP
- `routing.py` - Reused from coordinate system

**Data Format:**
```json
{
  "id": "Rack_A1",
  "center": {"x": 25, "y": 35},
  "width": 3,
  "depth": 25,
  "traversable": false,
  "pick_points": [
    {"id": "A1-1", "offset": {"x": -2, "y": -10}}
  ]
}
```

**Key Features:**
- ✅ Obstacle collision detection (Shapely)
- ✅ Physical dimensions (width, depth)
- ✅ Traversable vs non-traversable areas
- ✅ Pick points as offsets from parent objects
- ✅ Automatic component connection

**Run:**
```bash
python example_physical.py
```

## File Details

### Core Python Modules

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 112 | Entry point for coordinate-based system |
| `warehouse_graph.py` | 335 | DBSCAN clustering, aisle detection, graph building |
| `visualization.py` | 87 | Graph visualization with edge coloring |
| `routing.py` | 130 | Shortest path, TSP, demonstrations |
| `physical_layout.py` | ~250 | Physical warehouse parsing, obstacle detection |
| `physical_visualization.py` | ~150 | Visualize physical dimensions and obstacles |
| `example_physical.py` | ~150 | Physical warehouse TSP demonstration |
| `example_quiet.py` | 20 | Minimal output example |

**Total:** ~1,234 lines of Python code

### Data Files

| File | Format | Nodes | Description |
|------|--------|-------|-------------|
| `warehouse_locations.json` | Simple | 27 | Coordinate-only data (id, x, y, type, zone) |
| `warehouse_physical.json` | Physical | 65 | Dimensions + obstacles (18 objects, 44 picks, 15 waypoints) |

### Documentation

| File | Pages | Coverage |
|------|-------|----------|
| `README.md` | ~8 | Modular system architecture, usage, API |
| `MIGRATION.md` | ~3 | Migration from monolithic to modular design |
| `README_PHYSICAL.md` | ~12 | Complete physical layout documentation |
| `PHYSICAL_QUICKSTART.md` | ~6 | Quick reference for physical system |

## Feature Matrix

| Feature | Coordinate System | Physical System |
|---------|------------------|-----------------|
| Automatic aisle detection | ✅ DBSCAN | ➖ Manual definition |
| Obstacle awareness | ❌ | ✅ Polygon intersection |
| Physical dimensions | ❌ | ✅ Width, depth |
| Opposite shelf routing | ✅ | ✅ Via obstacle blocking |
| TSP optimization | ✅ | ✅ |
| Shortest path | ✅ | ✅ |
| Visualization | ✅ 2D graph | ✅ Physical layout |
| Setup complexity | Low | Medium |
| Realism | Medium | High |
| Best for | Quick prototypes | Real warehouses |

## Dependencies

### Core Dependencies
```python
pandas           # DataFrame manipulation
networkx         # Graph algorithms, TSP
scikit-learn     # DBSCAN clustering
matplotlib       # Visualization
numpy            # Numerical operations
```

### Physical Layout Additional
```python
shapely          # NEW: Polygon intersection detection
```

## Installation

```bash
# Core system
pip install pandas networkx scikit-learn matplotlib numpy

# Physical layout system (add shapely)
pip install shapely
```

## Quick Start

### Coordinate-Based System

```python
from main import main

# Run with full output
graph, locations = main(verbose=True, show_demo=True)

# Run quietly
graph, locations = main(verbose=False, show_demo=False)
```

### Physical Layout System

```python
from physical_layout import load_physical_warehouse
from routing import solve_tsp

# Load and build graph
graph, warehouse = load_physical_warehouse('warehouse_physical.json')

# Solve TSP
picks = ['A1-1', 'A1-2', 'B1-1']
route, distance = solve_tsp(graph, picks)
```

## Performance

### Coordinate System
- **Nodes:** 27
- **Edges:** 34
- **Graph build:** <0.1s
- **TSP (10 nodes):** <0.1s

### Physical System  
- **Nodes:** 65 (44 picks + 15 waypoints + 6 centers)
- **Edges:** 243 (after blocking 1796 obstacle-crossing paths)
- **Graph build:** ~0.5s
- **TSP (10 nodes):** ~0.5s

## Algorithm Complexity

| Operation | Coordinate | Physical |
|-----------|-----------|----------|
| DBSCAN clustering | O(n log n) | N/A |
| Graph construction | O(n²) | O(n²) |
| Obstacle checking | N/A | O(k) per edge, k=obstacles |
| TSP approximation | O(n²) | O(n²) |
| Shortest path | O(E log V) | O(E log V) |

## Use Cases

### Use Coordinate System When:
- 📍 You only have x,y coordinates
- 🚀 Quick prototyping needed
- 📊 Warehouse layout is simple  
- 🔄 Automatic aisle detection desired

### Use Physical System When:
- 📏 You have actual warehouse dimensions
- 🚧 Obstacle avoidance is critical
- 🏢 Modeling a real warehouse facility
- 📐 Layout has complex geometries
- 🎯 High accuracy required

## Integration Points

Both systems share:
- `routing.py` - Same TSP and shortest path algorithms work with both graph types
- NetworkX Graph structure - Both produce compatible graphs
- Visualization philosophy - Both use matplotlib with color-coded edges

## Future Enhancements

### Both Systems
- [ ] Multi-floor support
- [ ] Dynamic obstacles
- [ ] Real-time path updates
- [ ] Batch picking optimization

### Coordinate System
- [ ] Better automatic aisle detection
- [ ] Support for irregular layouts

### Physical System
- [ ] One-way aisles
- [ ] Equipment size constraints
- [ ] Congestion modeling
- [ ] Spatial indexing for large warehouses

## Version History

1. **v0.1** - Monolithic k-NN based system
2. **v0.2** - Rigid aisle-based topology
3. **v0.3** - DBSCAN automatic detection
4. **v0.4** - Opposite shelf routing
5. **v0.5** - Modular refactoring (4 modules)
6. **v0.6** - Logging cleanup
7. **v1.0** - **Physical layout system** ⭐ (Current)

## Getting Help

- **Coordinate system:** See `README.md`
- **Physical system:** See `README_PHYSICAL.md` 
- **Quick start:** See `PHYSICAL_QUICKSTART.md`
- **Migration:** See `MIGRATION.md`

## License

[Your license here]

## Contributors

[Your name here]

---

**Last Updated:** 2024
**Status:** ✅ Production Ready
