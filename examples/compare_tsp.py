#!/usr/bin/env python3
"""
Compare different TSP algorithms on the same pick route
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from physical.physical_layout import load_physical_warehouse
from physical.routing import solve_tsp_with_endpoints


def load_picks(picks_file):
    """Load picks from file"""
    picks = []
    with open(picks_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                picks.append(line)
    return picks


def compare_methods(warehouse_json, picks_file, max_dist=50):
    """Compare different TSP methods"""
    print("Loading warehouse and picks...")
    graph, warehouse = load_physical_warehouse(warehouse_json)
    graph = warehouse.build_graph(max_connection_dist=max_dist)
    picks = load_picks(picks_file)
    
    # Find start/end
    start = end = None
    for obj in warehouse.traversable_areas:
        if obj.type in ['staging', 'dock']:
            start = end = obj.id
            break
    
    if not start:
        start = end = warehouse.traversable_areas[0].id
    
    print(f"Warehouse: {warehouse_json}")
    print(f"Picks: {len(picks)}")
    print(f"Start/End: {start}")
    print(f"\n{'='*70}")
    print("COMPARING METHODS")
    print('='*70)
    
    methods = ['greedy', '2-opt']
    if len(picks) <= 10:
        methods.append('exhaustive')
    
    results = {}
    for method in methods:
        print(f"\n{method.upper()}:")
        route, distance, order = solve_tsp_with_endpoints(graph, start, picks, end, method=method)
        results[method] = {
            'route': route,
            'distance': distance,
            'order': order
        }
        print(f"  Distance: {distance:.2f} units")
        print(f"  Waypoints: {len(route)} nodes")
    
    # Find best
    best_method = min(results.keys(), key=lambda m: results[m]['distance'])
    best_distance = results[best_method]['distance']
    
    print(f"\n{'='*70}")
    print("COMPARISON")
    print('='*70)
    for method in methods:
        distance = results[method]['distance']
        diff = distance - best_distance
        marker = " ← BEST" if method == best_method else f" (+{diff:.2f} units)"
        print(f"{method:>12}: {distance:>10.2f} units{marker}")
    
    print(f"\n{'='*70}")
    print(f"BEST METHOD: {best_method.upper()}")
    print(f"Pick sequence: {' → '.join(results[best_method]['order'])}")
    print('='*70)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python compare_tsp.py <warehouse_json> <picks_file> [max_dist]")
        sys.exit(1)
    
    warehouse_json = sys.argv[1]
    picks_file = sys.argv[2]
    max_dist = float(sys.argv[3]) if len(sys.argv) > 3 else 50.0
    
    compare_methods(warehouse_json, picks_file, max_dist)
