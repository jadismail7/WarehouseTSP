"""
Physical Warehouse Visualization

Visualizes warehouses with physical dimensions, showing obstacles,
traversable areas, pick points, and graph connections.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx


def visualize_physical_warehouse(warehouse, graph, show_blocked_paths=False, 
                                 max_connection_dist=20):
    """
    Visualize a physical warehouse with obstacles and graph.
    
    Args:
        warehouse: PhysicalWarehouse object
        graph: NetworkX graph
        show_blocked_paths: Whether to show paths blocked by obstacles
        max_connection_dist: Max distance for showing blocked paths
    """
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Draw obstacles (non-traversable objects)
    for obj in warehouse.obstacles:
        rect = patches.Rectangle(
            (obj.center_x - obj.width/2, obj.center_y - obj.depth/2),
            obj.width, obj.depth,
            linewidth=2, edgecolor='black', facecolor='lightgray', alpha=0.7
        )
        ax.add_patch(rect)
        
        # Label obstacles
        ax.text(obj.center_x, obj.center_y, obj.id,
               ha='center', va='center', fontsize=8, weight='bold')
    
    # Draw traversable areas
    for obj in warehouse.traversable_areas:
        rect = patches.Rectangle(
            (obj.center_x - obj.width/2, obj.center_y - obj.depth/2),
            obj.width, obj.depth,
            linewidth=1, edgecolor='green', facecolor='lightgreen', alpha=0.2,
            linestyle='--'
        )
        ax.add_patch(rect)
        
        # Label aisles
        ax.text(obj.center_x, obj.center_y, obj.id,
               ha='center', va='center', fontsize=7, color='green', style='italic')
    
    # Optionally show blocked paths
    if show_blocked_paths:
        for node_id, node_data in warehouse.nodes.items():
            nearby = warehouse.get_nearby_nodes(node_id, max_connection_dist)
            for other_id, dist in nearby:
                if not graph.has_edge(node_id, other_id):
                    other = warehouse.nodes[other_id]
                    ax.plot([node_data['x'], other['x']], 
                           [node_data['y'], other['y']],
                           'r-', alpha=0.1, linewidth=0.5)
    
    # Draw graph edges (clear paths)
    pos = {node: (data['x'], data['y']) for node, data in graph.nodes(data=True)}
    
    # Color edges by type
    edge_colors = []
    edge_widths = []
    for u, v in graph.edges():
        u_type = graph.nodes[u].get('type', 'unknown')
        v_type = graph.nodes[v].get('type', 'unknown')
        
        if u_type == 'pick' and v_type == 'pick':
            # Pick-to-pick connections
            parent_u = graph.nodes[u].get('parent')
            parent_v = graph.nodes[v].get('parent')
            if parent_u == parent_v:
                edge_colors.append('blue')  # Same rack
                edge_widths.append(1.5)
            else:
                edge_colors.append('orange')  # Different racks
                edge_widths.append(1.0)
        else:
            # Connections through aisles
            edge_colors.append('darkgreen')
            edge_widths.append(2.0)
    
    # Draw edges
    for idx, (u, v) in enumerate(graph.edges()):
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.plot([x1, x2], [y1, y2], 
               color=edge_colors[idx], 
               alpha=0.6, 
               linewidth=edge_widths[idx],
               zorder=1)
    
    # Draw nodes
    pick_nodes = [n for n, d in graph.nodes(data=True) if d.get('type') == 'pick']
    aisle_nodes = [n for n, d in graph.nodes(data=True) if d.get('type') != 'pick']
    
    # Pick points
    pick_pos = {n: pos[n] for n in pick_nodes}
    if pick_pos:
        xs, ys = zip(*pick_pos.values())
        ax.scatter(xs, ys, c='red', s=100, marker='o', 
                  edgecolors='darkred', linewidths=2, 
                  label='Pick Points', zorder=3)
    
    # Aisle waypoints
    aisle_pos = {n: pos[n] for n in aisle_nodes}
    if aisle_pos:
        xs, ys = zip(*aisle_pos.values())
        ax.scatter(xs, ys, c='lightblue', s=150, marker='s', 
                  edgecolors='blue', linewidths=2, 
                  label='Aisle Waypoints', zorder=2)
    
    # Label nodes
    for node, (x, y) in pos.items():
        ax.annotate(node, (x, y), fontsize=6, ha='center', va='bottom',
                   xytext=(0, 3), textcoords='offset points')
    
    # Set bounds
    bounds = warehouse.get_bounds()
    margin = 5
    ax.set_xlim(bounds['x_min'] - margin, bounds['x_max'] + margin)
    ax.set_ylim(bounds['y_min'] - margin, bounds['y_max'] + margin)
    
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title('Physical Warehouse Layout with Obstacle-Aware Graph', fontsize=14, weight='bold')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    plt.show()


def print_physical_warehouse_summary(warehouse, graph):
    """Print summary statistics for physical warehouse."""
    print("\n" + "="*60)
    print("PHYSICAL WAREHOUSE SUMMARY")
    print("="*60)
    
    print(f"\nWarehouse Objects:")
    print(f"  Total objects: {len(warehouse.objects)}")
    print(f"  Obstacles (non-traversable): {len(warehouse.obstacles)}")
    print(f"  Traversable areas: {len(warehouse.traversable_areas)}")
    
    print(f"\nGraph Statistics:")
    print(f"  Total nodes: {graph.number_of_nodes()}")
    
    pick_nodes = [n for n, d in graph.nodes(data=True) if d.get('type') == 'pick']
    aisle_nodes = [n for n, d in graph.nodes(data=True) if d.get('type') != 'pick']
    
    print(f"    - Pick points: {len(pick_nodes)}")
    print(f"    - Aisle waypoints: {len(aisle_nodes)}")
    
    print(f"  Total edges: {graph.number_of_edges()}")
    print(f"  Connected: {nx.is_connected(graph)}")
    
    if nx.is_connected(graph):
        print(f"  Average degree: {sum(dict(graph.degree()).values()) / graph.number_of_nodes():.2f}")
    else:
        components = list(nx.connected_components(graph))
        print(f"  ⚠ Disconnected components: {len(components)}")
        for i, comp in enumerate(components):
            print(f"    Component {i+1}: {len(comp)} nodes")
    
    # Edge type breakdown
    same_rack = 0
    cross_rack = 0
    through_aisle = 0
    
    for u, v in graph.edges():
        u_type = graph.nodes[u].get('type', 'unknown')
        v_type = graph.nodes[v].get('type', 'unknown')
        
        if u_type == 'pick' and v_type == 'pick':
            parent_u = graph.nodes[u].get('parent')
            parent_v = graph.nodes[v].get('parent')
            if parent_u == parent_v:
                same_rack += 1
            else:
                cross_rack += 1
        else:
            through_aisle += 1
    
    print(f"\nEdge Types:")
    print(f"  Same-rack connections: {same_rack}")
    print(f"  Cross-rack connections: {cross_rack}")
    print(f"  Through-aisle connections: {through_aisle}")
    
    # Bounds
    bounds = warehouse.get_bounds()
    print(f"\nWarehouse Bounds:")
    print(f"  X: [{bounds['x_min']:.1f}, {bounds['x_max']:.1f}] (width: {bounds['x_max'] - bounds['x_min']:.1f})")
    print(f"  Y: [{bounds['y_min']:.1f}, {bounds['y_max']:.1f}] (depth: {bounds['y_max'] - bounds['y_min']:.1f})")
    
    print("="*60 + "\n")
