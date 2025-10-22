#!/usr/bin/env python3
"""
Warehouse TSP Solver - Main Entry Point

Usage:
    python warehouse_tsp.py <warehouse_json> <picks_file> [options]

Arguments:
    warehouse_json    Path to warehouse layout JSON file
    picks_file        Path to file with pick locations (one per line)
    
Options:
    --start START     Starting location ID (default: first traversable area)
    --end END         Ending location ID (default: same as start)
    --method METHOD   TSP algorithm: greedy, 2-opt, exhaustive (default: 2-opt)
    --max-dist DIST   Maximum connection distance (default: 30)
    --visualize TYPE  Visualization: none, graph, route, both (default: route)
    --output PATH     Save visualization to file (default: output/warehouse_solution.png)
    --no-display      Don't show plot window, only save to file
    --stats           Show detailed statistics
    
Examples:
    # Basic usage with 2-opt algorithm
    python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt
    
    # Use greedy algorithm with custom start/end
    python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt \
        --start Staging_Area_West --end Charging_Station_1 --method greedy
    
    # Visualize full graph without solving
    python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt \
        --visualize graph --no-display
    
    # Get detailed statistics only
    python warehouse_tsp.py data/warehouse_large.json data/picks_sample.txt \
        --visualize none --stats
"""

import argparse
import sys
from pathlib import Path
import json
import pandas as pd

# Import enhanced graph construction and visualization
from legacy.warehouse_graph_enhanced import (
    detect_aisles_with_dimensions,
    build_enhanced_graph,
    create_graph_from_edges,
    analyze_graph_quality
)
from legacy.routing import solve_tsp, calculate_route_distance
from legacy.visualization_enhanced import (
    visualize_graph_with_racks,
    visualize_route_with_racks
)

from cli_utils import load_picks_file


def load_warehouse_data(filename):
    """Load warehouse data from JSON file"""
    with open(filename) as f:
        data = json.load(f)
    return pd.DataFrame(data)


def find_default_start(locs):
    """Find a suitable default start location (staging area or first traversable)"""
    # Try staging areas first
    staging = locs[locs['type'] == 'staging']
    if len(staging) > 0:
        return staging.iloc[0]['id']
    
    # Fall back to first traversable location
    traversable = locs[locs['traversable'] == True]
    if len(traversable) > 0:
        return traversable.iloc[0]['id']
    
    # Last resort: first location
    return locs.iloc[0]['id']


def main():
    parser = argparse.ArgumentParser(
        description='Warehouse TSP Solver - Optimize pick routes in warehouses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('warehouse_json', help='Path to warehouse layout JSON file')
    parser.add_argument('picks_file', help='Path to file with pick locations (one per line)')
    parser.add_argument('--start', help='Starting location ID')
    parser.add_argument('--end', help='Ending location ID')
    parser.add_argument('--method', choices=['greedy', '2-opt', 'exhaustive'], 
                       default='2-opt', help='TSP algorithm (default: 2-opt)')
    parser.add_argument('--max-dist', type=float, default=30.0,
                       help='Maximum connection distance (default: 30)')
    parser.add_argument('--visualize', choices=['none', 'graph', 'route', 'both'],
                       default='route', help='Visualization type (default: route)')
    parser.add_argument('--output', help='Save visualization to file (default: output/warehouse_solution.png)')
    parser.add_argument('--no-display', action='store_true',
                       help="Don't show plot window, only save to file")
    parser.add_argument('--stats', action='store_true',
                       help='Show detailed statistics')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Validate files exist
    if not Path(args.warehouse_json).exists():
        print(f"Error: Warehouse file not found: {args.warehouse_json}")
        sys.exit(1)
    
    if not Path(args.picks_file).exists():
        print(f"Error: Picks file not found: {args.picks_file}")
        sys.exit(1)
    
    print("="*70)
    print("WAREHOUSE TSP SOLVER - ENHANCED WITH RACK INFERENCE")
    print("="*70)
    
    # Load warehouse data
    print(f"\nLoading warehouse: {args.warehouse_json}")
    locs = load_warehouse_data(args.warehouse_json)
    print(f"  Locations: {len(locs)}")
    
    # Load picks
    print(f"Loading picks: {args.picks_file}")
    picks = load_picks_file(args.picks_file)
    print(f"  Found {len(picks)} pick locations")
    
    # Validate picks
    invalid = [p for p in picks if p not in locs['id'].values]
    if invalid:
        print(f"⚠ Warning: Invalid picks (not in warehouse): {invalid}")
        picks = [p for p in picks if p in locs['id'].values]
        print(f"  Continuing with {len(picks)} valid picks")
    
    # Build enhanced graph with rack inference
    print("\nBuilding enhanced graph with rack inference...")
    locs = detect_aisles_with_dimensions(locs, x_tolerance=5, y_tolerance=5, min_aisle_size=3)
    edges = build_enhanced_graph(locs, max_intra_aisle_dist=args.max_dist, 
                                 max_cross_aisle_dist=args.max_dist, 
                                 min_clearance=1.0, verbose=False)
    G = create_graph_from_edges(locs, edges)
    
    # Analyze graph quality
    print("\n" + "-"*70)
    analyze_graph_quality(G, locs, verbose=True)
    print("-"*70)
    
    # Determine start/end
    start = args.start or find_default_start(locs)
    end = args.end or start
    
    print(f"\n  Start: {start}")
    print(f"  End: {end}")
    
    # Visualize graph only if requested
    if args.visualize in ['graph', 'both']:
        output = args.output or 'output/warehouse_graph.png'
        if args.visualize == 'both':
            output = output.replace('.png', '_graph.png')
        
        print(f"\nGenerating graph visualization...")
        visualize_graph_with_racks(locs, G, output_file=output, 
                                   title="Warehouse Graph with Detected Racks",
                                   display=not args.no_display)
    
    if args.visualize == 'graph':
        print("\nDone! (graph only, no TSP solving)")
        return
    
    # Solve TSP
    print(f"\nSolving TSP with {args.method} algorithm...")
    
    # Build route with start location
    route_to_optimize = [start] + picks
    if end != start:
        route_to_optimize.append(end)
    
    # Solve TSP
    if args.method == 'exhaustive' and len(picks) > 10:
        print(f"⚠ Warning: Exhaustive search for {len(picks)} picks may be slow!")
        print("  Falling back to 2-opt algorithm...")
        args.method = '2-opt'
    
    best_order = solve_tsp(G, route_to_optimize, cycle=False, method='christofides')
    
    if not best_order:
        print("Error: Could not find valid route")
        sys.exit(1)
    
    # Calculate distance
    total_distance = calculate_route_distance(G, best_order)
    
    # Extract pick order (exclude start/end waypoints)
    pick_order = [loc for loc in best_order if loc in picks]
    
    # Print results
    print("\n" + "="*70)
    print("SOLUTION")
    print("="*70)
    print(f"\nPick sequence: {' → '.join(pick_order)}")
    print(f"Total distance: {total_distance:.2f} units")
    print(f"Total waypoints: {len(best_order)} nodes")
    print(f"Number of picks: {len(pick_order)}")
    
    # Show statistics if requested
    if args.stats:
        print("\n" + "-"*70)
        print("DETAILED STATISTICS")
        print("-"*70)
        
        # Zone distribution
        zone_counts = {}
        for loc in pick_order:
            zone = locs[locs['id'] == loc].iloc[0]['zone']
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
        
        print("\nZone Distribution:")
        for zone, count in sorted(zone_counts.items()):
            print(f"  Zone {zone}: {count} picks")
        
        # Segment analysis
        print("\nRoute Segments:")
        for i in range(min(10, len(best_order) - 1)):  # Show first 10 segments
            from_loc = best_order[i]
            to_loc = best_order[i + 1]
            segment_dist = calculate_route_distance(G, [from_loc, to_loc])
            print(f"  {from_loc:15s} → {to_loc:15s}  {segment_dist:6.1f} units")
        
        if len(best_order) > 11:
            print(f"  ... ({len(best_order) - 11} more segments)")
    
    # Visualize route if requested
    if args.visualize in ['route', 'both']:
        output = args.output or 'output/warehouse_solution.png'
        if args.visualize == 'both':
            output = output.replace('.png', '_route.png')
        
        print(f"\nGenerating route visualization...")
        visualize_route_with_racks(locs, G, best_order, pick_order, start, end, 
                                   total_distance, output_file=output,
                                   display=not args.no_display)
    
    print("\n" + "="*70)
    print("DONE!")
    print("="*70)


if __name__ == '__main__':
    main()
