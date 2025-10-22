"""
Compare Legacy vs Enhanced Graph Construction

This script compares the original graph construction approach with the
enhanced approach that uses physical properties (width, depth, traversable).

Key Improvements in Enhanced Approach:
1. Automatic rack inference from bin locations
2. Obstacle avoidance using traversability
3. Physical dimension-aware path blocking
4. Better aisle detection
"""

import json
import pandas as pd
import time

# Import both approaches
from warehouse_graph import detect_aisles, build_aisle_graph, create_graph_from_edges as create_legacy_graph
from warehouse_graph_enhanced import (
    detect_aisles_with_dimensions, 
    build_enhanced_graph, 
    create_graph_from_edges as create_enhanced_graph,
    analyze_graph_quality
)
from routing import solve_tsp, calculate_route_distance


def load_warehouse_data(filename="data/warehouse_locations_large.json"):
    """Load warehouse data"""
    with open(filename) as f:
        return pd.DataFrame(json.load(f))


def compare_approaches(data_file="data/warehouse_locations_large.json"):
    """
    Compare legacy and enhanced graph construction approaches.
    """
    print("="*80)
    print("COMPARISON: Legacy vs Enhanced Graph Construction")
    print("="*80)
    print()
    
    # Load data
    print(f"Loading data from: {data_file}")
    locs = load_warehouse_data(data_file)
    print(f"  Loaded {len(locs)} locations\n")
    
    # ===== LEGACY APPROACH =====
    print("-"*80)
    print("LEGACY APPROACH (Original)")
    print("-"*80)
    
    start_time = time.time()
    
    # Legacy doesn't use physical properties
    locs_legacy = locs.copy()
    locs_legacy = detect_aisles(locs_legacy, x_tolerance=3, y_tolerance=3, min_aisle_size=3)
    
    edges_legacy = build_aisle_graph(
        locs_legacy,
        max_intra_aisle_dist=25,
        max_cross_aisle_dist=20,
        ensure_connectivity=True,
        only_connect_intersections=True,
        prevent_cross_aisle_shortcuts=True,
        verbose=False
    )
    
    G_legacy = create_legacy_graph(locs_legacy, edges_legacy)
    legacy_time = time.time() - start_time
    
    print(f"  Nodes: {G_legacy.number_of_nodes()}")
    print(f"  Edges: {G_legacy.number_of_edges()}")
    print(f"  Avg degree: {2*G_legacy.number_of_edges()/G_legacy.number_of_nodes():.2f}")
    print(f"  Build time: {legacy_time:.3f}s")
    print()
    
    # ===== ENHANCED APPROACH =====
    print("-"*80)
    print("ENHANCED APPROACH (Physical Properties Aware)")
    print("-"*80)
    
    start_time = time.time()
    
    locs_enhanced = locs.copy()
    locs_enhanced = detect_aisles_with_dimensions(locs_enhanced, x_tolerance=5, y_tolerance=5, min_aisle_size=3)
    
    edges_enhanced = build_enhanced_graph(
        locs_enhanced,
        max_intra_aisle_dist=25,
        max_cross_aisle_dist=20,
        min_clearance=1.0,
        verbose=False
    )
    
    G_enhanced = create_enhanced_graph(locs_enhanced, edges_enhanced)
    enhanced_time = time.time() - start_time
    
    # Analyze quality
    metrics = analyze_graph_quality(G_enhanced, locs_enhanced, verbose=False)
    
    print(f"  Nodes: {metrics['num_nodes']} ({metrics['traversable_nodes']} traversable, {metrics['obstacle_nodes']} obstacles)")
    print(f"  Edges: {metrics['num_edges']}")
    print(f"  Avg degree: {metrics['avg_degree']:.2f}")
    print(f"  Inferred racks: {metrics['num_racks']}")
    print(f"  Build time: {enhanced_time:.3f}s")
    print()
    
    # ===== COMPARISON SUMMARY =====
    print("="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    
    print("\nGraph Structure:")
    print(f"  Legacy nodes:      {G_legacy.number_of_nodes()}")
    print(f"  Enhanced nodes:    {G_enhanced.number_of_nodes()}")
    print(f"  Difference:        {G_enhanced.number_of_nodes() - G_legacy.number_of_nodes()}")
    
    print(f"\n  Legacy edges:      {G_legacy.number_of_edges()}")
    print(f"  Enhanced edges:    {G_enhanced.number_of_edges()}")
    print(f"  Difference:        {G_enhanced.number_of_edges() - G_legacy.number_of_edges()}")
    
    print("\nKey Improvements in Enhanced Approach:")
    print("  ✓ Automatically infers rack structures from bins")
    print(f"    → Detected {metrics['num_racks']} racks without manual specification")
    print("  ✓ Respects non-traversable obstacles")
    print(f"    → {metrics['obstacle_nodes']} obstacles excluded from routing")
    print("  ✓ Checks physical line-of-sight for connections")
    print("    → Prevents paths through walls/racks")
    print("  ✓ Uses physical dimensions for clearance")
    print("    → More accurate distance calculations")
    
    # Test routing on both graphs
    print("\n" + "="*80)
    print("ROUTING COMPARISON")
    print("="*80)
    
    # Try to load picks for testing
    try:
        with open('data/picks_large_test.txt', 'r') as f:
            test_picks = [line.strip() for line in f if line.strip()][:10]
        
        # Filter picks that exist in both graphs
        valid_picks_legacy = [p for p in test_picks if p in G_legacy.nodes()]
        valid_picks_enhanced = [p for p in test_picks if p in G_enhanced.nodes()]
        
        print(f"\nTesting TSP with {len(test_picks)} picks...")
        print(f"  Valid in legacy graph:   {len(valid_picks_legacy)}")
        print(f"  Valid in enhanced graph: {len(valid_picks_enhanced)}")
        
        if len(valid_picks_legacy) >= 3 and len(valid_picks_enhanced) >= 3:
            # Use common picks
            common_picks = [p for p in valid_picks_legacy if p in valid_picks_enhanced][:5]
            
            print(f"\nOptimizing route for {len(common_picks)} common picks:")
            print(f"  {', '.join(common_picks)}")
            
            # Legacy TSP
            route_legacy = solve_tsp(G_legacy, common_picks, cycle=False)
            if route_legacy:
                dist_legacy = calculate_route_distance(G_legacy, route_legacy)
                print(f"\n  Legacy route distance:   {dist_legacy:.2f} units")
            
            # Enhanced TSP
            route_enhanced = solve_tsp(G_enhanced, common_picks, cycle=False)
            if route_enhanced:
                dist_enhanced = calculate_route_distance(G_enhanced, route_enhanced)
                print(f"  Enhanced route distance: {dist_enhanced:.2f} units")
                
                if dist_legacy and dist_enhanced:
                    diff = dist_legacy - dist_enhanced
                    pct = (diff / dist_legacy) * 100
                    print(f"  Difference:              {diff:.2f} units ({pct:+.1f}%)")
    
    except FileNotFoundError:
        print("\n(Skipping routing test - picks_large_test.txt not found)")
    
    print("\n" + "="*80)
    print("Comparison complete!")
    print("="*80)
    
    return {
        'legacy': G_legacy,
        'enhanced': G_enhanced,
        'metrics': metrics
    }


if __name__ == "__main__":
    import sys
    
    data_file = sys.argv[1] if len(sys.argv) > 1 else "data/warehouse_locations_large.json"
    compare_approaches(data_file)
