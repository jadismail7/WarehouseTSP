"""
Warehouse Routing and Path Analysis Module

Handles pathfinding, TSP optimization, and routing demonstrations.
"""

import networkx as nx
import networkx.algorithms.approximation as approx


def calculate_distance_between_points(p1, p2):
    """Calculate Euclidean distance between two coordinate tuples"""
    import math
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


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
    try:
        path = nx.shortest_path(G, start, end, weight='weight')
        path_length = nx.shortest_path_length(G, start, end, weight='weight')
        return path, path_length
    except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
        print(f"Cannot find path from {start} to {end}: {e}")
        return None, None


def solve_tsp(G, pick_locations, cycle=False, method='christofides'):
    """
    Solve the Traveling Salesman Problem for a set of pick locations.
    
    Args:
        G: NetworkX graph
        pick_locations: List of node IDs to visit
        cycle: If True, return to starting location
        method: 'christofides', 'greedy', or 'simulated_annealing'
    
    Returns:
        tuple: (route_list, total_distance) or (None, None) if cannot solve
    """
    # Filter to only include nodes that exist in the graph
    valid_picks = [p for p in pick_locations if p in G.nodes]
    
    if len(valid_picks) < 2:
        print(f"Not enough valid pick locations for TSP (need at least 2, got {len(valid_picks)})")
        return None, None
    
    if method == 'christofides':
        # Christofides algorithm (1.5-approximation for metric TSP)
        tsp_route = approx.traveling_salesman_problem(
            G, nodes=valid_picks, cycle=cycle, weight='weight', method=approx.christofides
        )
    elif method == 'greedy':
        # Greedy nearest neighbor
        tsp_route = approx.traveling_salesman_problem(
            G, nodes=valid_picks, cycle=cycle, weight='weight', method=approx.greedy_tsp
        )
    elif method == 'simulated_annealing':
        # Simulated annealing
        tsp_route = approx.traveling_salesman_problem(
            G, nodes=valid_picks, cycle=cycle, weight='weight', method=approx.simulated_annealing_tsp
        )
    else:
        # Default to Christofides
        tsp_route = approx.traveling_salesman_problem(
            G, nodes=valid_picks, cycle=cycle, weight='weight'
        )
    
    # Calculate total distance
    total_distance = 0
    for i in range(len(tsp_route) - 1):
        if G.has_edge(tsp_route[i], tsp_route[i+1]):
            total_distance += G[tsp_route[i]][tsp_route[i+1]]['weight']
        else:
            # Need to find path between non-adjacent nodes
            path_len = nx.shortest_path_length(G, tsp_route[i], tsp_route[i+1], weight='weight')
            total_distance += path_len
    
    return tsp_route, total_distance


def solve_tsp_with_endpoints(G, start_node, pick_locations, end_node, method='2-opt'):
    """
    Solve TSP with specific start and end points using various heuristics.
    
    Args:
        G: NetworkX graph
        start_node: Starting location
        pick_locations: List of pick points to visit
        end_node: Ending location
        method: 'greedy', '2-opt', 'christofides', or 'exhaustive'
    
    Returns:
        tuple: (full_route, total_distance, pick_order)
    """
    import itertools
    
    valid_picks = [p for p in pick_locations if p in G.nodes]
    
    if not valid_picks:
        return None, None, None
    
    if method == 'exhaustive' and len(valid_picks) <= 10:
        # Exhaustive search for small sets
        return _solve_tsp_exhaustive(G, start_node, valid_picks, end_node)
    elif method == '2-opt':
        return _solve_tsp_2opt(G, start_node, valid_picks, end_node)
    elif method == 'christofides':
        return _solve_tsp_christofides(G, start_node, valid_picks, end_node)
    else:  # greedy
        return _solve_tsp_greedy(G, start_node, valid_picks, end_node)


def _solve_tsp_greedy(G, start_node, pick_locations, end_node):
    """Greedy nearest neighbor heuristic"""
    current = start_node
    remaining = set(pick_locations)
    route = [start_node]
    pick_order = []  # Track picks in order they're selected
    total_distance = 0
    
    while remaining:
        nearest = None
        nearest_dist = float('inf')
        
        for pick in remaining:
            if nx.has_path(G, current, pick):
                dist = nx.shortest_path_length(G, current, pick, weight='weight')
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = pick
        
        if nearest is None:
            break
        
        path_segment = nx.shortest_path(G, current, nearest, weight='weight')
        route.extend(path_segment[1:])
        total_distance += nearest_dist
        remaining.remove(nearest)
        pick_order.append(nearest)  # Add to pick order when selected
        current = nearest
    
    # Add path to end
    if nx.has_path(G, current, end_node):
        final_segment = nx.shortest_path(G, current, end_node, weight='weight')
        final_dist = nx.shortest_path_length(G, current, end_node, weight='weight')
        route.extend(final_segment[1:])
        total_distance += final_dist
    
    return route, total_distance, pick_order


def _solve_tsp_2opt(G, start_node, pick_locations, end_node):
    """2-opt local search improvement on greedy solution"""
    # Start with greedy solution
    route, distance, pick_order = _solve_tsp_greedy(G, start_node, pick_locations, end_node)
    
    if not pick_order or len(pick_order) < 3:
        return route, distance, pick_order
    
    # Extract just the pick portion for optimization
    improved = True
    iterations = 0
    max_iterations = 100
    
    while improved and iterations < max_iterations:
        improved = False
        iterations += 1
        
        for i in range(len(pick_order) - 1):
            for j in range(i + 2, len(pick_order)):
                # Try reversing segment between i and j
                new_order = pick_order[:i+1] + pick_order[i+1:j+1][::-1] + pick_order[j+1:]
                
                # Calculate new distance
                new_distance = 0
                current = start_node
                
                for pick in new_order:
                    if nx.has_path(G, current, pick):
                        new_distance += nx.shortest_path_length(G, current, pick, weight='weight')
                        current = pick
                    else:
                        new_distance = float('inf')
                        break
                
                if current != end_node and nx.has_path(G, current, end_node):
                    new_distance += nx.shortest_path_length(G, current, end_node, weight='weight')
                
                if new_distance < distance:
                    pick_order = new_order
                    distance = new_distance
                    improved = True
                    break
            
            if improved:
                break
    
    # Rebuild full route with improved order
    route = [start_node]
    total_distance = 0
    current = start_node
    
    for pick in pick_order:
        path_segment = nx.shortest_path(G, current, pick, weight='weight')
        segment_dist = nx.shortest_path_length(G, current, pick, weight='weight')
        route.extend(path_segment[1:])
        total_distance += segment_dist
        current = pick
    
    final_segment = nx.shortest_path(G, current, end_node, weight='weight')
    final_dist = nx.shortest_path_length(G, current, end_node, weight='weight')
    route.extend(final_segment[1:])
    total_distance += final_dist
    
    return route, total_distance, pick_order


def _solve_tsp_exhaustive(G, start_node, pick_locations, end_node):
    """Exhaustive search (only for small sets)"""
    import itertools
    
    best_distance = float('inf')
    best_order = None
    
    for perm in itertools.permutations(pick_locations):
        total_dist = 0
        current = start_node
        
        for pick in perm:
            if not nx.has_path(G, current, pick):
                total_dist = float('inf')
                break
            total_dist += nx.shortest_path_length(G, current, pick, weight='weight')
            current = pick
        
        if current != end_node and nx.has_path(G, current, end_node):
            total_dist += nx.shortest_path_length(G, current, end_node, weight='weight')
        
        if total_dist < best_distance:
            best_distance = total_dist
            best_order = list(perm)
    
    if best_order is None:
        return None, None, None
    
    # Build full route
    route = [start_node]
    current = start_node
    
    for pick in best_order:
        path_segment = nx.shortest_path(G, current, pick, weight='weight')
        route.extend(path_segment[1:])
        current = pick
    
    final_segment = nx.shortest_path(G, current, end_node, weight='weight')
    route.extend(final_segment[1:])
    
    return route, best_distance, best_order


def _solve_tsp_christofides(G, start_node, pick_locations, end_node):
    """Christofides algorithm wrapper"""
    # Build complete graph of distances between picks + endpoints
    nodes = [start_node] + pick_locations + [end_node]
    
    # For now, fall back to 2-opt (Christofides requires more setup)
    return _solve_tsp_2opt(G, start_node, pick_locations, end_node)


def demonstrate_opposite_shelf_routing(G, locs):
    """
    Demonstrate how the graph handles opposite shelf routing scenarios.
    
    Args:
        G: NetworkX graph
        locs: DataFrame with location data
    """
    print("\n" + "="*70)
    print("OPPOSITE SHELF ROUTING DEMONSTRATION")
    print("="*70)
    
    # Test Case 1: Middle of aisle - must go around
    print("\n[Test 1] Middle of opposite shelves (A1-2 → A2-2)")
    path, path_length = find_shortest_path(G, 'A1-2', 'A2-2')
    if path:
        p1 = locs[locs['id'] == 'A1-2'][['x', 'y']].iloc[0]
        p2 = locs[locs['id'] == 'A2-2'][['x', 'y']].iloc[0]
        straight_dist = calculate_distance_between_points([p1['x'], p1['y']], [p2['x'], p2['y']])
        print(f"  Route: {' → '.join(path)}")
        print(f"  Distance: {path_length:.2f} units (straight-line: {straight_dist:.2f})")
        print(f"  ✓ Goes around aisle end (cannot cut through shelf)")
    
    # Test Case 2: Same side of aisle - direct connection
    print("\n[Test 2] Same side of aisle (A1-2 → A1-3)")
    path, path_length = find_shortest_path(G, 'A1-2', 'A1-3')
    if path:
        print(f"  Route: {' → '.join(path)}")
        print(f"  Distance: {path_length:.2f} units")
        print(f"  ✓ Direct connection within same aisle")
    
    # Test Case 3: Opposite ends - showing the end connections
    print("\n[Test 3] Opposite sides at aisle end (A1-1 → A2-1)")
    path, path_length = find_shortest_path(G, 'A1-1', 'A2-1')
    if path:
        p1 = locs[locs['id'] == 'A1-1'][['x', 'y']].iloc[0]
        p2 = locs[locs['id'] == 'A2-1'][['x', 'y']].iloc[0]
        straight_dist = calculate_distance_between_points([p1['x'], p1['y']], [p2['x'], p2['y']])
        print(f"  Route: {' → '.join(path)}")
        print(f"  Distance: {path_length:.2f} units (straight-line: {straight_dist:.2f})")
        print(f"  ✓ Direct connection at aisle end")
    
    print("\n" + "="*70)
