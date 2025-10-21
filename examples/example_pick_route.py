"""
Example: Pick Route with Start and End Points

Demonstrates a realistic warehouse workflow:
1. Start at Staging Area
2. Pick items from various racks
3. End at Charging Station
"""

import networkx as nx
from physical_layout import load_physical_warehouse
from physical_visualization import visualize_physical_warehouse, print_physical_warehouse_summary
from routing import find_shortest_path


def solve_pick_route_with_endpoints(graph, start_node, pick_locations, end_node):
    """
    Solve a pick route that starts at one location, visits picks, and ends at another.
    
    Args:
        graph: NetworkX graph
        start_node: Starting location (e.g., staging area)
        pick_locations: List of pick points to visit
        end_node: Ending location (e.g., charging station)
    
    Returns:
        tuple: (full_route, total_distance, pick_order)
    """
    import itertools
    
    # Filter to only picks that exist in the graph
    valid_picks = [p for p in pick_locations if p in graph.nodes]
    
    if not valid_picks:
        print("No valid pick locations found!")
        return None, None, None
    
    print(f"\nOptimizing route for {len(valid_picks)} picks...")
    print(f"Start: {start_node}")
    print(f"Picks: {valid_picks}")
    print(f"End: {end_node}")
    
    # For small number of picks, try all permutations
    # For larger sets, use greedy nearest neighbor
    if len(valid_picks) <= 8:
        print(f"  Using exhaustive search (trying all {len(list(itertools.permutations(valid_picks)))} permutations)...")
        best_distance = float('inf')
        best_order = None
        
        for perm in itertools.permutations(valid_picks):
            # Calculate distance for this permutation
            try:
                total_dist = 0
                
                # Start to first pick
                dist = nx.shortest_path_length(graph, start_node, perm[0], weight='weight')
                total_dist += dist
                
                # Between picks
                for i in range(len(perm) - 1):
                    dist = nx.shortest_path_length(graph, perm[i], perm[i+1], weight='weight')
                    total_dist += dist
                
                # Last pick to end
                dist = nx.shortest_path_length(graph, perm[-1], end_node, weight='weight')
                total_dist += dist
                
                if total_dist < best_distance:
                    best_distance = total_dist
                    best_order = perm
            except nx.NetworkXNoPath:
                continue
        
        if best_order is None:
            print("  Could not find valid route!")
            return None, None, None
        
        print(f"  Found optimal route with distance: {best_distance:.2f}")
        
    else:
        # Greedy nearest neighbor for larger sets
        print(f"  Using greedy nearest neighbor heuristic...")
        remaining = set(valid_picks)
        current = start_node
        order = []
        
        while remaining:
            # Find nearest unvisited pick
            nearest = None
            nearest_dist = float('inf')
            
            for pick in remaining:
                try:
                    dist = nx.shortest_path_length(graph, current, pick, weight='weight')
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest = pick
                except nx.NetworkXNoPath:
                    continue
            
            if nearest is None:
                print(f"  Could not reach remaining picks: {remaining}")
                break
            
            order.append(nearest)
            remaining.remove(nearest)
            current = nearest
        
        best_order = tuple(order)
        
        # Calculate total distance
        total_dist = 0
        current = start_node
        for pick in best_order:
            total_dist += nx.shortest_path_length(graph, current, pick, weight='weight')
            current = pick
        total_dist += nx.shortest_path_length(graph, current, end_node, weight='weight')
        best_distance = total_dist
        
        print(f"  Greedy solution distance: {best_distance:.2f}")
    
    # Build the full route with waypoints
    full_route = [start_node]
    current = start_node
    
    for pick in best_order:
        path = nx.shortest_path(graph, current, pick, weight='weight')
        full_route.extend(path[1:])  # Skip first node (already in route)
        current = pick
    
    # Add path to end
    path = nx.shortest_path(graph, current, end_node, weight='weight')
    full_route.extend(path[1:])
    
    return full_route, best_distance, best_order


def main():
    print("="*70)
    print("WAREHOUSE PICK ROUTE OPTIMIZATION")
    print("="*70)
    
    # Load warehouse
    print("\nLoading warehouse...")
    graph, warehouse = load_physical_warehouse('warehouse_physical.json')
    
    # Verify start and end points exist
    start = "Staging_Area"
    end = "Charging_Station"
    
    if start not in graph.nodes:
        print(f"Error: {start} not found in graph!")
        return
    
    if end not in graph.nodes:
        print(f"Error: {end} not found in graph!")
        return
    
    print(f"✓ Start point: {start}")
    print(f"✓ End point: {end}")
    
    # Select some picks from different racks
    # Get picks from the largest connected component
    if not nx.is_connected(graph):
        largest_cc = max(nx.connected_components(graph), key=len)
        print(f"\n⚠ Graph has multiple components. Using largest component ({len(largest_cc)} nodes)")
        
        # Filter nodes to only those in the component
        if start not in largest_cc:
            print(f"⚠ Warning: {start} not in largest component!")
            return
        if end not in largest_cc:
            print(f"⚠ Warning: {end} not in largest component!")
            return
    else:
        largest_cc = set(graph.nodes())
    
    # Get rack picks from the connected component
    all_picks = [n for n, d in graph.nodes(data=True) 
                 if d.get('type') == 'pick' 
                 and d.get('parent', '').startswith('Rack_')
                 and n in largest_cc]
    
    print(f"\nAvailable picks in connected component: {len(all_picks)}")
    
    # Select a diverse set of picks
    picks_by_rack = {}
    for pick in all_picks:
        rack = graph.nodes[pick].get('parent')
        if rack not in picks_by_rack:
            picks_by_rack[rack] = []
        picks_by_rack[rack].append(pick)
    
    # Get 1-2 picks from each rack
    selected_picks = []
    for rack in sorted(picks_by_rack.keys()):
        selected_picks.extend(picks_by_rack[rack][:2])
    
    # Limit to 6 picks for reasonable computation
    selected_picks = selected_picks[:6]
    
    if len(selected_picks) < 2:
        print("Not enough picks available!")
        return
    
    print(f"\nSelected {len(selected_picks)} picks from {len(picks_by_rack)} racks:")
    for rack, picks in sorted(picks_by_rack.items()):
        rack_selected = [p for p in selected_picks if p in picks]
        if rack_selected:
            print(f"  {rack}: {rack_selected}")
    
    # Solve the route
    print("\n" + "="*70)
    print("ROUTE OPTIMIZATION")
    print("="*70)
    
    full_route, total_distance, pick_order = solve_pick_route_with_endpoints(
        graph, start, selected_picks, end
    )
    
    if full_route is None:
        print("\n❌ Could not find valid route!")
        return
    
    # Display results
    print("\n" + "="*70)
    print("OPTIMIZED ROUTE")
    print("="*70)
    
    print(f"\nPick sequence: {' → '.join(pick_order)}")
    print(f"Total distance: {total_distance:.2f} units")
    print(f"Total waypoints: {len(full_route)} nodes")
    
    # Show the full route broken down by segments
    print(f"\nFull route:")
    print(f"  {' → '.join(full_route[:5])}")
    if len(full_route) > 10:
        print(f"  ... ({len(full_route) - 10} intermediate waypoints)")
        print(f"  {' → '.join(full_route[-5:])}")
    elif len(full_route) > 5:
        print(f"  {' → '.join(full_route[5:])}")
    
    # Calculate segment distances
    print(f"\nRoute segments:")
    current = start
    segment_num = 1
    
    # Start to first pick
    first_pick = pick_order[0]
    dist = nx.shortest_path_length(graph, current, first_pick, weight='weight')
    print(f"  {segment_num}. {current} → {first_pick}: {dist:.2f} units")
    current = first_pick
    segment_num += 1
    
    # Between picks
    for i in range(len(pick_order) - 1):
        next_pick = pick_order[i + 1]
        dist = nx.shortest_path_length(graph, current, next_pick, weight='weight')
        print(f"  {segment_num}. {current} → {next_pick}: {dist:.2f} units")
        current = next_pick
        segment_num += 1
    
    # Last pick to end
    dist = nx.shortest_path_length(graph, current, end, weight='weight')
    print(f"  {segment_num}. {current} → {end}: {dist:.2f} units")
    
    # Show racks visited
    racks_visited = []
    for pick in pick_order:
        rack = graph.nodes[pick].get('parent')
        if rack and rack not in racks_visited:
            racks_visited.append(rack)
    
    print(f"\nRacks visited: {', '.join(racks_visited)}")
    print(f"Number of racks: {len(racks_visited)}")
    print(f"Number of picks: {len(pick_order)}")
    
    # Visualize
    print("\n" + "="*70)
    print("VISUALIZATION")
    print("="*70)
    print("\nGenerating warehouse visualization...")
    print("(The optimized route is shown by the graph edges)")
    print("\nFor detailed route visualization with edge weights, run:")
    print("  python example_visual_route.py")
    print("\nClose the plot window to exit.")
    
    visualize_physical_warehouse(warehouse, graph, show_blocked_paths=False)


if __name__ == "__main__":
    main()
