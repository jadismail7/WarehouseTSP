# Quick Reference: TSP with Rack-Aware Routing

## 🚀 Quick Start

### Run Complete TSP Demo (Recommended)
```powershell
python legacy/run_tsp_demo.py
```
Runs TSP on both small and large warehouses with full analysis.

---

## 📋 Available Commands

### 1. **Full TSP Demo** (Both Warehouses)
```powershell
python legacy/run_tsp_demo.py
```
- Tests small warehouse (8 picks)
- Tests large warehouse (20 picks)
- Shows comparison summary
- **Time:** ~3 seconds total

### 2. **Rack Routing Demonstration**
```powershell
python legacy/demo_rack_routing.py
```
- Shows rack detection details
- Demonstrates opposite-side blocking
- Examples of detours around racks
- **Time:** ~2 seconds

### 3. **Enhanced Graph Analysis**
```powershell
python legacy/main_enhanced.py --no-demo
```
- Builds graph for large warehouse
- Shows connectivity analysis
- Displays rack detection
- No route optimization
- **Time:** ~2 seconds

### 4. **Custom Picks File**
```powershell
python legacy/main_enhanced.py --picks data/picks_large_test.txt --tsp
```
- Run TSP with specific pick list
- Works with any valid picks file

### 5. **Legacy vs Enhanced Comparison**
```powershell
python legacy/compare_graphs.py
```
- Side-by-side comparison
- Shows improvements from rack awareness

---

## 📁 Test Data Files

### Small Warehouse
- **Layout:** `data/warehouse_locations.json` (27 locations)
- **Picks:** `data/picks_small_test.txt` (8 items)
- **Zones:** A, B, C
- **Racks:** 5 (2 pairs)

### Large Warehouse
- **Layout:** `data/warehouse_locations_large.json` (181 locations)
- **Picks:** `data/picks_large_test.txt` (20 items)
- **Zones:** A, B, C, D, E, F
- **Racks:** 12 (6 pairs)

---

## 🎯 What Each Demo Shows

| Demo | Graph Building | Rack Detection | TSP Optimization | Routing Details |
|------|----------------|----------------|------------------|-----------------|
| `run_tsp_demo.py` | ✅ | ✅ | ✅ | ✅ Full route |
| `demo_rack_routing.py` | ✅ | ✅ Detailed | ❌ | ✅ Examples only |
| `main_enhanced.py --no-demo` | ✅ | ✅ | ❌ | ❌ |
| `main_enhanced.py --tsp` | ✅ | ✅ | ✅ | ✅ Full route |
| `compare_graphs.py` | ✅ Both | ✅ | ❌ | ✅ Comparison |

---

## 📊 Expected Output

### run_tsp_demo.py Output Structure
```
╔══════════════════════════════════╗
║  TSP WITH RACK-AWARE ROUTING     ║
╚══════════════════════════════════╝

▀▀▀ SMALL WAREHOUSE TEST ▀▀▀
  - Loading data
  - Building graph (5 racks, 2 pairs)
  - Solving TSP (8 picks)
  - Optimal route: 232.3 units
  - Route segments with detours
  - Zone distribution

▀▀▀ LARGE WAREHOUSE TEST ▀▀▀
  - Loading data
  - Building graph (12 racks, 6 pairs)
  - Solving TSP (20 picks)
  - Optimal route: 2,139.6 units
  - Route segments with detours
  - Zone distribution

╔══════════════════════════════════╗
║      COMPARISON SUMMARY          ║
╚══════════════════════════════════╝
  Small: 8 picks, 232.3u, 0.07s build, 0.00s TSP
  Large: 20 picks, 2,139.6u, 2.32s build, 0.03s TSP
```

---

## 🔍 Understanding the Results

### Graph Quality Metrics
```
Nodes: 171          # Traversable locations
Edges: 191          # Allowed connections
Average degree: 2.23  # Connectivity (sparse = realistic)
Connected: True     # All locations reachable
Racks: 12 (6 pairs) # Auto-detected structures
```

### Route Segments
```
A1-1 → A1-2  15.0 units (direct: 15.0, detour: +0%)
  ↑ Direct connection within same aisle side

B1-2 → B2-3  25.0 units (direct: 15.0, detour: +67%)
  ↑ Must go around rack (opposite sides)
```

### Detour Percentages
- **0% detour:** Direct path available (same side or via intersection)
- **67% detour:** Must route around rack end (typical for opposite sides)
- **Higher detours:** Multiple obstacles or longer alternative paths

---

## 💡 Tips

### Creating Custom Pick Lists
1. Create a text file (e.g., `my_picks.txt`)
2. Add one location ID per line
3. Use `#` for comments
4. Run: `python legacy/main_enhanced.py --picks data/my_picks.txt --tsp`

### Valid Location IDs
- **Small warehouse:** A1-1 to C1-4, Staging_1, Staging_2, CrossAisle_1-3
- **Large warehouse:** A1-1 to F4-12, Staging_West/East, Docks, etc.
- Use `--no-demo` mode to see all available locations

### Performance Notes
- **Small warehouse:** Near-instant (<0.1s)
- **Large warehouse:** ~2-3 seconds total
- Graph building is the slowest part (one-time cost)
- TSP solving is very fast (<0.05s even for 20 picks)

---

## 🐛 Troubleshooting

### "No module named 'warehouse_graph_enhanced'"
```powershell
# Make sure you're in the project root directory
cd C:\Users\ismailjad\src\WarehouseTSP
python legacy/run_tsp_demo.py
```

### "Location not found" errors
- Check that pick IDs match locations in warehouse file
- Location IDs are case-sensitive
- Run with `--no-demo` to see valid location list

### Graph disconnected warnings
- Normal during building (bridging happens automatically)
- Final result should show "Connected: True"
- If stays disconnected, check data file format

---

## 📚 Documentation

- **Full technical docs:** `legacy/README_ENHANCED.md`
- **Enhancement summary:** `legacy/ENHANCEMENT_SUMMARY.md`
- **TSP integration:** `legacy/TSP_SUMMARY.md` (this file)
- **Main README:** `README.md`

---

## ✅ Success Indicators

When everything works correctly, you should see:
- ✅ "Connected: True" in graph analysis
- ✅ "Inferred racks: X (Y pairs detected)"
- ✅ "Paths will route around racks"
- ✅ All detour percentages make sense (0% or ~67%)
- ✅ No error messages
- ✅ Routes visit all picks exactly once

**Happy optimizing! 🚀**
