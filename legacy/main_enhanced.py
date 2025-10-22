"""
Enhanced Warehouse TSP - Main Application

Uses physical properties (width, depth, traversable) for improved graph construction:
1. Automatically infers rack structures from bin dimensions
2. Respects non-traversable obstacles (offices, packing stations, etc.)
3. Checks line-of-sight to prevent paths through obstacles
4. Better aisle detection using physical dimensions

Key Features:
- Automatic rack inference from picking location (bin) clustering
- Obstacle avoidance using traversability flags
- Clearance calculations based on physical dimensions
- No need to manually specify rack information
- More accurate pathfinding that respects warehouse layout

Usage:
    python main_enhanced.py [--data warehouse_locations_large.json] [--output enhanced_graph.png]
"""

import json
import pandas as pd
import networkx as nx
import argparse

from warehouse_graph_enhanced import (
    detect_aisles_with_dimensions, 
    build_enhanced_graph, 
    create_graph_from_edges,
    analyze_graph_quality
)
from visualization import visualize_warehouse_graph, print_graph_summary
from routing import find_shortest_path, solve_tsp


def load_warehouse_data(filename="data/warehouse_locations_large.json"):
    """
    Load warehouse location data from JSON file.
    Expects locations to have: id, x, y, type, zone, width, depth, traversable
    """
    with open(filename) as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Verify required columns
    required_cols = ['id', 'x', 'y', 'type', 'zone', 'width', 'depth', 'traversable']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return df


def main(data_file="data/warehouse_locations_large.json", output_file=None, verbose=True, show_demo=True):
    """
    Main application workflow with enhanced graph construction.
    
    Args:
        data_file: Path to warehouse JSON data file
        output_file: Path to save visualization (None = display only)
        verbose: Show detailed progress messages
        show_demo: Run demonstration examples
    """
    
    print("="*70)
    print("ENHANCED WAREHOUSE TSP - Physical Layout Aware")
    print("="*70 + "\n")
    
    # Load warehouse data
    if verbose:
        print(f"Loading warehouse data from: {data_file}")
    locs = load_warehouse_data(data_file)
    
    if verbose:
        print(f"Loaded {len(locs)} locations")
        print(f"  - Traversable: {sum(locs['traversable'])}")
        print(f"  - Obstacles: {sum(~locs['traversable'])}")
        print()
    
    # Detect aisle structures with physical dimensions
    if verbose:
        print("Detecting aisle structures and inferring racks...")
    locs = detect_aisles_with_dimensions(locs, x_tolerance=5, y_tolerance=5, min_aisle_size=3)
    
    num_v_aisles = len(set(locs['v_aisle']) - {-1})
    num_h_aisles = len(set(locs['h_aisle']) - {-1})
    num_racks = len(set(locs['rack_id']) - {-1})
    
    if verbose:
        print(f"  - Vertical aisles: {num_v_aisles}")
        print(f"  - Horizontal aisles: {num_h_aisles}")
        if num_racks > 0:
            print(f"  - Inferred racks from bins: {num_racks}")
        print()
    
    # Build enhanced warehouse graph
    if verbose:
        print("Building enhanced warehouse graph...")
    edges = build_enhanced_graph(
        locs, 
        max_intra_aisle_dist=25,  # Slightly larger for large warehouse
        max_cross_aisle_dist=20,
        min_clearance=1.0,  # Minimum clearance from obstacles
        verbose=verbose
    )
    
    print()
    
    # Create NetworkX graph
    G = create_graph_from_edges(locs, edges)
    
    # Analyze graph quality
    metrics = analyze_graph_quality(G, locs, verbose=verbose)
    
    # Print summary
    if verbose:
        print_graph_summary(G)
    
    # Visualize the graph
    viz_title = "Enhanced Warehouse Graph (Physical Layout Aware)"
    visualize_warehouse_graph(G, locs, title=viz_title)
    
    if show_demo and metrics['is_connected']:
        # Example: Shortest path
        print("\n" + "="*70)
        print("EXAMPLE: Shortest Path Routing")
        print("="*70)
        
        # Find some traversable locations to route between
        traversable_locs = locs[locs['traversable'] == True]
        
        if len(traversable_locs) >= 2:
            # Try routing from a dock/staging to a picking location
            start_candidates = traversable_locs[traversable_locs['type'].isin(['dock', 'staging'])]
            pick_candidates = traversable_locs[traversable_locs['type'] == 'picking']
            
            if len(start_candidates) > 0 and len(pick_candidates) > 0:
                start = start_candidates.iloc[0]['id']
                end = pick_candidates.iloc[0]['id']
                
                path, path_length = find_shortest_path(G, start, end)
                if path:
                    print(f"\n{start} → {end}: {path_length:.2f} units")
                    print(f"  via: {' → '.join(path[:10])}", end="")
                    if len(path) > 10:
                        print(f" ... ({len(path)} total nodes)")
                    else:
                        print()
        
        # Example: TSP optimization
        print("\n" + "="*70)
        print("EXAMPLE: TSP Optimization")
        print("="*70)
        
        # Get some sample picks from the test file if available
        try:
            with open('data/picks_large_test.txt', 'r') as f:
                picks = [line.strip() for line in f if line.strip()]
            
            # Take first 10 picks for demo
            demo_picks = picks[:10]
            
            # Verify picks are in graph
            demo_picks = [p for p in demo_picks if p in G.nodes()]
            
            if len(demo_picks) >= 3:
                print(f"\nOptimizing route for {len(demo_picks)} picks:")
                print(f"  {', '.join(demo_picks)}")
                
                tsp_route = solve_tsp(G, demo_picks, cycle=False)
                if tsp_route:
                    total_dist = 0
                    for i in range(len(tsp_route) - 1):
                        path, dist = find_shortest_path(G, tsp_route[i], tsp_route[i+1])
                        total_dist += dist
                    
                    print(f"\nOptimized order: {' → '.join(tsp_route)}")
                    print(f"Total distance: {total_dist:.2f} units")
        except FileNotFoundError:
            print("\n(Skipping TSP demo - picks_large_test.txt not found)")
    
    elif not metrics['is_connected']:
        print("\n⚠️  WARNING: Graph is not fully connected!")
        print("   Some locations may be unreachable. Consider adjusting parameters.")
    
    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)
    
    return G, locs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enhanced Warehouse TSP with Physical Layout')
    parser.add_argument('--data', default='data/warehouse_locations_large.json',
                       help='Path to warehouse data JSON file')
    parser.add_argument('--output', default=None,
                       help='Path to save graph visualization (default: display only)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress verbose output')
    parser.add_argument('--no-demo', action='store_true',
                       help='Skip demonstration examples')
    
    args = parser.parse_args()
    
    main(
        data_file=args.data,
        output_file=args.output,
        verbose=not args.quiet,
        show_demo=not args.no_demo
    )
