#!/usr/bin/env python3
"""
Large Warehouse: Complex Pick Route with 20 Items using 2-opt TSP Heuristic
"""

import random
from physical_layout import load_physical_warehouse
from physical_visualization import visualize_physical_warehouse
from routing import solve_tsp_with_endpoints
import networkx as nx
import matplotlib.pyplot as plt

def solve_large_pick_route(graph, start_node, pick_locations, end_node, method='2-opt'):
    """
    Solve pick route using specified TSP heuristic.
    
    Args:
        graph: NetworkX graph
        start_node: Starting location
        pick_locations: List of pick points to visit
        end_node: Ending location
        method: '2-opt', 'greedy', or 'exhaustive'
    
    Returns:
        tuple: (full_route, total_distance, pick_order)
    """
    valid_picks = [p for p in pick_locations if p in graph.nodes]
    
    if not valid_picks:
        print("No valid pick locations found!")
        return None, None, None
    
    print(f"\nOptimizing route for {len(valid_picks)} picks...")
    print(f"Start: {start_node}")
    print(f"End: {end_node}")
    print(f"  Using {method} algorithm...")
    
    return solve_tsp_with_endpoints(graph, start_node, valid_picks, end_node, method=method)


print("="*70)
print("LARGE WAREHOUSE: 20-ITEM PICK ROUTE")
print("="*70)

# Load warehouse with larger connection distance
print("\nLoading warehouse...")
graph, warehouse = load_physical_warehouse('warehouse_large.json')

# Rebuild with larger connection distance to connect components
print("Rebuilding graph with max_connection_dist=50...")
graph = warehouse.build_graph(max_connection_dist=50)

print(f"  Nodes: {graph.number_of_nodes()}")
print(f"  Edges: {graph.number_of_edges()}")

# Get all available picks
all_picks = [n for n in graph.nodes if '-' in n and any(c in n for c in 'ABCDEFGH')]
print(f"  Available picks: {len(all_picks)}")

# Select 20 random picks from different racks
random.seed(42)  # For reproducibility
selected_picks = random.sample(all_picks, 20)
selected_picks.sort()

print(f"\nSelected 20 picks:")
for i, pick in enumerate(selected_picks, 1):
    print(f"  {i:2d}. {pick}")

# Count picks per rack
from collections import Counter
rack_distribution = Counter([p.split('-')[0] for p in selected_picks])
print(f"\nPicks per rack:")
for rack, count in sorted(rack_distribution.items()):
    print(f"  {rack}: {count} picks")

# Set start and end points
start_node = 'Staging_Area_West'
end_node = 'Staging_Area_East'

print(f"\nRoute parameters:")
print(f"  Start: {start_node}")
print(f"  End: {end_node}")
print(f"  Picks to visit: {len(selected_picks)}")

# Solve the route with different methods and compare
methods = ['greedy', '2-opt']
results = {}

for method in methods:
    print(f"\n{'='*70}")
    print(f"TRYING {method.upper()} ALGORITHM")
    print('='*70)
    
    route, total_distance, pick_order = solve_large_pick_route(
        graph, start_node, selected_picks, end_node, method=method
    )
    
    if route:
        results[method] = {
            'route': route,
            'distance': total_distance,
            'pick_order': pick_order
        }
        print(f"\n  ✓ Distance: {total_distance:.2f} units")
        print(f"  ✓ Pick order: {' → '.join(pick_order)}")

# Choose best result
best_method = min(results.keys(), key=lambda m: results[m]['distance'])
route = results[best_method]['route']
total_distance = results[best_method]['distance']
pick_order = results[best_method]['pick_order']

print(f"\n{'='*70}")
print(f"BEST ALGORITHM: {best_method.upper()}")
print('='*70)

for method in methods:
    if method in results:
        marker = " ← BEST" if method == best_method else ""
        improvement = ""
        if method != best_method:
            diff = results[method]['distance'] - total_distance
            improvement = f" (+{diff:.2f} units worse)"
        print(f"  {method:15s}: {results[method]['distance']:8.2f} units{improvement}{marker}")

if route:
    print(f"\n" + "="*70)
    print("OPTIMIZED ROUTE")
    print("="*70)
    
    print(f"\nPick sequence: {' → '.join(pick_order)}")
    print(f"Total distance: {total_distance:.2f} units")
    print(f"Total waypoints: {len(route)} nodes")
    
    # Show first and last few waypoints
    print(f"\nFirst 10 waypoints:")
    for i, node in enumerate(route[:10], 1):
        marker = " ← PICK" if node in selected_picks else ""
        print(f"  {i:2d}. {node}{marker}")
    
    if len(route) > 20:
        print(f"  ... ({len(route) - 20} waypoints omitted)")
        print(f"\nLast 10 waypoints:")
        for i, node in enumerate(route[-10:], len(route)-9):
            marker = " ← PICK" if node in selected_picks else ""
            print(f"  {i:3d}. {node}{marker}")
    
    print(f"\n" + "="*70)
    print("VISUALIZATION")
    print("="*70)
    
    # Create visualization
    print("\nGenerating visualization...")
    fig = plt.figure(figsize=(20, 18))
    ax = plt.gca()
    
    # Draw warehouse obstacles
    for obj in warehouse.obstacles:
        vertices = list(obj.polygon.exterior.coords)
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        ax.fill(xs, ys, color='gray', alpha=0.3, edgecolor='black', linewidth=1)
        
        # Label
        ax.text(obj.center_x, obj.center_y, obj.id.replace('_', '\n'),
               fontsize=8, ha='center', va='center', color='black', alpha=0.5)
    
    # Draw traversable areas
    for obj in warehouse.traversable_areas:
        vertices = list(obj.polygon.exterior.coords)
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        ax.fill(xs, ys, color='lightblue', alpha=0.2, edgecolor='blue', linewidth=1)
    
    # Highlight the route
    route_edges = []
    for i in range(len(route) - 1):
        if graph.has_edge(route[i], route[i+1]):
            route_edges.append((route[i], route[i+1]))
    
    # Get node positions
    pos = {node: (graph.nodes[node]['x'], graph.nodes[node]['y']) for node in graph.nodes}
    
    # Draw route path
    nx.draw_networkx_edges(graph, pos, edgelist=route_edges, 
                          edge_color='red', width=3, alpha=0.7,
                          arrows=True, arrowsize=15, arrowstyle='->')
    
    # Highlight picks
    pick_positions = {p: pos[p] for p in selected_picks if p in pos}
    if pick_positions:
        nx.draw_networkx_nodes(graph, pick_positions, nodelist=list(pick_positions.keys()),
                              node_color='yellow', node_size=300, 
                              edgecolors='red', linewidths=3)
        
        # Number the picks
        for i, pick in enumerate(pick_order, 1):
            if pick in pos:
                x, y = pos[pick]
                ax.text(x, y, str(i), fontsize=10, fontweight='bold',
                       ha='center', va='center', color='black',
                       bbox=dict(boxstyle='circle', facecolor='yellow', 
                               edgecolor='red', linewidth=2))
    
    # Highlight start and end
    if start_node in pos:
        x, y = pos[start_node]
        ax.scatter([x], [y], c='green', s=500, marker='*', 
                  edgecolors='darkgreen', linewidths=3, zorder=10, label='Start')
    
    if end_node in pos:
        x, y = pos[end_node]
        ax.scatter([x], [y], c='blue', s=500, marker='*',
                  edgecolors='darkblue', linewidths=3, zorder=10, label='End')
    
    ax.set_title(f'Large Warehouse - 20 Pick Route\nTotal Distance: {total_distance:.2f} units', 
                fontsize=18, fontweight='bold')
    ax.legend(fontsize=12, loc='upper right')
    
    plt.tight_layout()
    plt.savefig('large_warehouse_route.png', dpi=150, bbox_inches='tight')
    print("  Saved to: large_warehouse_route.png")
    
    print("\nClose the plot window to exit...")
    plt.show()
    
else:
    print("\n❌ Failed to find a valid route!")

print("\n" + "="*70)
