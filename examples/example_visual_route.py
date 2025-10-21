"""
Enhanced Pick Route Example with Route Visualization

Shows the actual path taken with highlighted route.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
from physical_layout import load_physical_warehouse
from example_pick_route import solve_pick_route_with_endpoints


def visualize_pick_route(warehouse, graph, route, start, end, picks, show_all_weights=False):
    """
    Visualize the warehouse with the pick route highlighted.
    
    Args:
        warehouse: PhysicalWarehouse object
        graph: NetworkX graph
        route: List of nodes in the route
        start: Starting node
        end: Ending node
        picks: List of pick nodes visited
        show_all_weights: If True, show weights on all edges (can be cluttered)
    """
    fig, ax = plt.subplots(figsize=(18, 12))
    
    # Draw obstacles (non-traversable objects)
    for obj in warehouse.obstacles:
        rect = patches.Rectangle(
            (obj.center_x - obj.width/2, obj.center_y - obj.depth/2),
            obj.width, obj.depth,
            linewidth=2, edgecolor='black', facecolor='lightgray', alpha=0.7
        )
        ax.add_patch(rect)
        ax.text(obj.center_x, obj.center_y, obj.id,
               ha='center', va='center', fontsize=7, weight='bold')
    
    # Draw traversable areas
    for obj in warehouse.traversable_areas:
        # Highlight start and end specially
        if obj.id == start:
            color = 'lightblue'
            alpha = 0.4
            label_color = 'blue'
            label_weight = 'bold'
        elif obj.id == end:
            color = 'lightcoral'
            alpha = 0.4
            label_color = 'red'
            label_weight = 'bold'
        else:
            color = 'lightgreen'
            alpha = 0.2
            label_color = 'green'
            label_weight = 'normal'
        
        rect = patches.Rectangle(
            (obj.center_x - obj.width/2, obj.center_y - obj.depth/2),
            obj.width, obj.depth,
            linewidth=2, edgecolor='green', facecolor=color, alpha=alpha,
            linestyle='--'
        )
        ax.add_patch(rect)
        ax.text(obj.center_x, obj.center_y, obj.id,
               ha='center', va='center', fontsize=8, color=label_color, 
               style='italic', weight=label_weight)
    
    # Draw all graph edges (light gray)
    pos = {node: (data['x'], data['y']) for node, data in graph.nodes(data=True)}
    
    for u, v in graph.edges():
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.plot([x1, x2], [y1, y2], 
               color='lightgray', alpha=0.3, linewidth=0.5, zorder=1)
        
        # Optionally show weights on all edges
        if show_all_weights:
            weight = graph[u][v]['weight']
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            ax.text(mid_x, mid_y, f'{weight:.0f}',
                   fontsize=6, ha='center', va='center',
                   color='gray', alpha=0.6, zorder=1)
    
    # Highlight the route taken with weights
    route_edges = []
    for i in range(len(route) - 1):
        route_edges.append((route[i], route[i+1]))
    
    for u, v in route_edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.plot([x1, x2], [y1, y2], 
               color='blue', alpha=0.8, linewidth=3, zorder=2)
        
        # Add weight label on the edge
        if graph.has_edge(u, v):
            weight = graph[u][v]['weight']
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            ax.text(mid_x, mid_y, f'{weight:.1f}',
                   fontsize=8, ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                           edgecolor='blue', alpha=0.8),
                   zorder=5)
    
    # Draw all nodes (small)
    all_nodes_x = [pos[n][0] for n in graph.nodes()]
    all_nodes_y = [pos[n][1] for n in graph.nodes()]
    ax.scatter(all_nodes_x, all_nodes_y, c='lightgray', s=20, 
              alpha=0.5, zorder=3)
    
    # Highlight route waypoints
    route_set = set(route)
    waypoint_nodes = [n for n in route if n not in picks and n != start and n != end]
    if waypoint_nodes:
        wp_x = [pos[n][0] for n in waypoint_nodes]
        wp_y = [pos[n][1] for n in waypoint_nodes]
        ax.scatter(wp_x, wp_y, c='skyblue', s=50, marker='o',
                  edgecolors='blue', linewidths=1, alpha=0.6, zorder=4)
    
    # Highlight pick points
    pick_x = [pos[p][0] for p in picks]
    pick_y = [pos[p][1] for p in picks]
    ax.scatter(pick_x, pick_y, c='yellow', s=200, marker='*',
              edgecolors='orange', linewidths=2, 
              label='Pick Points', zorder=6)
    
    # Highlight start
    start_x, start_y = pos[start]
    ax.scatter([start_x], [start_y], c='green', s=300, marker='s',
              edgecolors='darkgreen', linewidths=3,
              label='Start (Staging)', zorder=7)
    
    # Highlight end
    end_x, end_y = pos[end]
    ax.scatter([end_x], [end_y], c='red', s=300, marker='s',
              edgecolors='darkred', linewidths=3,
              label='End (Charging)', zorder=7)
    
    # Add sequence numbers to picks
    for idx, pick in enumerate(picks, 1):
        x, y = pos[pick]
        ax.annotate(str(idx), (x, y), fontsize=10, weight='bold',
                   ha='center', va='center', color='red',
                   bbox=dict(boxstyle='circle', facecolor='white', 
                           edgecolor='red', linewidth=2),
                   zorder=8)
    
    # Add labels for start and end
    ax.annotate('START', (start_x, start_y), fontsize=9, weight='bold',
               ha='center', va='bottom', xytext=(0, 8),
               textcoords='offset points', color='darkgreen')
    ax.annotate('END', (end_x, end_y), fontsize=9, weight='bold',
               ha='center', va='bottom', xytext=(0, 8),
               textcoords='offset points', color='darkred')
    
    # Set bounds
    bounds = warehouse.get_bounds()
    margin = 5
    ax.set_xlim(bounds['x_min'] - margin, bounds['x_max'] + margin)
    ax.set_ylim(bounds['y_min'] - margin, bounds['y_max'] + margin)
    
    ax.set_xlabel('X Coordinate', fontsize=12)
    ax.set_ylabel('Y Coordinate', fontsize=12)
    ax.set_title(f'Optimized Pick Route: {len(picks)} picks, {len(route)} waypoints', 
                fontsize=14, weight='bold')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=10)
    
    plt.tight_layout()
    plt.show()


def main():
    print("="*70)
    print("PICK ROUTE WITH VISUAL ROUTE HIGHLIGHTING")
    print("="*70)
    
    # Load warehouse
    print("\nLoading warehouse...")
    graph, warehouse = load_physical_warehouse('warehouse_physical.json')
    
    # Define start and end
    start = "Staging_Area"
    end = "Charging_Station"
    
    # Check connectivity
    if not nx.is_connected(graph):
        largest_cc = max(nx.connected_components(graph), key=len)
        if start not in largest_cc or end not in largest_cc:
            print(f"Error: Start or end not in main component!")
            return
    else:
        largest_cc = set(graph.nodes())
    
    # Get picks
    all_picks = [n for n, d in graph.nodes(data=True) 
                 if d.get('type') == 'pick' 
                 and d.get('parent', '').startswith('Rack_')
                 and n in largest_cc]
    
    # Select diverse picks
    picks_by_rack = {}
    for pick in all_picks:
        rack = graph.nodes[pick].get('parent')
        if rack not in picks_by_rack:
            picks_by_rack[rack] = []
        picks_by_rack[rack].append(pick)
    
    selected_picks = []
    for rack in sorted(picks_by_rack.keys())[:4]:  # Only first 4 racks
        selected_picks.extend(picks_by_rack[rack][:2])
    
    selected_picks = selected_picks[:6]
    
    print(f"Selected picks: {selected_picks}")
    
    # Solve route
    full_route, total_distance, pick_order = solve_pick_route_with_endpoints(
        graph, start, selected_picks, end
    )
    
    if full_route is None:
        print("Could not find route!")
        return
    
    print(f"\n✓ Route found!")
    print(f"  Pick sequence: {' → '.join(pick_order)}")
    print(f"  Total distance: {total_distance:.2f} units")
    print(f"  Waypoints: {len(full_route)} nodes")
    
    # Visualize with route highlighted
    print("\nGenerating visualization with highlighted route...")
    print("  • Blue edges show the optimal path")
    print("  • Numbers on edges show distances")
    visualize_pick_route(warehouse, graph, full_route, start, end, list(pick_order), 
                        show_all_weights=False)


if __name__ == "__main__":
    main()
