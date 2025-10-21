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

from physical.physical_layout import load_physical_warehouse
from physical.routing import solve_tsp_with_endpoints

from cli_utils import (
    detect_warehouse_format,
    load_picks_file,
    load_warehouse_legacy,
    find_default_start_end,
    find_default_start_end_legacy
)
from cli_stats import print_statistics, print_statistics_legacy
from cli_visualize import (
    visualize_graph_only,
    visualize_graph_only_legacy,
    visualize_route,
    visualize_route_legacy
)


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
    print("WAREHOUSE TSP SOLVER")
    print("="*70)
    
    # Detect warehouse format
    warehouse_format = detect_warehouse_format(args.warehouse_json)
    print(f"\nDetected format: {warehouse_format}")
    
    # Load warehouse based on format
    print(f"Loading warehouse: {args.warehouse_json}")
    
    if warehouse_format == 'legacy':
        print("⚠️  Using legacy coordinate-based system")
        graph, warehouse = load_warehouse_legacy(args.warehouse_json, args.max_dist)
    else:
        graph, warehouse = load_physical_warehouse(args.warehouse_json)
        
        # Rebuild with custom max distance if specified
        if args.max_dist != 30.0:
            print(f"Rebuilding graph with max_connection_dist={args.max_dist}")
            graph = warehouse.build_graph(max_connection_dist=args.max_dist)
    
    # Load picks
    print(f"Loading picks: {args.picks_file}")
    picks = load_picks_file(args.picks_file)
    print(f"  Found {len(picks)} pick locations")
    
    # Determine start/end based on format
    if warehouse_format == 'legacy':
        start = args.start or find_default_start_end_legacy(graph)
        end = args.end or start
    else:
        start = args.start or find_default_start_end(warehouse)
        end = args.end or start
    
    if not start:
        print("Error: Could not determine start location")
        sys.exit(1)
    
    print(f"  Start: {start}")
    print(f"  End: {end}")
    
    # Visualize graph only if requested
    if args.visualize in ['graph', 'both']:
        output = args.output or 'output/warehouse_graph.png'
        if args.visualize == 'both':
            output = output.replace('.png', '_graph.png')
        
        if warehouse_format == 'legacy':
            visualize_graph_only_legacy(graph, output, display=not args.no_display)
        else:
            visualize_graph_only(warehouse, graph, output, display=not args.no_display)
    
    if args.visualize == 'graph':
        print("\nDone! (graph only, no TSP solving)")
        return
    
    # Solve TSP
    print(f"\nSolving TSP with {args.method} algorithm...")
    route, total_distance, pick_order = solve_tsp_with_endpoints(
        graph, start, picks, end, method=args.method
    )
    
    if not route:
        print("Error: Could not find valid route")
        sys.exit(1)
    
    # Print results
    print("\n" + "="*70)
    print("SOLUTION")
    print("="*70)
    print(f"\nPick sequence: {' → '.join(pick_order)}")
    print(f"Total distance: {total_distance:.2f} units")
    print(f"Total waypoints: {len(route)} nodes")
    
    # Show statistics if requested
    if args.stats:
        if warehouse_format == 'legacy':
            print_statistics_legacy(graph, route, total_distance, pick_order, start, end)
        else:
            print_statistics(graph, warehouse, route, total_distance, pick_order, start, end)
    
    # Visualize route if requested
    if args.visualize in ['route', 'both']:
        output = args.output or 'output/warehouse_solution.png'
        if args.visualize == 'both':
            output = output.replace('.png', '_route.png')
        
        if warehouse_format == 'legacy':
            visualize_route_legacy(graph, route, pick_order, start, end,
                                  total_distance, output, display=not args.no_display)
        else:
            visualize_route(warehouse, graph, route, pick_order, start, end, 
                           total_distance, output, display=not args.no_display)
    
    print("\n" + "="*70)
    print("DONE!")
    print("="*70)


if __name__ == '__main__':
    main()
