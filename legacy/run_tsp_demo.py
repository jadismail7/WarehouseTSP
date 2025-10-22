"""
TSP Optimization with Rack-Aware Routing

This script demonstrates complete pick route optimization using:
1. Enhanced graph construction with rack inference
2. TSP algorithm for optimal pick sequence
3. Realistic pathfinding that respects physical rack barriers
"""

import json
import pandas as pd
import time
from warehouse_graph_enhanced import (
    detect_aisles_with_dimensions,
    build_enhanced_graph,
    create_graph_from_edges,
    analyze_graph_quality
)
from routing import solve_tsp, calculate_route_distance


def load_warehouse_data(filename):
    """Load warehouse data from JSON file"""
    with open(filename) as f:
        data = json.load(f)
    return pd.DataFrame(data)


def load_picks(filename):
    """Load pick locations from text file"""
    picks = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                picks.append(line)
    return picks


def run_tsp_with_enhanced_routing(warehouse_file, picks_file, start_location=None):
    """
    Complete TSP optimization workflow:
    1. Load warehouse data
    2. Build enhanced graph with rack awareness
    3. Solve TSP for pick sequence
    4. Calculate complete route with pathfinding
    """
    print("="*80)
    print(f"TSP OPTIMIZATION: {picks_file}")
    print("="*80)
    print()
    
    # Load data
    print(f"Loading warehouse: {warehouse_file}")
    locs = load_warehouse_data(warehouse_file)
    print(f"  Locations: {len(locs)}")
    print()
    
    print(f"Loading picks: {picks_file}")
    picks = load_picks(picks_file)
    print(f"  Picks to collect: {len(picks)}")
    print(f"  Pick list: {', '.join(picks[:5])}{'...' if len(picks) > 5 else ''}")
    print()
    
    # Validate picks
    invalid = [p for p in picks if p not in locs['id'].values]
    if invalid:
        print(f"⚠ Warning: Invalid picks (not in warehouse): {invalid}")
        picks = [p for p in picks if p in locs['id'].values]
        print(f"  Continuing with {len(picks)} valid picks")
        print()
    
    # Build enhanced graph
    print("Building enhanced graph with rack inference...")
    start_time = time.time()
    
    locs = detect_aisles_with_dimensions(locs, x_tolerance=5, y_tolerance=5, min_aisle_size=3)
    edges = build_enhanced_graph(locs, max_intra_aisle_dist=25, max_cross_aisle_dist=20, 
                                 min_clearance=1.0, verbose=False)
    G = create_graph_from_edges(locs, edges)
    
    build_time = time.time() - start_time
    print(f"  Graph built in {build_time:.2f}s")
    
    # Analyze graph
    analyze_graph_quality(G, locs, verbose=True)
    print()
    
    # Determine start location
    if start_location is None:
        # Use first staging area or first location
        staging = locs[locs['type'] == 'staging']
        if len(staging) > 0:
            start_location = staging.iloc[0]['id']
        else:
            start_location = locs.iloc[0]['id']
    
    print(f"Starting location: {start_location}")
    print()
    
    # Solve TSP
    print("Solving TSP for optimal pick sequence...")
    start_time = time.time()
    
    # Build route with start location
    route_to_optimize = [start_location] + picks
    best_order = solve_tsp(G, route_to_optimize, cycle=False)
    
    if best_order is None:
        print("  ❌ TSP solving failed")
        return None
    
    # Calculate distance
    best_distance = calculate_route_distance(G, best_order)
    
    tsp_time = time.time() - start_time
    print(f"  TSP solved in {tsp_time:.2f}s")
    print()
    
    # Display results
    print("-"*80)
    print("OPTIMAL ROUTE")
    print("-"*80)
    print(f"Total distance: {best_distance:.2f} units")
    print(f"Number of stops: {len(best_order)}")
    print()
    
    print("Pick sequence:")
    for i, loc in enumerate(best_order, 1):
        loc_data = locs[locs['id'] == loc].iloc[0]
        print(f"  {i:2d}. {loc:20s} (Zone {loc_data['zone']}, Type: {loc_data['type']})")
    
    print()
    
    # Calculate segment distances
    print("-"*80)
    print("ROUTE SEGMENTS")
    print("-"*80)
    
    total_dist = 0
    for i in range(len(best_order) - 1):
        from_loc = best_order[i]
        to_loc = best_order[i + 1]
        
        # Calculate segment distance
        segment_dist = calculate_route_distance(G, [from_loc, to_loc])
        total_dist += segment_dist
        
        # Get direct distance
        from_data = locs[locs['id'] == from_loc].iloc[0]
        to_data = locs[locs['id'] == to_loc].iloc[0]
        direct_dist = ((from_data['x'] - to_data['x'])**2 + 
                      (from_data['y'] - to_data['y'])**2)**0.5
        
        detour_pct = (segment_dist / direct_dist - 1) * 100 if direct_dist > 0 else 0
        
        print(f"  {from_loc:15s} → {to_loc:15s}  "
              f"{segment_dist:6.1f} units  "
              f"(direct: {direct_dist:5.1f}, detour: +{detour_pct:4.0f}%)")
    
    print()
    print(f"Total route distance: {total_dist:.2f} units")
    print()
    
    # Zone statistics
    print("-"*80)
    print("ZONE DISTRIBUTION")
    print("-"*80)
    
    zone_counts = {}
    for loc in best_order[1:]:  # Skip start location
        zone = locs[locs['id'] == loc].iloc[0]['zone']
        zone_counts[zone] = zone_counts.get(zone, 0) + 1
    
    for zone, count in sorted(zone_counts.items()):
        print(f"  Zone {zone}: {count} picks")
    
    print()
    print("="*80)
    print("✓ TSP optimization complete!")
    print("="*80)
    print()
    
    return {
        'picks': picks,
        'route': best_order,
        'distance': best_distance,
        'graph_nodes': G.number_of_nodes(),
        'graph_edges': G.number_of_edges(),
        'build_time': build_time,
        'tsp_time': tsp_time
    }


def main():
    """Run TSP on both small and large warehouses"""
    
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "TSP WITH RACK-AWARE ROUTING" + " "*31 + "║")
    print("╚" + "="*78 + "╝")
    print("\n")
    
    results = []
    
    # Small warehouse
    print("\n" + "▀"*80)
    print("SMALL WAREHOUSE TEST")
    print("▀"*80 + "\n")
    
    result_small = run_tsp_with_enhanced_routing(
        warehouse_file="data/warehouse_locations.json",
        picks_file="data/picks_small_test.txt",
        start_location="Staging_1"
    )
    results.append(('Small', result_small))
    
    # Large warehouse
    print("\n" + "▀"*80)
    print("LARGE WAREHOUSE TEST")
    print("▀"*80 + "\n")
    
    result_large = run_tsp_with_enhanced_routing(
        warehouse_file="data/warehouse_locations_large.json",
        picks_file="data/picks_large_test.txt",
        start_location="Staging_West"
    )
    results.append(('Large', result_large))
    
    # Summary comparison
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*28 + "COMPARISON SUMMARY" + " "*32 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    print(f"{'Warehouse':<15} {'Picks':<8} {'Distance':<12} {'Nodes':<8} {'Edges':<8} {'Build':<10} {'TSP':<10}")
    print("-"*80)
    
    for name, result in results:
        print(f"{name:<15} "
              f"{len(result['picks']):<8} "
              f"{result['distance']:>10.1f}u  "
              f"{result['graph_nodes']:<8} "
              f"{result['graph_edges']:<8} "
              f"{result['build_time']:>8.2f}s  "
              f"{result['tsp_time']:>8.2f}s")
    
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Automatic rack inference from bin clustering")
    print("  ✓ No shortcuts through shelves (realistic routing)")
    print("  ✓ TSP optimization for minimal total distance")
    print("  ✓ Pathfinding respects physical obstacles")
    print()


if __name__ == "__main__":
    main()
