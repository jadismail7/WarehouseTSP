"""
CLI Visualization Functions

All visualization functions for both physical and legacy warehouse formats.
"""

import math
import matplotlib.pyplot as plt
import networkx as nx


def visualize_graph_only_legacy(graph, output_path, display=True):
    """Visualize legacy warehouse graph"""
    import pandas as pd
    
    # Create a locations dataframe from graph node attributes
    locs_data = []
    for node in graph.nodes():
        node_data = graph.nodes[node]
        locs_data.append({
            'id': node,
            'x': node_data['x'],
            'y': node_data['y'],
            'v_aisle': node_data.get('v_aisle', -1),
            'h_aisle': node_data.get('h_aisle', -1)
        })
    locs = pd.DataFrame(locs_data)
    
    # Use legacy visualization
    plt.figure(figsize=(16, 12))
    pos = {n: (graph.nodes[n]['x'], graph.nodes[n]['y']) for n in graph.nodes}
    
    # Color nodes by vertical aisle
    v_aisle_colors = [graph.nodes[n].get('v_aisle', -1) for n in graph.nodes]
    node_colors = ['red' if v == -1 else plt.cm.tab20(v % 20) for v in v_aisle_colors]
    
    # Categorize edges
    intra_aisle_edges = []
    cross_aisle_edges = []
    connector_edges = []
    
    for a, b in graph.edges():
        a_v = graph.nodes[a].get('v_aisle', -1)
        b_v = graph.nodes[b].get('v_aisle', -1)
        a_h = graph.nodes[a].get('h_aisle', -1)
        b_h = graph.nodes[b].get('h_aisle', -1)
        
        if (a_v == b_v and a_v >= 0) or (a_h == b_h and a_h >= 0):
            intra_aisle_edges.append((a, b))
        elif a_v >= 0 and b_v >= 0 and a_h >= 0 and b_h >= 0:
            cross_aisle_edges.append((a, b))
        else:
            connector_edges.append((a, b))
    
    # Draw edges
    nx.draw_networkx_edges(graph, pos, edgelist=intra_aisle_edges, alpha=0.6, width=2, 
                          edge_color='blue', label='Intra-aisle')
    nx.draw_networkx_edges(graph, pos, edgelist=cross_aisle_edges, alpha=0.8, width=3, 
                          edge_color='green', label='Cross-aisle')
    nx.draw_networkx_edges(graph, pos, edgelist=connector_edges, alpha=0.4, width=1.5, 
                          edge_color='gray', style='dashed', label='Connectors')
    
    # Draw nodes
    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=500, alpha=0.8, 
                          edgecolors='black', linewidths=1.5)
    nx.draw_networkx_labels(graph, pos, font_size=7, font_weight='bold')
    
    plt.title(f'Legacy Warehouse Graph\n{graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges\n'
             'Same color = same vertical aisle, Red = isolated\n'
             'Blue=Intra-aisle, Green=Cross-aisle, Gray=Connectors', fontsize=12)
    plt.legend(loc='upper right')
    plt.axis('equal')
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Graph visualization saved to: {output_path}")
    
    if display:
        plt.show()
    else:
        plt.close()


def visualize_graph_only(warehouse, graph, output_path, display=True):
    """Visualize just the warehouse graph (physical format)"""
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Draw obstacles
    for obj in warehouse.obstacles:
        vertices = list(obj.polygon.exterior.coords)
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        ax.fill(xs, ys, color='gray', alpha=0.3, edgecolor='black', linewidth=1)
        ax.text(obj.center_x, obj.center_y, obj.id.replace('_', '\n'),
               fontsize=7, ha='center', va='center', color='black', alpha=0.5)
    
    # Draw traversable areas
    for obj in warehouse.traversable_areas:
        vertices = list(obj.polygon.exterior.coords)
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        ax.fill(xs, ys, color='lightblue', alpha=0.2, edgecolor='blue', linewidth=1)
    
    # Draw graph edges (sample)
    pos = {node: (graph.nodes[node]['x'], graph.nodes[node]['y']) for node in graph.nodes}
    edge_sample = list(graph.edges())[:1000]
    nx.draw_networkx_edges(graph, pos, edgelist=edge_sample, alpha=0.2, width=0.5)
    
    # Draw pick points
    pick_nodes = [n for n in graph.nodes if '-' in n]
    pick_pos = {n: pos[n] for n in pick_nodes if n in pos}
    nx.draw_networkx_nodes(graph, pick_pos, nodelist=list(pick_pos.keys()),
                          node_color='red', node_size=20, alpha=0.6)
    
    ax.set_aspect('equal')
    ax.set_title(f'Warehouse Graph\n{graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges',
                fontsize=14, fontweight='bold')
    ax.set_xlabel('X coordinate')
    ax.set_ylabel('Y coordinate')
    
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Graph visualization saved to: {output_path}")
    
    if display:
        plt.show()
    else:
        plt.close()


def visualize_route_legacy(graph, route, pick_order, start, end, total_distance,
                           output_path, display=True):
    """Visualize the optimized route (legacy format)"""
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Get node positions
    pos = {node: (graph.nodes[node]['x'], graph.nodes[node]['y']) for node in graph.nodes}
    
    # Draw all edges lightly
    nx.draw_networkx_edges(graph, pos, alpha=0.1, width=0.5, edge_color='gray')
    
    # Draw route path
    route_edges = []
    for i in range(len(route) - 1):
        if graph.has_edge(route[i], route[i+1]):
            route_edges.append((route[i], route[i+1]))
    
    nx.draw_networkx_edges(graph, pos, edgelist=route_edges,
                          edge_color='red', width=3, alpha=0.7,
                          arrows=True, arrowsize=15, arrowstyle='->')
    
    # Draw all nodes
    nx.draw_networkx_nodes(graph, pos, node_color='lightgray', node_size=100, alpha=0.5)
    
    # Highlight picks with numbers
    pick_positions = {p: pos[p] for p in pick_order if p in pos}
    if pick_positions:
        nx.draw_networkx_nodes(graph, pick_positions, nodelist=list(pick_positions.keys()),
                              node_color='yellow', node_size=300,
                              edgecolors='red', linewidths=3)
        
        # Track location counts for duplicates
        location_counts = {}
        
        for i, pick in enumerate(pick_order, 1):
            if pick in pos:
                x, y = pos[pick]
                
                # Handle duplicate locations by offsetting labels
                location_key = (x, y)
                if location_key in location_counts:
                    offset_angle = location_counts[location_key] * (2 * math.pi / 4)
                    offset_dist = 2.0
                    x_offset = x + offset_dist * math.cos(offset_angle)
                    y_offset = y + offset_dist * math.sin(offset_angle)
                    location_counts[location_key] += 1
                else:
                    x_offset, y_offset = x, y
                    location_counts[location_key] = 1
                
                ax.text(x_offset, y_offset, str(i), fontsize=10, fontweight='bold',
                       ha='center', va='center', color='black',
                       bbox=dict(boxstyle='circle', facecolor='yellow',
                               edgecolor='red', linewidth=2))
    
    # Highlight start and end
    if start in pos:
        x, y = pos[start]
        ax.scatter([x], [y], c='green', s=500, marker='*',
                  edgecolors='darkgreen', linewidths=3, zorder=10, label='Start')
    
    if end in pos:
        x, y = pos[end]
        ax.scatter([x], [y], c='blue', s=500, marker='*',
                  edgecolors='darkblue', linewidths=3, zorder=10, label='End')
    
    ax.set_aspect('equal')
    ax.set_title(f'Legacy Warehouse Route\n{len(pick_order)} picks, Distance: {total_distance:.2f} units',
                fontsize=16, fontweight='bold')
    ax.legend(fontsize=12, loc='upper right')
    ax.set_xlabel('X coordinate')
    ax.set_ylabel('Y coordinate')
    
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Route visualization saved to: {output_path}")
    
    if display:
        plt.show()
    else:
        plt.close()


def visualize_route(warehouse, graph, route, pick_order, start, end, total_distance, 
                    output_path, display=True):
    """Visualize the optimized route (physical format)"""
    fig, ax = plt.subplots(figsize=(20, 18))
    
    # Draw obstacles
    for obj in warehouse.obstacles:
        vertices = list(obj.polygon.exterior.coords)
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        ax.fill(xs, ys, color='gray', alpha=0.3, edgecolor='black', linewidth=1)
        ax.text(obj.center_x, obj.center_y, obj.id.replace('_', '\n'),
               fontsize=7, ha='center', va='center', color='black', alpha=0.5)
    
    # Draw traversable areas
    for obj in warehouse.traversable_areas:
        vertices = list(obj.polygon.exterior.coords)
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        ax.fill(xs, ys, color='lightblue', alpha=0.2, edgecolor='blue', linewidth=1)
    
    # Get node positions
    pos = {node: (graph.nodes[node]['x'], graph.nodes[node]['y']) for node in graph.nodes}
    
    # Draw route path
    route_edges = []
    for i in range(len(route) - 1):
        if graph.has_edge(route[i], route[i+1]):
            route_edges.append((route[i], route[i+1]))
    
    nx.draw_networkx_edges(graph, pos, edgelist=route_edges,
                          edge_color='red', width=3, alpha=0.7,
                          arrows=True, arrowsize=15, arrowstyle='->')
    
    # Highlight picks with numbers
    pick_positions = {p: pos[p] for p in pick_order if p in pos}
    if pick_positions:
        nx.draw_networkx_nodes(graph, pick_positions, nodelist=list(pick_positions.keys()),
                              node_color='yellow', node_size=300,
                              edgecolors='red', linewidths=3)
        
        # Track location counts for duplicates
        location_counts = {}
        
        for i, pick in enumerate(pick_order, 1):
            if pick in pos:
                x, y = pos[pick]
                
                # Handle duplicate locations by offsetting labels
                location_key = (x, y)
                if location_key in location_counts:
                    offset_angle = location_counts[location_key] * (2 * math.pi / 4)
                    offset_dist = 2.0
                    x_offset = x + offset_dist * math.cos(offset_angle)
                    y_offset = y + offset_dist * math.sin(offset_angle)
                    location_counts[location_key] += 1
                else:
                    x_offset, y_offset = x, y
                    location_counts[location_key] = 1
                
                ax.text(x_offset, y_offset, str(i), fontsize=10, fontweight='bold',
                       ha='center', va='center', color='black',
                       bbox=dict(boxstyle='circle', facecolor='yellow',
                               edgecolor='red', linewidth=2))
    
    # Highlight start and end
    if start in pos:
        x, y = pos[start]
        ax.scatter([x], [y], c='green', s=500, marker='*',
                  edgecolors='darkgreen', linewidths=3, zorder=10, label='Start')
    
    if end in pos:
        x, y = pos[end]
        ax.scatter([x], [y], c='blue', s=500, marker='*',
                  edgecolors='darkblue', linewidths=3, zorder=10, label='End')
    
    ax.set_aspect('equal')
    ax.set_title(f'Optimized Pick Route\n{len(pick_order)} picks, Distance: {total_distance:.2f} units',
                fontsize=16, fontweight='bold')
    ax.legend(fontsize=12, loc='upper right')
    ax.set_xlabel('X coordinate')
    ax.set_ylabel('Y coordinate')
    
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Route visualization saved to: {output_path}")
    
    if display:
        plt.show()
    else:
        plt.close()
