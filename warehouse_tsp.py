#!/usr/bin/env python3
"""
Warehouse TSP Solver - Main Entry Point

Supports:
- Single-floor warehouses
- Multi-floor warehouses with configurable inter-floor penalties
- Two TSP strategies: unified graph or per-floor optimization

Usage:
    # Single floor
    python warehouse_tsp.py warehouse.json picks.txt
    
    # Multi-floor
    python warehouse_tsp.py --warehouse-layout floor1.json floor2.json floor3.json picks.txt
    
Arguments:
    warehouse_json    Path to warehouse layout JSON file (single floor mode)
    picks_file        Path to file with pick locations (one per line)
    
Multi-Floor Options:
    --warehouse-layout FILE1 FILE2 ...    Multiple JSON files, one per floor
    --inter-floor-penalty DISTANCE        Penalty for moving between floors (default: 1000)
    --multi-floor-strategy STRATEGY       'unified' or 'per-floor' (default: unified)
    --stairs FLOOR:ID ...                 Stair locations for inter-floor travel
    --elevators FLOOR:ID ...              Elevator locations for inter-floor travel
    --compare                             Compare both TSP strategies
    
Options:
    --start START     Starting location ID (default: first staging area)
    --end END         Ending location ID (default: same as start)
    --max-dist DIST   Maximum connection distance (default: 25)
    --visualize TYPE  Visualization: none, graph, route, both (default: route)
    --output PATH     Save visualization to file (default: output/warehouse_solution.png)
    --no-display      Don't show plot window, only save to file
    --stats           Show detailed statistics
"""

import argparse
import sys
from pathlib import Path
import json
import pandas as pd

# Import enhanced graph construction and visualization
from legacy.warehouse_graph_enhanced import (
    detect_aisles_with_dimensions,
    build_enhanced_graph,
    create_graph_from_edges,
    analyze_graph_quality
)

# Import physical warehouse loader for legacy format support
from physical.physical_layout import load_physical_warehouse
from legacy.routing import solve_tsp, calculate_route_distance
from legacy.visualization_enhanced import (
    visualize_graph_with_racks,
    visualize_route_with_racks
)
from legacy.multi_floor import MultiFloorWarehouse, compare_strategies

from cli_utils import load_picks_file


def detect_warehouse_format(filename):
    """Detect warehouse JSON format: 'simple' (x, y) or 'physical' (center, pick_points)"""
    with open(filename) as f:
        data = json.load(f)
    
    if not data or len(data) == 0:
        return 'simple'
    
    first_item = data[0]
    
    # Physical format has 'center' with x,y dict and optional 'pick_points'
    if 'center' in first_item and isinstance(first_item['center'], dict):
        return 'physical'
    
    # Simple format has direct 'x' and 'y' coordinates
    if 'x' in first_item and 'y' in first_item:
        return 'simple'
    
    # Default to simple
    return 'simple'


def load_warehouse_data(filename):
    """Load warehouse data from JSON file"""
    with open(filename) as f:
        data = json.load(f)
    return pd.DataFrame(data)


def find_default_start(locs):
    """Find a suitable default start location (staging area or first traversable)"""
    # Try staging areas first
    staging = locs[locs['type'] == 'staging']
    if len(staging) > 0:
        return staging.iloc[0]['id']
    
    # Fall back to first traversable location
    traversable = locs[locs['traversable'] == True]
    if len(traversable) > 0:
        return traversable.iloc[0]['id']
    
    # Last resort: first location
    return locs.iloc[0]['id']


def main():
    parser = argparse.ArgumentParser(
        description='Warehouse TSP Solver - Single or Multi-Floor Optimization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Positional arguments (for single-floor mode compatibility)
    parser.add_argument('warehouse_json', nargs='?', help='Path to warehouse layout JSON file (single floor)')
    parser.add_argument('picks_file', nargs='?', help='Path to file with pick locations (one per line)')
    
    # Multi-floor arguments
    parser.add_argument('--warehouse-layout', nargs='+', metavar='FILE',
                       help='Multiple JSON files for multi-floor warehouse (one per floor)')
    parser.add_argument('--inter-floor-penalty', type=float, default=1000.0,
                       help='Distance penalty for moving between floors (default: 1000)')
    parser.add_argument('--multi-floor-strategy', choices=['unified', 'per-floor', 'compare'],
                       default='unified', help='TSP strategy for multi-floor (default: unified)')
    parser.add_argument('--stairs', nargs='+', metavar='FLOOR:ID',
                       help='Stair locations: floor:location_id (e.g., 1:Stairs_A 2:Stairs_A)')
    parser.add_argument('--elevators', nargs='+', metavar='FLOOR:ID',
                       help='Elevator locations: floor:location_id (e.g., 1:Elevator_1 2:Elevator_1)')
    
    # General arguments
    parser.add_argument('--start', help='Starting location ID')
    parser.add_argument('--end', help='Ending location ID')
    parser.add_argument('--max-dist', type=float, default=25.0,
                       help='Maximum connection distance (default: 25)')
    parser.add_argument('--visualize', choices=['none', 'graph', 'route', 'both'],
                       default='route', help='Visualization type (default: route)')
    parser.add_argument('--output', help='Save visualization to file')
    parser.add_argument('--no-display', action='store_true',
                       help="Don't show plot window, only save to file")
    parser.add_argument('--stats', action='store_true',
                       help='Show detailed statistics')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Determine mode: multi-floor or single-floor
    is_multi_floor = args.warehouse_layout is not None
    
    if is_multi_floor:
        # Multi-floor mode: last argument should be picks file
        if args.picks_file:
            # picks_file was provided as positional arg
            picks_file = args.picks_file
            floor_files = args.warehouse_layout
        elif len(args.warehouse_layout) >= 2:
            # Last warehouse_layout arg is actually picks file
            picks_file = args.warehouse_layout[-1]
            floor_files = args.warehouse_layout[:-1]
        else:
            print("Error: Multi-floor mode requires at least 1 warehouse file and 1 picks file")
            print("Usage: --warehouse-layout floor1.json floor2.json picks.txt")
            sys.exit(1)
        
        # Validate files
        for floor_file in floor_files:
            if not Path(floor_file).exists():
                print(f"Error: Floor file not found: {floor_file}")
                sys.exit(1)
        
        if not Path(picks_file).exists():
            print(f"Error: Picks file not found: {picks_file}")
            sys.exit(1)
        
        # Run multi-floor optimization
        run_multi_floor(floor_files, picks_file, args)
    
    else:
        # Single-floor mode
        if not args.warehouse_json or not args.picks_file:
            print("Error: Single-floor mode requires warehouse_json and picks_file")
            print("Usage: python warehouse_tsp.py warehouse.json picks.txt")
            print("   or: python warehouse_tsp.py --warehouse-layout floor1.json floor2.json picks.txt")
            sys.exit(1)
        
        # Validate files
        if not Path(args.warehouse_json).exists():
            print(f"Error: Warehouse file not found: {args.warehouse_json}")
            sys.exit(1)
        
        if not Path(args.picks_file).exists():
            print(f"Error: Picks file not found: {args.picks_file}")
            sys.exit(1)
        
        # Run single-floor optimization
        run_single_floor(args.warehouse_json, args.picks_file, args)


def run_single_floor(warehouse_json, picks_file, args):
    """Run TSP optimization for single-floor warehouse."""
    print("="*70)
    print("WAREHOUSE TSP SOLVER - SINGLE FLOOR")
    print("="*70)
    
    # Detect warehouse format
    warehouse_format = detect_warehouse_format(warehouse_json)
    print(f"\nDetected format: {warehouse_format}")
    
    # Load warehouse data based on format
    print(f"Loading warehouse: {warehouse_json}")
    
    if warehouse_format == 'physical':
        # Use physical layout loader
        print("  Using physical layout loader...")
        G, warehouse_obj = load_physical_warehouse(warehouse_json)
        
        # Convert to DataFrame for compatibility
        all_nodes = []
        for node_id in G.nodes():
            node_data = G.nodes[node_id]
            all_nodes.append({
                'id': node_id,
                'x': node_data.get('x', 0),
                'y': node_data.get('y', 0),
                'type': node_data.get('type', 'picking'),
                'traversable': True  # All nodes in graph are traversable
            })
        locs = pd.DataFrame(all_nodes)
        print(f"  Loaded {len(locs)} locations from physical layout")
        
    else:
        # Use simple format loader
        print("  Using simple format loader...")
        locs = load_warehouse_data(warehouse_json)
        print(f"  Locations: {len(locs)}")
        
        # Build enhanced graph with rack inference
        print("\nBuilding enhanced graph with rack inference...")
        locs = detect_aisles_with_dimensions(locs, x_tolerance=5, y_tolerance=5, min_aisle_size=3)
        edges = build_enhanced_graph(locs, max_intra_aisle_dist=args.max_dist, 
                                     max_cross_aisle_dist=args.max_dist, 
                                     min_clearance=1.0, verbose=False)
        G = create_graph_from_edges(locs, edges)
    
    # Load picks
    print(f"\nLoading picks: {picks_file}")
    picks = load_picks_file(picks_file)
    print(f"  Found {len(picks)} pick locations")
    
    # Validate picks
    invalid = [p for p in picks if p not in locs['id'].values]
    if invalid:
        print(f"⚠ Warning: Invalid picks (not in warehouse): {invalid}")
        picks = [p for p in picks if p in locs['id'].values]
        print(f"  Continuing with {len(picks)} valid picks")
    
    # Analyze graph quality
    print("\n" + "-"*70)
    analyze_graph_quality(G, locs, verbose=True)
    print("-"*70)
    
    # Determine start/end
    start = args.start or find_default_start(locs)
    end = args.end or start
    
    print(f"\n  Start: {start}")
    print(f"  End: {end}")
    
    # Visualize graph only if requested
    if args.visualize in ['graph', 'both']:
        output = args.output or 'output/warehouse_graph.png'
        if args.visualize == 'both':
            output = output.replace('.png', '_graph.png')
        
        print(f"\nGenerating graph visualization...")
        visualize_graph_with_racks(locs, G, output_file=output, 
                                   title="Warehouse Graph with Detected Racks",
                                   display=not args.no_display)
    
    if args.visualize == 'graph':
        print("\nDone! (graph only, no TSP solving)")
        return
    
    # Solve TSP
    print(f"\nSolving TSP with Christofides algorithm...")
    
    # Build route with start location
    route_to_optimize = [start] + picks
    if end != start:
        route_to_optimize.append(end)
    
    best_order = solve_tsp(G, route_to_optimize, cycle=False, method='christofides')
    
    if not best_order:
        print("Error: Could not find valid route")
        sys.exit(1)
    
    # Calculate distance
    total_distance = calculate_route_distance(G, best_order)
    
    # Extract pick order (exclude start/end waypoints)
    pick_order = [loc for loc in best_order if loc in picks]
    
    # Print results
    print("\n" + "="*70)
    print("SOLUTION")
    print("="*70)
    print(f"\nPick sequence: {' -> '.join(pick_order)}")
    print(f"Total distance: {total_distance:.2f} units")
    print(f"Total waypoints: {len(best_order)} nodes")
    print(f"Number of picks: {len(pick_order)}")
    
    # Show statistics if requested
    if args.stats:
        print("\n" + "-"*70)
        print("DETAILED STATISTICS")
        print("-"*70)
        
        # Zone distribution (if zones are available)
        if 'zone' in locs.columns:
            zone_counts = {}
            for loc in pick_order:
                zone = locs[locs['id'] == loc].iloc[0]['zone']
                zone_counts[zone] = zone_counts.get(zone, 0) + 1
            
            print("\nZone Distribution:")
            for zone, count in sorted(zone_counts.items()):
                print(f"  Zone {zone}: {count} picks")
        
        # Segment analysis
        print("\nRoute Segments:")
        for i in range(min(10, len(best_order) - 1)):  # Show first 10 segments
            from_loc = best_order[i]
            to_loc = best_order[i + 1]
            segment_dist = calculate_route_distance(G, [from_loc, to_loc])
            print(f"  {from_loc:15s} -> {to_loc:15s}  {segment_dist:6.1f} units")
        
        if len(best_order) > 11:
            print(f"  ... ({len(best_order) - 11} more segments)")
    
    # Visualize route if requested
    if args.visualize in ['route', 'both']:
        output = args.output or 'output/warehouse_solution.png'
        if args.visualize == 'both':
            output = output.replace('.png', '_route.png')
        
        print(f"\nGenerating route visualization...")
        visualize_route_with_racks(locs, G, best_order, pick_order, start, end, 
                                   total_distance, output_file=output,
                                   display=not args.no_display)
    
    print("\n" + "="*70)
    print("DONE!")
    print("="*70)


def run_multi_floor(floor_files, picks_file, args):
    """Run TSP optimization for multi-floor warehouse."""
    print("="*70)
    print("WAREHOUSE TSP SOLVER - MULTI-FLOOR")
    print("="*70)
    
    # Parse stair and elevator locations
    stairs = []
    elevators = []
    
    if args.stairs:
        for stair_spec in args.stairs:
            try:
                floor, loc_id = stair_spec.split(':')
                stairs.append((int(floor), loc_id))
            except ValueError:
                print(f"⚠ Warning: Invalid stair spec '{stair_spec}', expected FLOOR:ID")
    
    if args.elevators:
        for elev_spec in args.elevators:
            try:
                floor, loc_id = elev_spec.split(':')
                elevators.append((int(floor), loc_id))
            except ValueError:
                print(f"⚠ Warning: Invalid elevator spec '{elev_spec}', expected FLOOR:ID")
    
    # Create multi-floor warehouse
    warehouse = MultiFloorWarehouse(floor_files, inter_floor_penalty=args.inter_floor_penalty)
    
    # Load picks
    print(f"\nLoading picks: {picks_file}")
    picks = load_picks_file(picks_file)
    print(f"  Found {len(picks)} pick locations")
    
    # Build graphs
    warehouse.build_per_floor_graphs(max_intra_aisle_dist=args.max_dist,
                                     max_cross_aisle_dist=args.max_dist,
                                     min_clearance=1.0)
    
    # Build unified graph if needed
    if args.multi_floor_strategy in ['unified', 'compare']:
        warehouse.build_unified_graph(stair_locations=stairs or None,
                                     elevator_locations=elevators or None)
    
    # Solve TSP based on strategy
    if args.multi_floor_strategy == 'compare':
        # Compare both strategies
        results = compare_strategies(warehouse, picks, args.start, args.end)
        
        # Use unified for visualization
        route = results['unified']['route']
        total_distance = results['unified']['distance']
        pick_order = results['unified']['picks']
        transitions = results['unified']['transitions']
        locs = warehouse.get_floor_locations()
        G = warehouse.unified_graph
        
    elif args.multi_floor_strategy == 'unified':
        # Unified TSP
        route, total_distance, pick_order, transitions = warehouse.solve_unified_tsp(
            picks, args.start, args.end
        )
        locs = warehouse.get_floor_locations()
        G = warehouse.unified_graph
        
    else:  # per-floor
        # Per-floor TSP
        route, total_distance, pick_order, transitions = warehouse.solve_per_floor_tsp(
            picks, args.start, args.end, merge_strategy='sequential'
        )
        locs = warehouse.get_floor_locations()
        # For visualization, use unified graph if built, otherwise first floor
        G = warehouse.unified_graph if warehouse.unified_graph else warehouse.floor_graphs[1]
    
    if not route:
        print("Error: Could not find valid route")
        sys.exit(1)
    
    # Print floor transition summary
    print("\n" + "="*70)
    print("FLOOR TRANSITIONS")
    print("="*70)
    print(f"Number of floor changes: {transitions['num_transitions']}")
    print(f"Floors visited: {transitions['floors_visited']}")
    if transitions['transitions']:
        print("\nTransition sequence:")
        for from_floor, to_floor in transitions['transitions']:
            print(f"  Floor {from_floor} -> Floor {to_floor}")
    
    # Show statistics if requested
    if args.stats:
        print("\n" + "-"*70)
        print("DETAILED STATISTICS")
        print("-"*70)
        
        # Floor distribution
        floor_counts = {}
        for loc in pick_order:
            floor = int(loc.split('_')[0][1:]) if loc.startswith('F') else 1
            floor_counts[floor] = floor_counts.get(floor, 0) + 1
        
        print("\nFloor Distribution:")
        for floor, count in sorted(floor_counts.items()):
            print(f"  Floor {floor}: {count} picks")
        
        # Zone distribution per floor
        print("\nZone Distribution:")
        for floor_num in sorted(warehouse.floors.keys()):
            floor_locs = warehouse.floors[floor_num]
            floor_picks = [loc for loc in pick_order if loc.startswith(f'F{floor_num}_')]
            
            if len(floor_picks) > 0:
                zone_counts = {}
                for loc in floor_picks:
                    orig_id = loc.split('_', 1)[1]  # Remove F#_ prefix
                    matching = floor_locs[floor_locs['original_id'] == orig_id]
                    if len(matching) > 0:
                        zone = matching.iloc[0]['zone']
                        zone_counts[zone] = zone_counts.get(zone, 0) + 1
                
                print(f"  Floor {floor_num}:")
                for zone, count in sorted(zone_counts.items()):
                    print(f"    Zone {zone}: {count} picks")
    
    # Visualize if requested - create separate visualization per floor
    if args.visualize != 'none':
        print("\n" + "="*70)
        print("GENERATING PER-FLOOR VISUALIZATIONS")
        print("="*70)
        
        # Create visualization for each floor separately
        for floor_num in sorted(warehouse.floors.keys()):
            floor_locs = warehouse.floors[floor_num]
            floor_graph = warehouse.floor_graphs[floor_num]
            
            # Filter route to only include nodes on this floor
            floor_prefix = f'F{floor_num}_'
            floor_route = [node for node in route if node.startswith(floor_prefix)]
            floor_picks = [node for node in pick_order if node.startswith(floor_prefix)]
            
            # Determine start/end for this floor
            floor_start = floor_route[0] if floor_route else None
            floor_end = floor_route[-1] if floor_route else None
            
            # Calculate distance for this floor only
            floor_distance = 0
            if len(floor_route) > 1:
                for i in range(len(floor_route) - 1):
                    if floor_graph.has_edge(floor_route[i], floor_route[i+1]):
                        floor_distance += floor_graph[floor_route[i]][floor_route[i+1]]['weight']
            
            print(f"\nFloor {floor_num}:")
            print(f"  Nodes visited: {len(floor_route)}")
            print(f"  Picks: {len(floor_picks)}")
            print(f"  Distance: {floor_distance:.1f} units")
            
            # Graph visualization
            if args.visualize in ['graph', 'both']:
                graph_output = f'output/warehouse_graph_floor{floor_num}.png'
                print(f"  Generating graph visualization...")
                visualize_graph_with_racks(floor_locs, floor_graph, 
                                          output_file=graph_output,
                                          display=not args.no_display)
                print(f"  Saved: {graph_output}")
            
            # Route visualization
            if args.visualize in ['route', 'both'] and len(floor_route) > 0:
                route_output = f'output/warehouse_route_floor{floor_num}.png'
                print(f"  Generating route visualization...")
                visualize_route_with_racks(floor_locs, floor_graph, floor_route, 
                                          floor_picks, floor_start, floor_end,
                                          floor_distance, output_file=route_output,
                                          display=not args.no_display)
                print(f"  Saved: {route_output}")
    
    print("\n" + "="*70)
    print("DONE!")
    print("="*70)


if __name__ == '__main__':
    main()

