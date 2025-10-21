"""
CLI Utilities for Warehouse TSP

Helper functions for file loading, format detection, and default value finding.
"""

import json
import sys


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
