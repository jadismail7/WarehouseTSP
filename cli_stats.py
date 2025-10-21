"""
CLI Statistics Display

Functions for printing detailed statistics about warehouses, graphs, and routes.
"""

import networkx as nx
from collections import Counter


def print_statistics(graph, warehouse, route, total_distance, pick_order, start, end):
    """Print detailed statistics about the solution (physical format)"""
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
    rack_dist = Counter([p.split('-')[0] for p in pick_order if '-' in p])
    print(f"\nPicks by rack:")
    for rack, count in sorted(rack_dist.items()):
        print(f"  {rack}: {count}")
    
    print("\n" + "="*70)


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
    if len(pick_order) > 0:
        print(f"  Average per pick: {total_distance / len(pick_order):.2f} units")
    
    print("\n" + "="*70)
