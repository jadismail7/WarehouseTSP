"""
Warehouse TSP - Main Application

Automatic warehouse graph construction with intelligent aisle detection,
opposite shelf routing, and TSP optimization.

This is the main entry point that orchestrates the various modules:
- warehouse_graph: Core graph building and aisle detection
- visualization: Graph visualization with edge type highlighting
- routing: Pathfinding and TSP optimization

Key Features:
1. DBSCAN clustering to detect vertical and horizontal aisles
2. Connects nodes within the same aisle sequentially
3. Finds cross-aisle connections ONLY at true intersection points (avoids mid-aisle shortcuts)
4. **Detects opposite shelf faces and prevents walking through shelves**
5. Allows connections at aisle ends where you can go around
6. Ensures full connectivity across all warehouse zones
7. Works with any coordinate-based warehouse data

Parameters to tune:
- x_tolerance/y_tolerance: Clustering sensitivity for aisle detection (default: 3)
- min_aisle_size: Minimum nodes to form a true aisle (default: 3)
- max_intra_aisle_dist: Maximum distance between sequential aisle nodes (default: 20)
- max_cross_aisle_dist: Maximum distance for cross-aisle connections (default: 15)
- only_connect_intersections: True = only connect at intersections (prevents mid-aisle shortcuts)
- prevent_cross_aisle_shortcuts: True = prevents walking through opposite shelf faces
"""

import json
import pandas as pd
import networkx as nx

from warehouse_graph import detect_aisles, build_aisle_graph, create_graph_from_edges
from visualization import visualize_warehouse_graph, print_graph_summary, print_edge_summary
from routing import find_shortest_path, solve_tsp, demonstrate_opposite_shelf_routing


def load_warehouse_data(filename="warehouse_locations.json"):
    """Load warehouse location data from JSON file."""
    with open(filename) as f:
        return pd.DataFrame(json.load(f))


def main(verbose=True, show_demo=True):
    """
    Main application workflow.
    
    Args:
        verbose: If True, show detailed progress messages
        show_demo: If True, run demonstration examples
    """
    
    # Load warehouse data
    locs = load_warehouse_data()
    
    # Detect aisle structures
    if verbose:
        print("Detecting aisle structures...")
    locs = detect_aisles(locs, x_tolerance=3, y_tolerance=3, min_aisle_size=3)
    
    num_v_aisles = len(set(locs['v_aisle']) - {-1})
    num_h_aisles = len(set(locs['h_aisle']) - {-1})
    if verbose:
        print(f"Found {num_v_aisles} vertical aisles, {num_h_aisles} horizontal aisles")
    
    # Build warehouse graph
    if verbose:
        print("Building warehouse graph...")
    edges = build_aisle_graph(
        locs, 
        max_intra_aisle_dist=20, 
        max_cross_aisle_dist=15,
        only_connect_intersections=True,  # Set to False to allow mid-aisle connections
        prevent_cross_aisle_shortcuts=True,  # Set to False to allow walking through shelves
        verbose=verbose
    )
    
    # Create NetworkX graph
    G = create_graph_from_edges(locs, edges)
    
    # Print summaries
    if verbose:
        print_graph_summary(G)
        print_edge_summary(G)
    
    # Visualize the graph
    visualize_warehouse_graph(G, locs, title="Auto-Detected Warehouse Aisle Structure")
    
    if show_demo:
        # Example: Shortest path
        print("\n" + "="*70)
        print("EXAMPLE: Shortest Path Routing")
        print("="*70)
        
        path, path_length = find_shortest_path(G, 'Dock_Receiving', 'B1-1')
        if path:
            print(f"Dock_Receiving → B1-1: {path_length:.2f} units")
            print(f"  via: {' → '.join(path)}")
        
        # Example: TSP optimization
        print("\n" + "="*70)
        print("EXAMPLE: TSP Optimization")
        print("="*70)
        
        picks = ['A1-1', 'A2-2', 'C1-1', 'B1-2']
        tsp_route = solve_tsp(G, picks, cycle=False)
        if tsp_route:
            print(f"Optimized pick route: {' → '.join(tsp_route)}")
        
        # Demonstrate opposite shelf routing
        demonstrate_opposite_shelf_routing(G, locs)
    
    return G, locs


if __name__ == "__main__":
    main()
