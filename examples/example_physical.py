"""
Example: Physical Warehouse TSP

Demonstrates TSP solving on a warehouse with physical dimensions and obstacles.
"""

import sys
import networkx as nx
from physical_layout import load_physical_warehouse
from physical_visualization import visualize_physical_warehouse, print_physical_warehouse_summary
from routing import find_shortest_path, solve_tsp


def main():
    print("Loading physical warehouse layout...")
    graph, warehouse = load_physical_warehouse('warehouse_physical.json')
    
    # Print summary
    print_physical_warehouse_summary(warehouse, graph)
    
    # Demonstrate shortest path between two pick points
    print("\n" + "="*60)
    print("SHORTEST PATH EXAMPLE")
    print("="*60)
    
    # Pick two nodes from different racks
    pick_nodes = [n for n, d in graph.nodes(data=True) if d.get('type') == 'pick']
    
    if len(pick_nodes) >= 2:
        start = pick_nodes[0]
        end = pick_nodes[-1]
        
        path, distance = find_shortest_path(graph, start, end)
        
        if path:
            print(f"\nShortest path from {start} to {end}:")
            print(f"  Path: {' -> '.join(path)}")
            print(f"  Total distance: {distance:.2f} units")
            print(f"  Path length: {len(path)} nodes")
        else:
            print(f"\n⚠ No path found between {start} and {end}")
            print(f"   (Nodes may be in different disconnected components)")
    
    # Solve TSP for multiple pick points
    print("\n" + "="*60)
    print("TSP OPTIMIZATION EXAMPLE")
    print("="*60)
    
    # Select only RACK pick points (not aisle waypoints)
    rack_picks = [n for n, d in graph.nodes(data=True) 
                  if d.get('type') == 'pick' and d.get('parent', '').startswith('Rack_')]
    
    if len(rack_picks) >= 5:
        # Get the largest connected component
        if not nx.is_connected(graph):
            largest_cc = max(nx.connected_components(graph), key=len)
            rack_picks = [p for p in rack_picks if p in largest_cc]
            print(f"\n  Note: Using picks from largest connected component only ({len(rack_picks)} picks)")
        
        # Select picks from different racks (get up to 10)
        picks_by_rack = {}
        for node in rack_picks:
            parent = graph.nodes[node].get('parent')
            if parent not in picks_by_rack:
                picks_by_rack[parent] = []
            picks_by_rack[parent].append(node)
        
        # Get multiple picks from each rack for a more interesting route
        selected_picks = []
        max_picks_per_rack = max(3, 10 // len(picks_by_rack))  # Distribute picks across racks
        for rack, picks in sorted(picks_by_rack.items()):
            selected_picks.extend(picks[:max_picks_per_rack])
        
        selected_picks = selected_picks[:10]  # Limit to 10 for reasonable computation
        
        print(f"\nOptimizing route for {len(selected_picks)} pick points...")
        print(f"Picks: {selected_picks}")
        
        # Verify all picks are connected
        picks_in_graph = [p for p in selected_picks if p in graph]
        if len(picks_in_graph) < len(selected_picks):
            print(f"  ⚠ {len(selected_picks) - len(picks_in_graph)} picks not in graph")
            selected_picks = picks_in_graph
        
        # Check connectivity
        subgraph_nodes = set()
        for pick in selected_picks:
            subgraph_nodes.add(pick)
            # Add immediate neighbors to help with connectivity
            subgraph_nodes.update(graph.neighbors(pick))
        
        subgraph = graph.subgraph(subgraph_nodes)
        
        if nx.is_connected(subgraph):
            tsp_route, tsp_distance = solve_tsp(graph, selected_picks)
            
            print(f"\nOptimized TSP route:")
            print(f"  Route: {' -> '.join(tsp_route)}")
            print(f"  Total distance: {tsp_distance:.2f} units")
            print(f"  Number of picks: {len(tsp_route)}")
            
            # Show which racks are visited
            racks_visited = []
            for node in tsp_route:
                rack = graph.nodes[node].get('parent')
                if rack and rack not in racks_visited:
                    racks_visited.append(rack)
            
            print(f"  Racks visited: {racks_visited}")
        else:
            # Try with fewer picks from the same component
            print(f"\n⚠ Selected picks span disconnected components")
            print(f"   Retrying with picks from largest component only...")
            
            # Find largest component among selected picks
            comps = list(nx.connected_components(graph.subgraph(selected_picks)))
            if comps:
                largest_pick_comp = max(comps, key=len)
                connected_picks = list(largest_pick_comp)[:10]
                
                print(f"   Using {len(connected_picks)} connected picks: {connected_picks}")
                
                tsp_route, tsp_distance = solve_tsp(graph, connected_picks)
                
                print(f"\nOptimized TSP route:")
                print(f"  Route: {' -> '.join(tsp_route)}")
                print(f"  Total distance: {tsp_distance:.2f} units")
                print(f"  Number of picks: {len(tsp_route)}")
                
                # Show which racks are visited
                racks_visited = []
                for node in tsp_route:
                    rack = graph.nodes[node].get('parent')
                    if rack and rack not in racks_visited:
                        racks_visited.append(rack)
                
                print(f"  Racks visited: {racks_visited}")
    
    # Visualize the warehouse
    print("\n" + "="*60)
    print("Generating visualization...")
    print("="*60)
    print("\nClose the plot window to exit.")
    
    visualize_physical_warehouse(warehouse, graph, show_blocked_paths=False)


if __name__ == "__main__":
    main()
