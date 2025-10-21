#!/usr/bin/env python3
"""
Warehouse TSP Solver - Main Entry Point

Usage:
    python warehouse_tsp.py <warehouse_json> <picks_file> [options]

Arguments:
    warehouse_json    Path to warehouse layout JSON file
    picks_file        Path to file with pick locations (one per line)
    
Options:
    --start START     Starting location ID (default: first traversable area)
    --end END         Ending location ID (default: same as start)
    --method METHOD   TSP algorithm: greedy, 2-opt, exhaustive (default: 2-opt)
    --max-dist DIST   Maximum connection distance (default: 30)
    --visualize TYPE  Visualization: none, graph, route, both (default: route)
    --output PATH     Save visualization to file (default: warehouse_solution.png)
    --no-display      Don't show plot window, only save to file
    --stats           Show detailed statistics
    
Examples:
    # Basic usage with 2-opt algorithm
    python warehouse_tsp.py warehouse_large.json picks.txt
    
    # Use greedy algorithm with custom start/end
    python warehouse_tsp.py warehouse_large.json picks.txt --start Staging_Area_West --end Charging_Station_1 --method greedy
    
    # Visualize full graph without solving
    python warehouse_tsp.py warehouse_large.json picks.txt --visualize graph --no-display
    
    # Get detailed statistics only
    python warehouse_tsp.py warehouse_large.json picks.txt --visualize none --stats
"""

import argparse
import sys
import math
import json
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx

from physical.physical_layout import load_physical_warehouse
from physical.routing import solve_tsp_with_endpoints
from physical.physical_visualization import visualize_physical_warehouse


def detect_warehouse_format(json_file):
    """
    Detect whether warehouse JSON is physical format or legacy format.
    
    Returns:
        'physical' if it has objects with center/width/depth
        'legacy' if it has locations with x/y coordinates
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Physical format has "objects" array with items having "center", "width", "depth"
        if 'objects' in data and len(data['objects']) > 0:
            first_obj = data['objects'][0]
            if 'center' in first_obj and 'width' in first_obj and 'depth' in first_obj:
                return 'physical'
        
        # Legacy format: array of objects with "x", "y" coordinates
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if 'x' in first_item and 'y' in first_item:
                return 'legacy'
        
        # Legacy format might also have "locations" key
        if 'locations' in data and len(data['locations']) > 0:
            first_loc = data['locations'][0]
            if 'x' in first_loc and 'y' in first_loc:
                return 'legacy'
        
        # Default to physical if can't determine
        return 'physical'
    except Exception as e:
        print(f"Warning: Could not detect format: {e}")
        return 'physical'


def load_picks_file(picks_file):
    """Load pick locations from file (one ID per line, # for comments)"""
    picks = []
    try:
        with open(picks_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    picks.append(line)
    except FileNotFoundError:
        print(f"Error: Picks file not found: {picks_file}")
        sys.exit(1)
    
    return picks


def find_default_start_end(warehouse):
    """Find default start/end points (first traversable area)"""
    for obj in warehouse.traversable_areas:
        if obj.type in ['staging', 'dock']:
            return obj.id
    # Fallback to any traversable area
    if warehouse.traversable_areas:
        return warehouse.traversable_areas[0].id
    return None


def find_default_start_end_legacy(graph):
    """Find default start/end points for legacy format (first node)"""
    if graph.number_of_nodes() > 0:
        return list(graph.nodes())[0]
    return None


def load_warehouse_legacy(json_file, max_dist):
    """Load legacy coordinate-based warehouse"""
    import pandas as pd
    from legacy.warehouse_graph import detect_aisles, build_aisle_graph, create_graph_from_edges
    
    # Load location data
    with open(json_file) as f:
        locs = pd.DataFrame(json.load(f))
    
    # Detect aisle structures
    locs = detect_aisles(locs, x_tolerance=3, y_tolerance=3, min_aisle_size=3)
    
    # Build graph
    edges = build_aisle_graph(
        locs,
        max_intra_aisle_dist=max_dist if max_dist > 20 else 20,
        max_cross_aisle_dist=15,
        only_connect_intersections=True,
        prevent_cross_aisle_shortcuts=True,
        verbose=False
    )
    
    graph = create_graph_from_edges(locs, edges)
    return graph, None  # No warehouse object for legacy format


def print_statistics_legacy(graph, route, total_distance, pick_order, start, end):
    """Print detailed statistics for legacy format"""
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    
    print(f"\nGraph:")
    print(f"  Nodes: {graph.number_of_nodes()}")
    print(f"  Edges: {graph.number_of_edges()}")
    components = list(nx.connected_components(graph))
    print(f"  Connected: {'Yes' if len(components) == 1 else f'No ({len(components)} components)'}")
    
    print(f"\nRoute:")
    print(f"  Start: {start}")
    print(f"  End: {end}")
    print(f"  Picks: {len(pick_order)}")
    print(f"  Total waypoints: {len(route)}")
    print(f"  Total distance: {total_distance:.2f} units")
    print(f"  Average per pick: {total_distance / len(pick_order):.2f} units")
    
    print("\n" + "="*70)


def print_statistics(graph, warehouse, route, total_distance, pick_order, start, end):
    """Print detailed statistics about the solution"""
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    
    # Warehouse stats
    racks = [obj for obj in warehouse.objects if obj.type == 'rack']
    aisles = [obj for obj in warehouse.objects if obj.type == 'aisle']
    pick_points = [n for n in graph.nodes if '-' in n]
    
    print(f"\nWarehouse:")
    print(f"  Objects: {len(warehouse.objects)}")
    print(f"  Racks: {len(racks)}")
    print(f"  Aisles: {len(aisles)}")
    print(f"  Total pick points: {len(pick_points)}")
    
    print(f"\nGraph:")
    print(f"  Nodes: {graph.number_of_nodes()}")
    print(f"  Edges: {graph.number_of_edges()}")
    components = list(nx.connected_components(graph))
    print(f"  Connected: {'Yes' if len(components) == 1 else f'No ({len(components)} components)'}")
    
    print(f"\nRoute:")
    print(f"  Start: {start}")
    print(f"  End: {end}")
    print(f"  Picks: {len(pick_order)}")
    print(f"  Total waypoints: {len(route)}")
    print(f"  Total distance: {total_distance:.2f} units")
    print(f"  Average per pick: {total_distance / len(pick_order):.2f} units")
    
    # Rack distribution
    from collections import Counter
    rack_dist = Counter([p.split('-')[0] for p in pick_order if '-' in p])
    print(f"\nPicks by rack:")
    for rack, count in sorted(rack_dist.items()):
        print(f"  {rack}: {count}")
    
    print("\n" + "="*70)


def visualize_graph_only_legacy(graph, output_path, display=True):
    """Visualize legacy warehouse graph"""
    from legacy.visualization import visualize_warehouse_graph
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


def visualize_route_legacy(graph, route, pick_order, start, end, total_distance, 
                           output_path, display=True):
    """Visualize the optimized route for legacy warehouse"""
    plt.figure(figsize=(20, 18))
    pos = {n: (graph.nodes[n]['x'], graph.nodes[n]['y']) for n in graph.nodes}
    
    # Color nodes by vertical aisle
    v_aisle_colors = [graph.nodes[n].get('v_aisle', -1) for n in graph.nodes]
    node_colors = ['lightgray' if v == -1 else plt.cm.tab20(v % 20) for v in v_aisle_colors]
    
    # Draw all edges in light gray
    nx.draw_networkx_edges(graph, pos, alpha=0.1, width=0.5, edge_color='gray')
    
    # Draw all nodes
    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=200, alpha=0.3,
                          edgecolors='gray', linewidths=0.5)
    
    # Draw route path
    route_edges = []
    for i in range(len(route) - 1):
        if graph.has_edge(route[i], route[i+1]):
            route_edges.append((route[i], route[i+1]))
    
    nx.draw_networkx_edges(graph, pos, edgelist=route_edges,
                          edge_color='red', width=4, alpha=0.8,
                          arrows=True, arrowsize=20, arrowstyle='->')
    
    # Highlight picks with numbers
    pick_positions = {p: pos[p] for p in pick_order if p in pos}
    if pick_positions:
        nx.draw_networkx_nodes(graph, pick_positions, nodelist=list(pick_positions.keys()),
                              node_color='yellow', node_size=600,
                              edgecolors='red', linewidths=3)
        
        # Track duplicate locations for offsetting
        location_counts = {}
        
        for i, pick in enumerate(pick_order, 1):
            if pick in pos:
                x, y = pos[pick]
                
                # Handle duplicate locations by offsetting labels
                location_key = (x, y)
                if location_key in location_counts:
                    offset_angle = location_counts[location_key] * (2 * math.pi / 4)
                    offset_dist = 3.0
                    x_offset = x + offset_dist * math.cos(offset_angle)
                    y_offset = y + offset_dist * math.sin(offset_angle)
                    location_counts[location_key] += 1
                else:
                    x_offset, y_offset = x, y
                    location_counts[location_key] = 1
                
                plt.text(x_offset, y_offset, str(i), fontsize=11, fontweight='bold',
                        ha='center', va='center', color='black',
                        bbox=dict(boxstyle='circle', facecolor='yellow',
                                edgecolor='red', linewidth=2))
    
    # Highlight start and end
    if start in pos:
        x, y = pos[start]
        plt.scatter([x], [y], c='green', s=800, marker='*',
                   edgecolors='darkgreen', linewidths=3, zorder=10, label='Start')
    
    if end in pos and end != start:
        x, y = pos[end]
        plt.scatter([x], [y], c='blue', s=800, marker='*',
                   edgecolors='darkblue', linewidths=3, zorder=10, label='End')
    
    plt.title(f'Legacy Warehouse - Optimized Pick Route\n'
             f'{len(pick_order)} picks, Distance: {total_distance:.2f} units',
             fontsize=16, fontweight='bold')
    plt.legend(fontsize=12, loc='upper right')
    plt.axis('equal')
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Route visualization saved to: {output_path}")
    
    if display:
        plt.show()
    else:
        plt.close()


def visualize_graph_only(warehouse, graph, output_path, display=True):
    """Visualize just the warehouse graph"""
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


def visualize_route(warehouse, graph, route, pick_order, start, end, total_distance, 
                    output_path, display=True):
    """Visualize the optimized route"""
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
        
        # Track how many times we've drawn at each location (for duplicates)
        location_counts = {}
        
        for i, pick in enumerate(pick_order, 1):
            if pick in pos:
                x, y = pos[pick]
                
                # Handle duplicate locations by offsetting labels
                location_key = (x, y)
                if location_key in location_counts:
                    # Offset subsequent labels in a circle pattern
                    offset_angle = location_counts[location_key] * (2 * math.pi / 4)  # Up to 4 duplicates
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


def main():
    parser = argparse.ArgumentParser(
        description='Warehouse TSP Solver - Optimize pick routes in physical warehouses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('warehouse_json', help='Path to warehouse layout JSON file')
    parser.add_argument('picks_file', help='Path to file with pick locations (one per line)')
    parser.add_argument('--start', help='Starting location ID')
    parser.add_argument('--end', help='Ending location ID')
    parser.add_argument('--method', choices=['greedy', '2-opt', 'exhaustive'], 
                       default='2-opt', help='TSP algorithm (default: 2-opt)')
    parser.add_argument('--max-dist', type=float, default=30.0,
                       help='Maximum connection distance (default: 30)')
    parser.add_argument('--visualize', choices=['none', 'graph', 'route', 'both'],
                       default='route', help='Visualization type (default: route)')
    parser.add_argument('--output', help='Save visualization to file (default: output/warehouse_solution.png)')
    parser.add_argument('--no-display', action='store_true',
                       help="Don't show plot window, only save to file")
    parser.add_argument('--stats', action='store_true',
                       help='Show detailed statistics')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Validate files exist
    if not Path(args.warehouse_json).exists():
        print(f"Error: Warehouse file not found: {args.warehouse_json}")
        sys.exit(1)
    
    if not Path(args.picks_file).exists():
        print(f"Error: Picks file not found: {args.picks_file}")
        sys.exit(1)
    
    print("="*70)
    print("WAREHOUSE TSP SOLVER")
    print("="*70)
    
    # Detect warehouse format
    warehouse_format = detect_warehouse_format(args.warehouse_json)
    print(f"\nDetected format: {warehouse_format}")
    
    # Load warehouse based on format
    print(f"Loading warehouse: {args.warehouse_json}")
    
    if warehouse_format == 'legacy':
        print("⚠️  Using legacy coordinate-based system")
        graph, warehouse = load_warehouse_legacy(args.warehouse_json, args.max_dist)
    else:
        graph, warehouse = load_physical_warehouse(args.warehouse_json)
        
        # Rebuild with custom max distance if specified
        if args.max_dist != 30.0:
            print(f"Rebuilding graph with max_connection_dist={args.max_dist}")
            graph = warehouse.build_graph(max_connection_dist=args.max_dist)
    
    # Load picks
    print(f"Loading picks: {args.picks_file}")
    picks = load_picks_file(args.picks_file)
    print(f"  Found {len(picks)} pick locations")
    
    # Determine start/end based on format
    if warehouse_format == 'legacy':
        start = args.start or find_default_start_end_legacy(graph)
        end = args.end or start
    else:
        start = args.start or find_default_start_end(warehouse)
        end = args.end or start
    
    if not start:
        print("Error: Could not determine start location")
        sys.exit(1)
    
    print(f"  Start: {start}")
    print(f"  End: {end}")
    
    # Visualize graph only if requested
    if args.visualize in ['graph', 'both']:
        output = args.output or 'output/warehouse_graph.png'
        if args.visualize == 'both':
            output = output.replace('.png', '_graph.png')
        
        if warehouse_format == 'legacy':
            visualize_graph_only_legacy(graph, output, display=not args.no_display)
        else:
            visualize_graph_only(warehouse, graph, output, display=not args.no_display)
    
    if args.visualize == 'graph':
        print("\nDone! (graph only, no TSP solving)")
        return
    
    # Solve TSP
    print(f"\nSolving TSP with {args.method} algorithm...")
    route, total_distance, pick_order = solve_tsp_with_endpoints(
        graph, start, picks, end, method=args.method
    )
    
    if not route:
        print("Error: Could not find valid route")
        sys.exit(1)
    
    # Print results
    print("\n" + "="*70)
    print("SOLUTION")
    print("="*70)
    print(f"\nPick sequence: {' → '.join(pick_order)}")
    print(f"Total distance: {total_distance:.2f} units")
    print(f"Total waypoints: {len(route)} nodes")
    
    # Show statistics if requested
    if args.stats:
        if warehouse_format == 'legacy':
            print_statistics_legacy(graph, route, total_distance, pick_order, start, end)
        else:
            print_statistics(graph, warehouse, route, total_distance, pick_order, start, end)
    
    # Visualize route if requested
    if args.visualize in ['route', 'both']:
        output = args.output or 'output/warehouse_solution.png'
        if args.visualize == 'both':
            output = output.replace('.png', '_route.png')
        
        if warehouse_format == 'legacy':
            visualize_route_legacy(graph, route, pick_order, start, end,
                                  total_distance, output, display=not args.no_display)
        else:
            visualize_route(warehouse, graph, route, pick_order, start, end, 
                           total_distance, output, display=not args.no_display)
    
    print("\n" + "="*70)
    print("DONE!")
    print("="*70)


if __name__ == '__main__':
    main()
