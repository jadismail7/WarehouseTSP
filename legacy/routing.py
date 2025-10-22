"""
Warehouse Routing Module

Handles pathfinding and TSP optimization for warehouse graphs.
Compatible with both legacy and enhanced graph construction.
"""

import networkx as nx
import networkx.algorithms.approximation as approx


def find_shortest_path(G, start, end):
    """
    Find the shortest path between two nodes.
    
    Args:
        G: NetworkX graph
        start: Starting node ID
        end: Ending node ID
    
    Returns:
        tuple: (path_list, path_length) or (None, None) if no path exists
    """
    if start not in G.nodes or end not in G.nodes:
        print(f"Node not found: {start if start not in G.nodes else end}")
        return None, None
    
    try:
        path = nx.shortest_path(G, start, end, weight='weight')
        path_length = nx.shortest_path_length(G, start, end, weight='weight')
        return path, path_length
    except nx.NetworkXNoPath:
        print(f"No path exists between {start} and {end}")
        return None, None


def solve_tsp(G, pick_locations, cycle=False, method='christofides'):
    """
    Solve the Traveling Salesman Problem for a set of pick locations.
    
    Args:
        G: NetworkX graph
        pick_locations: List of node IDs to visit
        cycle: If True, return to starting location (default: False for open path)
        method: 'christofides', 'greedy', or 'simulated_annealing'
    
    Returns:
        list: Ordered list of nodes (route) or None if cannot solve
    """
    # Filter to only include nodes that exist in the graph
    valid_picks = [p for p in pick_locations if p in G.nodes]
    
    if len(valid_picks) < 2:
        print(f"Not enough valid pick locations for TSP (need at least 2, got {len(valid_picks)})")
        return None
    
    if len(valid_picks) == 2:
        # For 2 nodes, just return them in order
        return valid_picks
    
    try:
        # Choose TSP method
        if method == 'christofides':
            tsp_method = approx.christofides
        elif method == 'greedy':
            tsp_method = approx.greedy_tsp
        elif method == 'simulated_annealing':
            tsp_method = approx.simulated_annealing_tsp
        else:
            tsp_method = approx.christofides
        
        # Solve TSP
        tsp_route = approx.traveling_salesman_problem(
            G, nodes=valid_picks, cycle=cycle, weight='weight', method=tsp_method
        )
        
        return tsp_route
    
    except Exception as e:
        print(f"TSP solving failed: {e}")
        return None


def calculate_route_distance(G, route):
    """
    Calculate total distance for a given route through the graph.
    
    Args:
        G: NetworkX graph
        route: List of node IDs in order
    
    Returns:
        float: Total distance, or None if route is invalid
    """
    if not route or len(route) < 2:
        return 0.0
    
    total_distance = 0
    
    for i in range(len(route) - 1):
        try:
            # Check if nodes are directly connected
            if G.has_edge(route[i], route[i+1]):
                total_distance += G[route[i]][route[i+1]]['weight']
            else:
                # Need to find shortest path between non-adjacent nodes
                path_len = nx.shortest_path_length(G, route[i], route[i+1], weight='weight')
                total_distance += path_len
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            print(f"Cannot find path between {route[i]} and {route[i+1]}")
            return None
    
    return total_distance


def get_full_route_with_paths(G, route):
    """
    Expand a high-level route into full paths between each waypoint.
    
    Args:
        G: NetworkX graph
        route: List of waypoint node IDs
    
    Returns:
        tuple: (full_path_list, segment_distances)
            full_path_list: Complete list of nodes including intermediate nodes
            segment_distances: List of distances for each segment
    """
    if not route or len(route) < 2:
        return route, []
    
    full_path = [route[0]]
    segment_distances = []
    
    for i in range(len(route) - 1):
        try:
            segment_path, segment_dist = find_shortest_path(G, route[i], route[i+1])
            
            if segment_path:
                # Add all nodes except the first (already in full_path)
                full_path.extend(segment_path[1:])
                segment_distances.append(segment_dist)
            else:
                print(f"Warning: No path found between {route[i]} and {route[i+1]}")
                return None, None
                
        except Exception as e:
            print(f"Error finding path: {e}")
            return None, None
    
    return full_path, segment_distances


def demonstrate_opposite_shelf_routing(G, locs):
    """
    Demonstrate that the graph properly prevents shortcuts through opposite shelf faces.
    
    Args:
        G: NetworkX graph
        locs: DataFrame with location data
    """
    print("\n" + "="*70)
    print("DEMONSTRATION: Opposite Shelf Routing")
    print("="*70)
    
    # Try to find examples of opposite shelf locations
    if 'aisle_pair' not in locs.columns:
        print("No aisle pair information available (not using legacy graph structure)")
        return
    
    paired_locs = locs[locs['aisle_pair'] >= 0]
    
    if len(paired_locs) == 0:
        print("No opposite shelf pairs detected in this warehouse")
        return
    
    # Find a pair on opposite sides
    for pair_id in paired_locs['aisle_pair'].unique():
        pair_nodes = paired_locs[paired_locs['aisle_pair'] == pair_id]
        left_nodes = pair_nodes[pair_nodes['aisle_side'] == 'left']['id'].tolist()
        right_nodes = pair_nodes[pair_nodes['aisle_side'] == 'right']['id'].tolist()
        
        if len(left_nodes) > 0 and len(right_nodes) > 0:
            # Pick example nodes
            left_node = left_nodes[0]
            right_node = right_nodes[0]
            
            print(f"\nTesting route between opposite shelves:")
            print(f"  Left side: {left_node}")
            print(f"  Right side: {right_node}")
            
            path, dist = find_shortest_path(G, left_node, right_node)
            
            if path:
                print(f"\nRoute requires {len(path)} nodes (distance: {dist:.2f})")
                print(f"  Path goes around the aisle (not through shelves)")
                if len(path) <= 10:
                    print(f"  Route: {' → '.join(path)}")
                else:
                    print(f"  Route: {' → '.join(path[:5])} ... {' → '.join(path[-3:])}")
            break


def analyze_picking_efficiency(G, pick_locations, start_location=None, end_location=None):
    """
    Analyze the efficiency of a picking route.
    
    Args:
        G: NetworkX graph
        pick_locations: List of locations to pick from
        start_location: Optional starting point (e.g., staging area)
        end_location: Optional ending point (e.g., packing station)
    
    Returns:
        dict with efficiency metrics
    """
    metrics = {}
    
    # Build complete route
    full_route = []
    if start_location:
        full_route.append(start_location)
    full_route.extend(pick_locations)
    if end_location:
        full_route.append(end_location)
    
    if len(full_route) < 2:
        return None
    
    # Calculate naive (sequential) distance
    naive_distance = calculate_route_distance(G, full_route)
    metrics['naive_distance'] = naive_distance
    metrics['naive_route'] = full_route
    
    # Calculate optimized TSP distance
    if len(pick_locations) >= 2:
        # For TSP with fixed endpoints, we need special handling
        if start_location or end_location:
            # Simple approach: optimize the middle picks
            optimized_picks = solve_tsp(G, pick_locations, cycle=False)
            if optimized_picks:
                optimized_route = []
                if start_location:
                    optimized_route.append(start_location)
                optimized_route.extend(optimized_picks)
                if end_location:
                    optimized_route.append(end_location)
                
                optimized_distance = calculate_route_distance(G, optimized_route)
                metrics['optimized_distance'] = optimized_distance
                metrics['optimized_route'] = optimized_route
        else:
            # No fixed endpoints, just optimize picks
            optimized_picks = solve_tsp(G, pick_locations, cycle=False)
            if optimized_picks:
                optimized_distance = calculate_route_distance(G, optimized_picks)
                metrics['optimized_distance'] = optimized_distance
                metrics['optimized_route'] = optimized_picks
    
    # Calculate improvement
    if 'optimized_distance' in metrics and metrics['naive_distance']:
        improvement = (metrics['naive_distance'] - metrics['optimized_distance']) / metrics['naive_distance']
        metrics['improvement_percent'] = improvement * 100
    
    return metrics
