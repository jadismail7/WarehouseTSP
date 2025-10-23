"""
Enhanced Visualization Module

Provides visualization for warehouse graphs with rack detection and physical properties.
Includes rack polygon rendering to show the physical extent of detected racks.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Polygon
import networkx as nx
import numpy as np


def get_rack_polygons(locs):
    """
    Generate polygons for each detected rack based on the bins it contains.
    
    Args:
        locs: DataFrame with location data including rack_id, x, y, width, depth
    
    Returns:
        dict: {rack_id: polygon_coords} where polygon_coords is a list of (x, y) points
    """
    rack_polygons = {}
    
    # Get bins that are part of racks
    bins_with_racks = locs[(locs['rack_id'] >= 0) & (locs['type'] == 'picking')]
    
    if len(bins_with_racks) == 0:
        return rack_polygons
    
    # Group by rack_id
    for rack_id in bins_with_racks['rack_id'].unique():
        rack_bins = bins_with_racks[bins_with_racks['rack_id'] == rack_id]
        
        # Get the bounding box of all bins in this rack
        min_x = rack_bins['x'].min() - rack_bins['width'].max() / 2
        max_x = rack_bins['x'].max() + rack_bins['width'].max() / 2
        min_y = rack_bins['y'].min() - rack_bins['depth'].max() / 2
        max_y = rack_bins['y'].max() + rack_bins['depth'].max() / 2
        
        # Create polygon (rectangle) for the rack
        polygon = [
            (min_x, min_y),
            (max_x, min_y),
            (max_x, max_y),
            (min_x, max_y),
            (min_x, min_y)  # Close the polygon
        ]
        
        rack_polygons[rack_id] = polygon
    
    return rack_polygons


def get_rack_pairs(locs):
    """
    Identify which racks are paired (opposite sides of aisles).
    
    Returns:
        list: [(rack_id1, rack_id2, side1, side2)] for paired racks
    """
    pairs = []
    bins_with_sides = locs[(locs['rack_side'] != 'none') & (locs['rack_id'] >= 0)]
    
    if len(bins_with_sides) == 0:
        return pairs
    
    # Group by rack_id and get side
    rack_info = {}
    for rack_id in bins_with_sides['rack_id'].unique():
        rack_bins = bins_with_sides[bins_with_sides['rack_id'] == rack_id]
        side = rack_bins.iloc[0]['rack_side']
        rack_info[rack_id] = side
    
    # Find pairs (left + right at similar y-coordinates)
    left_racks = [rid for rid, side in rack_info.items() if side == 'left']
    right_racks = [rid for rid, side in rack_info.items() if side == 'right']
    
    for left_id in left_racks:
        left_bins = bins_with_sides[bins_with_sides['rack_id'] == left_id]
        left_y = left_bins['y'].mean()
        left_x = left_bins['x'].mean()
        
        for right_id in right_racks:
            right_bins = bins_with_sides[bins_with_sides['rack_id'] == right_id]
            right_y = right_bins['y'].mean()
            right_x = right_bins['x'].mean()
            
            # Check if they're at similar y-coordinates (same aisle)
            if abs(left_y - right_y) < 30 and right_x > left_x:
                pairs.append((left_id, right_id, 'left', 'right'))
    
    return pairs


def visualize_graph_with_racks(locs, G, output_file=None, title="Warehouse Graph with Racks", display=True):
    """
    Visualize the warehouse graph with rack polygons overlaid.
    
    Args:
        locs: DataFrame with location data
        G: NetworkX graph
        output_file: Optional path to save the figure
        title: Plot title
        display: Whether to display the plot window
    """
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Get rack polygons
    rack_polygons = get_rack_polygons(locs)
    rack_pairs = get_rack_pairs(locs)
    
    # Create color map for rack pairs
    pair_colors = plt.cm.tab20(np.linspace(0, 1, len(rack_pairs) * 2))
    rack_color_map = {}
    
    for i, (left_id, right_id, _, _) in enumerate(rack_pairs):
        rack_color_map[left_id] = pair_colors[i * 2]
        rack_color_map[right_id] = pair_colors[i * 2 + 1]
    
    # Draw rack polygons first (background)
    for rack_id, polygon in rack_polygons.items():
        poly_x = [p[0] for p in polygon]
        poly_y = [p[1] for p in polygon]
        
        # Determine color
        if rack_id in rack_color_map:
            color = rack_color_map[rack_id]
            alpha = 0.2
        else:
            color = 'lightgray'
            alpha = 0.15
        
        ax.fill(poly_x, poly_y, color=color, alpha=alpha, edgecolor='gray', linewidth=1.5)
    
    # Draw edges
    pos = {row['id']: (row['x'], row['y']) for _, row in locs.iterrows() if row['id'] in G.nodes()}
    
    for u, v in G.edges():
        if u in pos and v in pos:
            x = [pos[u][0], pos[v][0]]
            y = [pos[u][1], pos[v][1]]
            ax.plot(x, y, 'b-', alpha=0.3, linewidth=0.8, zorder=1)
    
    # Draw nodes by type
    node_types = {
        'picking': {'color': 'green', 'marker': 's', 'size': 50, 'label': 'Picking'},
        'staging': {'color': 'orange', 'marker': 'D', 'size': 120, 'label': 'Staging'},
        'dock': {'color': 'red', 'marker': '^', 'size': 150, 'label': 'Dock'},
        'intersection': {'color': 'blue', 'marker': 'o', 'size': 80, 'label': 'Intersection'},
        'utility': {'color': 'purple', 'marker': 'P', 'size': 100, 'label': 'Utility'},
    }
    
    for node_type, style in node_types.items():
        type_locs = locs[locs['type'] == node_type]
        type_nodes = [row['id'] for _, row in type_locs.iterrows() if row['id'] in G.nodes()]
        
        if len(type_nodes) > 0:
            type_pos = [pos[n] for n in type_nodes]
            x = [p[0] for p in type_pos]
            y = [p[1] for p in type_pos]
            ax.scatter(x, y, c=style['color'], marker=style['marker'], 
                      s=style['size'], label=style['label'], zorder=3, edgecolors='black', linewidth=0.5)
    
    # Draw obstacles
    obstacles = locs[locs['traversable'] == False]
    for _, obs in obstacles.iterrows():
        rect = Rectangle(
            (obs['x'] - obs['width']/2, obs['y'] - obs['depth']/2),
            obs['width'], obs['depth'],
            facecolor='red', alpha=0.3, edgecolor='darkred', linewidth=2, zorder=2
        )
        ax.add_patch(rect)
    
    # Create legend
    legend_elements = [mpatches.Patch(facecolor='lightgray', alpha=0.2, edgecolor='gray', label='Racks')]
    
    # Add pair colors to legend
    for i, (left_id, right_id, _, _) in enumerate(rack_pairs[:5]):  # Show first 5 pairs
        legend_elements.append(
            mpatches.Patch(facecolor=rack_color_map[left_id], alpha=0.3, 
                          edgecolor='gray', label=f'Rack Pair {i+1}')
        )
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    # Add standard legend for node types
    ax.legend(loc='upper left', fontsize=10, ncol=2)
    
    ax.set_xlabel('X Coordinate', fontsize=12)
    ax.set_ylabel('Y Coordinate', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to: {output_file}")
    
    if display:
        plt.show()
    else:
        plt.close()


def visualize_route_with_racks(locs, G, route, pick_order, start, end, total_distance, 
                                output_file=None, display=True):
    """
    Visualize the optimized route with rack polygons overlaid.
    
    Args:
        locs: DataFrame with location data
        G: NetworkX graph
        route: Complete route with all waypoints
        pick_order: Sequence of pick locations
        start: Start location ID
        end: End location ID
        total_distance: Total route distance
        output_file: Optional path to save the figure
        display: Whether to display the plot window
    """
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Get rack polygons
    rack_polygons = get_rack_polygons(locs)
    rack_pairs = get_rack_pairs(locs)
    
    # Create color map for rack pairs
    pair_colors = plt.cm.tab20(np.linspace(0, 1, len(rack_pairs) * 2))
    rack_color_map = {}
    
    for i, (left_id, right_id, _, _) in enumerate(rack_pairs):
        rack_color_map[left_id] = pair_colors[i * 2]
        rack_color_map[right_id] = pair_colors[i * 2 + 1]
    
    # Draw rack polygons first (background)
    for rack_id, polygon in rack_polygons.items():
        poly_x = [p[0] for p in polygon]
        poly_y = [p[1] for p in polygon]
        
        # Determine color
        if rack_id in rack_color_map:
            color = rack_color_map[rack_id]
            alpha = 0.15
        else:
            color = 'lightgray'
            alpha = 0.1
        
        ax.fill(poly_x, poly_y, color=color, alpha=alpha, edgecolor='gray', linewidth=1.0)
    
    # Get positions
    pos = {row['id']: (row['x'], row['y']) for _, row in locs.iterrows()}
    
    # Draw route path
    route_coords = [pos[node] for node in route if node in pos]
    if len(route_coords) > 1:
        route_x = [p[0] for p in route_coords]
        route_y = [p[1] for p in route_coords]
        ax.plot(route_x, route_y, 'r-', linewidth=3, alpha=0.7, label='Route Path', zorder=4)
        
        # Add arrows to show direction
        for i in range(0, len(route_coords) - 1, max(1, len(route_coords) // 20)):
            dx = route_coords[i+1][0] - route_coords[i][0]
            dy = route_coords[i+1][1] - route_coords[i][1]
            ax.arrow(route_coords[i][0], route_coords[i][1], dx*0.3, dy*0.3,
                    head_width=3, head_length=2, fc='red', ec='red', alpha=0.6, zorder=5)
    
    # Draw all nodes (lighter)
    all_nodes = [row['id'] for _, row in locs.iterrows() if row['id'] in G.nodes()]
    all_pos = [pos[n] for n in all_nodes if n in pos]
    if len(all_pos) > 0:
        x = [p[0] for p in all_pos]
        y = [p[1] for p in all_pos]
        ax.scatter(x, y, c='lightgray', s=30, alpha=0.5, zorder=2)
    
    # Highlight pick locations
    pick_locs = [node for node in pick_order if node in pos]
    if len(pick_locs) > 0:
        pick_pos = [pos[node] for node in pick_locs]
        x = [p[0] for p in pick_pos]
        y = [p[1] for p in pick_pos]
        ax.scatter(x, y, c='green', s=150, marker='*', label='Pick Locations', 
                  zorder=6, edgecolors='forestgreen', linewidth=2)
        
        # Label pick sequence
        for i, node in enumerate(pick_locs, 1):
            ax.annotate(str(i), pos[node], fontsize=8, ha='center', va='center',
                       color='white', weight='bold', zorder=7)
    
    # Highlight start/end
    if start in pos:
        ax.scatter(*pos[start], c='blue', s=250, marker='D', label='Start', 
                  zorder=8, edgecolors='navy', linewidth=2)
    if end in pos and end != start:
        ax.scatter(*pos[end], c='purple', s=250, marker='s', label='End', 
                  zorder=8, edgecolors='indigo', linewidth=2)
    
    ax.set_xlabel('X Coordinate', fontsize=12)
    ax.set_ylabel('Y Coordinate', fontsize=12)
    ax.set_title(f'Optimized Route (Distance: {total_distance:.1f} units)', 
                fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved route visualization to: {output_file}")
    
    if display:
        plt.show()
    else:
        plt.close()
