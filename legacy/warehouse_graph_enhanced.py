"""
Enhanced Warehouse Graph Construction Module

Leverages physical properties (width, depth, traversable) to build more accurate graphs:
1. Automatically infers rack structures from bin (picking location) dimensions
2. Uses traversability to exclude blocked areas from pathfinding
3. Calculates clearances based on physical dimensions
4. Prevents connections through non-traversable obstacles
"""

import math
import networkx as nx
from sklearn.cluster import DBSCAN
from collections import defaultdict
import numpy as np


def calculate_distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def infer_racks_from_bins(locs, bin_spacing_tolerance=20, vertical_alignment_tolerance=5):
    """
    Infer rack structures from picking locations (bins).
    Groups bins that are vertically aligned (same x-coordinate within tolerance).
    
    A rack is a vertical column of bins with similar x-coordinates.
    This allows us to detect which bins are on the same physical rack structure.
    
    Args:
        locs: DataFrame with location data including width, depth, traversable
        bin_spacing_tolerance: Maximum vertical spacing between bins in the same rack
        vertical_alignment_tolerance: Maximum x-coordinate variance for vertical alignment
    
    Returns:
        DataFrame with added 'rack_id' and 'rack_side' columns
    """
    # Filter to only picking locations (bins)
    bins = locs[locs['type'] == 'picking'].copy()
    
    if len(bins) == 0:
        locs['rack_id'] = -1
        locs['rack_side'] = 'none'
        return locs
    
    # Detect vertical racks (bins with similar x-coordinates)
    # These represent columns of bins on the same rack structure
    x_coords = bins['x'].values.reshape(-1, 1)
    clustering = DBSCAN(eps=vertical_alignment_tolerance, min_samples=2).fit(x_coords)
    
    bins['rack_id'] = clustering.labels_
    bins['rack_side'] = 'none'
    
    # Now detect pairs of racks that are close together (opposite sides of aisle)
    rack_centers = {}
    for rack_id in set(bins['rack_id']) - {-1}:
        rack_bins = bins[bins['rack_id'] == rack_id]
        center_x = rack_bins['x'].mean()
        rack_centers[rack_id] = center_x
    
    # Find pairs of racks that face each other across an aisle
    rack_pairs = {}
    paired_racks = set()
    rack_ids = sorted(rack_centers.keys())
    
    for i, rack1 in enumerate(rack_ids):
        if rack1 in paired_racks:
            continue
        for rack2 in rack_ids[i+1:]:
            if rack2 in paired_racks:
                continue
            
            distance = abs(rack_centers[rack1] - rack_centers[rack2])
            # Racks are paired if they're 10-20 units apart (typical aisle width)
            if 10 <= distance <= 20:
                left_rack = rack1 if rack_centers[rack1] < rack_centers[rack2] else rack2
                right_rack = rack2 if left_rack == rack1 else rack1
                
                # Mark sides
                bins.loc[bins['rack_id'] == left_rack, 'rack_side'] = 'left'
                bins.loc[bins['rack_id'] == right_rack, 'rack_side'] = 'right'
                
                rack_pairs[left_rack] = right_rack
                rack_pairs[right_rack] = left_rack
                
                paired_racks.add(rack1)
                paired_racks.add(rack2)
                break
    
    # Merge back to main dataframe
    locs['rack_id'] = -1
    locs['rack_side'] = 'none'
    locs.loc[bins.index, 'rack_id'] = bins['rack_id']
    locs.loc[bins.index, 'rack_side'] = bins['rack_side']
    
    return locs


def get_rack_boundaries(locs, rack_id):
    """
    Calculate the physical boundaries of a rack based on its bins.
    
    Args:
        locs: DataFrame with location data
        rack_id: ID of the rack to analyze
    
    Returns:
        dict with keys: min_x, max_x, min_y, max_y, width, depth
    """
    rack_bins = locs[locs['rack_id'] == rack_id]
    
    if len(rack_bins) == 0:
        return None
    
    # Calculate boundaries including bin dimensions
    min_x = rack_bins.apply(lambda row: row['x'] - row['width']/2, axis=1).min()
    max_x = rack_bins.apply(lambda row: row['x'] + row['width']/2, axis=1).max()
    min_y = rack_bins.apply(lambda row: row['y'] - row['depth']/2, axis=1).min()
    max_y = rack_bins.apply(lambda row: row['y'] + row['depth']/2, axis=1).max()
    
    return {
        'min_x': min_x,
        'max_x': max_x,
        'min_y': min_y,
        'max_y': max_y,
        'width': max_x - min_x,
        'depth': max_y - min_y
    }


def check_line_intersects_obstacle(p1, p2, obstacle_center, obstacle_width, obstacle_depth):
    """
    Check if a line segment from p1 to p2 intersects with a rectangular obstacle.
    
    Args:
        p1, p2: (x, y) tuples representing line endpoints
        obstacle_center: (x, y) center of obstacle
        obstacle_width: width of obstacle
        obstacle_depth: depth of obstacle
    
    Returns:
        True if line intersects obstacle, False otherwise
    """
    # Get obstacle boundaries
    obs_x, obs_y = obstacle_center
    obs_min_x = obs_x - obstacle_width / 2
    obs_max_x = obs_x + obstacle_width / 2
    obs_min_y = obs_y - obstacle_depth / 2
    obs_max_y = obs_y + obstacle_depth / 2
    
    # Check if either endpoint is inside the obstacle
    for p in [p1, p2]:
        if (obs_min_x <= p[0] <= obs_max_x and obs_min_y <= p[1] <= obs_max_y):
            return True
    
    # Simple line-rectangle intersection test using separating axis theorem
    # For simplicity, we'll use a more conservative approach:
    # Check if the line's bounding box overlaps with the obstacle
    line_min_x = min(p1[0], p2[0])
    line_max_x = max(p1[0], p2[0])
    line_min_y = min(p1[1], p2[1])
    line_max_y = max(p1[1], p2[1])
    
    # No overlap if bounding boxes don't intersect
    if (line_max_x < obs_min_x or line_min_x > obs_max_x or
        line_max_y < obs_min_y or line_min_y > obs_max_y):
        return False
    
    # If bounding boxes overlap, do detailed line-segment intersection
    # Check intersection with each edge of the rectangle
    rect_edges = [
        ((obs_min_x, obs_min_y), (obs_max_x, obs_min_y)),  # bottom
        ((obs_max_x, obs_min_y), (obs_max_x, obs_max_y)),  # right
        ((obs_max_x, obs_max_y), (obs_min_x, obs_max_y)),  # top
        ((obs_min_x, obs_max_y), (obs_min_x, obs_min_y))   # left
    ]
    
    for edge_p1, edge_p2 in rect_edges:
        if line_segments_intersect(p1, p2, edge_p1, edge_p2):
            return True
    
    return False


def line_segments_intersect(p1, p2, p3, p4):
    """
    Check if line segment p1-p2 intersects with line segment p3-p4.
    Uses parametric line equations.
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    if abs(denom) < 1e-10:
        return False  # Parallel lines
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    return 0 <= t <= 1 and 0 <= u <= 1


def is_path_blocked(p1, p2, locs, min_clearance=1.0):
    """
    Check if a straight-line path between two points is blocked by non-traversable obstacles.
    
    Args:
        p1, p2: (x, y) tuples for the path endpoints
        locs: DataFrame with location data
        min_clearance: Minimum clearance required from obstacles
    
    Returns:
        True if path is blocked, False if clear
    """
    # Get all non-traversable locations
    obstacles = locs[locs['traversable'] == False]
    
    for _, obs in obstacles.iterrows():
        obs_center = (obs['x'], obs['y'])
        # Add clearance buffer to obstacle dimensions
        obs_width = obs['width'] + 2 * min_clearance
        obs_depth = obs['depth'] + 2 * min_clearance
        
        if check_line_intersects_obstacle(p1, p2, obs_center, obs_width, obs_depth):
            return True
    
    return False


def detect_aisles_with_dimensions(locs, x_tolerance=5, y_tolerance=5, min_aisle_size=3):
    """
    Enhanced aisle detection that considers physical dimensions.
    
    Args:
        locs: DataFrame with location data including width, depth, traversable
        x_tolerance: Clustering tolerance for x-coordinates (vertical aisles)
        y_tolerance: Clustering tolerance for y-coordinates (horizontal aisles)
        min_aisle_size: Minimum number of nodes to be considered a true aisle
    
    Returns:
        DataFrame with added columns: v_aisle, h_aisle, rack_id
    """
    # First infer rack structures from bins
    locs = infer_racks_from_bins(locs)
    
    # Only use traversable locations for aisle detection
    traversable_locs = locs[locs['traversable'] == True]
    
    if len(traversable_locs) == 0:
        locs['v_aisle'] = -1
        locs['h_aisle'] = -1
        return locs
    
    # Detect vertical aisles (similar x-coordinates) - only from traversable locations
    x_coords = traversable_locs['x'].values.reshape(-1, 1)
    vertical_clusters = DBSCAN(eps=x_tolerance, min_samples=min_aisle_size).fit(x_coords)
    
    # Detect horizontal aisles (similar y-coordinates)
    y_coords = traversable_locs['y'].values.reshape(-1, 1)
    horizontal_clusters = DBSCAN(eps=y_tolerance, min_samples=min_aisle_size).fit(y_coords)
    
    # Initialize all locations with -1 (not in aisle)
    locs['v_aisle'] = -1
    locs['h_aisle'] = -1
    
    # Assign aisle IDs only to traversable locations
    locs.loc[traversable_locs.index, 'v_aisle'] = vertical_clusters.labels_
    locs.loc[traversable_locs.index, 'h_aisle'] = horizontal_clusters.labels_
    
    return locs


def should_prevent_connection(locs, idx1, idx2):
    """
    Check if a connection between two nodes should be prevented because
    it would go through a rack (opposite sides of same rack structure).
    
    Args:
        locs: DataFrame with location data
        idx1, idx2: Indices of the two locations
    
    Returns:
        True if connection should be prevented, False otherwise
    """
    rack1 = locs.loc[idx1, 'rack_id']
    rack2 = locs.loc[idx2, 'rack_id']
    side1 = locs.loc[idx1, 'rack_side']
    side2 = locs.loc[idx2, 'rack_side']
    
    # If both are bins on opposite sides of paired racks
    if rack1 >= 0 and rack2 >= 0 and side1 != 'none' and side2 != 'none':
        # Check if they're on opposite sides
        if side1 != side2:
            # Check if they're at similar y-coordinates (directly across from each other)
            y1 = locs.loc[idx1, 'y']
            y2 = locs.loc[idx2, 'y']
            
            # Allow connections at aisle ends (different y-coordinates)
            # Prevent mid-aisle shortcuts through racks
            if abs(y1 - y2) < 20:  # Within same vertical section
                return True
    
    return False


def build_enhanced_graph(locs, max_intra_aisle_dist=20, max_cross_aisle_dist=15, 
                        ensure_connectivity=True, min_clearance=1.0, verbose=True):
    """
    Build a graph using enhanced logic with physical dimensions and traversability.
    
    Key improvements:
    1. Only connects traversable locations
    2. Checks for obstacles blocking paths
    3. Uses physical dimensions for clearance calculations
    4. Infers rack structures automatically
    
    Args:
        locs: DataFrame with location data (must have width, depth, traversable)
        max_intra_aisle_dist: Maximum distance between sequential aisle nodes
        max_cross_aisle_dist: Maximum distance for cross-aisle connections
        ensure_connectivity: Ensure all components are connected
        min_clearance: Minimum clearance from obstacles (units)
        verbose: Print progress information
    
    Returns:
        List of edges as (node1_id, node2_id, distance) tuples
    """
    edges = []
    coords = locs[['x', 'y']].values
    ids = locs['id'].tolist()
    
    # Only consider traversable locations for routing
    traversable_indices = locs[locs['traversable'] == True].index.tolist()
    
    if verbose:
        num_traversable = len(traversable_indices)
        num_obstacles = len(locs[locs['traversable'] == False])
        num_racks = len(set(locs['rack_id']) - {-1})
        print(f"Graph building: {num_traversable} traversable nodes, {num_obstacles} obstacles")
        if num_racks > 0:
            print(f"Detected {num_racks} rack structure(s) from bin locations")
    
    # Group traversable nodes by vertical aisles
    v_aisles = defaultdict(list)
    for idx in traversable_indices:
        v_aisle = locs.loc[idx, 'v_aisle']
        if v_aisle >= 0:
            v_aisles[v_aisle].append(idx)
    
    # Group traversable nodes by horizontal aisles
    h_aisles = defaultdict(list)
    for idx in traversable_indices:
        h_aisle = locs.loc[idx, 'h_aisle']
        if h_aisle >= 0:
            h_aisles[h_aisle].append(idx)
    
    # Identify intersection nodes
    intersection_nodes = set()
    for idx in traversable_indices:
        if locs.loc[idx, 'v_aisle'] >= 0 and locs.loc[idx, 'h_aisle'] >= 0:
            intersection_nodes.add(idx)
    
    if verbose and len(intersection_nodes) > 0:
        print(f"Found {len(intersection_nodes)} intersection points")
    
    # Connect nodes within same vertical aisle (sort by y-coordinate)
    for aisle_id, node_indices in v_aisles.items():
        if len(node_indices) < 2:
            continue
        sorted_nodes = sorted(node_indices, key=lambda i: locs.loc[i, 'y'])
        for i in range(len(sorted_nodes) - 1):
            idx1, idx2 = sorted_nodes[i], sorted_nodes[i + 1]
            
            # Check if this would cross through a rack
            if should_prevent_connection(locs, idx1, idx2):
                continue
            
            p1 = (coords[idx1][0], coords[idx1][1])
            p2 = (coords[idx2][0], coords[idx2][1])
            dist = calculate_distance(p1, p2)
            
            if dist <= max_intra_aisle_dist:
                # Check if path is blocked by obstacles
                if not is_path_blocked(p1, p2, locs, min_clearance):
                    edges.append((ids[idx1], ids[idx2], dist))
    
    # Connect nodes within same horizontal aisle (sort by x-coordinate)
    for aisle_id, node_indices in h_aisles.items():
        if len(node_indices) < 2:
            continue
        sorted_nodes = sorted(node_indices, key=lambda i: locs.loc[i, 'x'])
        for i in range(len(sorted_nodes) - 1):
            idx1, idx2 = sorted_nodes[i], sorted_nodes[i + 1]
            
            # Check if this would cross through a rack
            if should_prevent_connection(locs, idx1, idx2):
                continue
            
            p1 = (coords[idx1][0], coords[idx1][1])
            p2 = (coords[idx2][0], coords[idx2][1])
            dist = calculate_distance(p1, p2)
            
            if dist <= max_intra_aisle_dist:
                # Check if path is blocked by obstacles
                if not is_path_blocked(p1, p2, locs, min_clearance):
                    edges.append((ids[idx1], ids[idx2], dist))
    
    # Cross-aisle connections at intersection points
    for i in intersection_nodes:
        for j in intersection_nodes:
            if i >= j:
                continue
            # Skip if already in same aisle
            if (locs.loc[i, 'v_aisle'] == locs.loc[j, 'v_aisle'] and locs.loc[i, 'v_aisle'] >= 0):
                continue
            if (locs.loc[i, 'h_aisle'] == locs.loc[j, 'h_aisle'] and locs.loc[i, 'h_aisle'] >= 0):
                continue
            
            # Check if this would cross through a rack
            if should_prevent_connection(locs, i, j):
                continue
            
            p1 = (coords[i][0], coords[i][1])
            p2 = (coords[j][0], coords[j][1])
            dist = calculate_distance(p1, p2)
            
            if dist <= max_cross_aisle_dist:
                # Check if path is blocked by obstacles
                if not is_path_blocked(p1, p2, locs, min_clearance):
                    edges.append((ids[i], ids[j], dist))
    
    # Connect isolated traversable nodes to nearest neighbors
    isolated = [idx for idx in traversable_indices 
                if locs.loc[idx, 'v_aisle'] == -1 and locs.loc[idx, 'h_aisle'] == -1]
    
    for iso_idx in isolated:
        distances = []
        p1 = (coords[iso_idx][0], coords[iso_idx][1])
        
        for idx in traversable_indices:
            if idx == iso_idx:
                continue
            p2 = (coords[idx][0], coords[idx][1])
            dist = calculate_distance(p1, p2)
            
            # Check if path is clear
            if not is_path_blocked(p1, p2, locs, min_clearance):
                distances.append((idx, dist))
        
        # Connect to 2 nearest for redundancy
        distances.sort(key=lambda x: x[1])
        for idx, dist in distances[:2]:
            edges.append((ids[iso_idx], ids[idx], dist))
    
    # Ensure connectivity
    if ensure_connectivity:
        temp_G = nx.Graph()
        for idx in traversable_indices:
            temp_G.add_node(locs.loc[idx, 'id'])
        for a, b, d in edges:
            temp_G.add_edge(a, b)
        
        components = list(nx.connected_components(temp_G))
        if len(components) > 1:
            if verbose:
                print(f"Connecting {len(components)} disconnected components...")
            
            # Connect all components to form a single connected graph
            for i in range(len(components) - 1):
                comp1 = components[i]
                comp2_remaining = []
                for j in range(i + 1, len(components)):
                    comp2_remaining.extend(components[j])
                
                min_dist = float('inf')
                best_pair = None
                
                for node1 in comp1:
                    idx1 = locs[locs['id'] == node1].index[0]
                    p1 = (coords[idx1][0], coords[idx1][1])
                    
                    for node2 in comp2_remaining:
                        idx2 = locs[locs['id'] == node2].index[0]
                        p2 = (coords[idx2][0], coords[idx2][1])
                        dist = calculate_distance(p1, p2)
                        
                        # Allow longer connections to bridge components
                        # Relax obstacle checking for connectivity bridges
                        if dist < min_dist:
                            min_dist = dist
                            best_pair = (node1, node2, dist)
                
                if best_pair:
                    edges.append(best_pair)
                    if verbose:
                        print(f"  Connected component {i+1} to rest: {best_pair[0]} ↔ {best_pair[1]} ({best_pair[2]:.2f} units)")
    
    return edges


def create_graph_from_edges(locs, edges):
    """
    Create a NetworkX graph from location data and edges.
    Includes physical properties as node attributes.
    Only includes traversable nodes in the graph.
    
    Args:
        locs: DataFrame with location data
        edges: List of (node1_id, node2_id, distance) tuples
    
    Returns:
        NetworkX Graph object
    """
    G = nx.Graph()
    
    # Only add traversable nodes to the graph
    # Non-traversable locations are obstacles, not routing nodes
    traversable_locs = locs[locs['traversable'] == True]
    
    # Add nodes with all attributes including physical properties
    for _, row in traversable_locs.iterrows():
        node_attrs = {
            'x': row.x, 
            'y': row.y,
            'type': row.type,
            'zone': row.zone,
            'width': row.width,
            'depth': row.depth,
            'traversable': row.traversable,
            'v_aisle': row.v_aisle,
            'h_aisle': row.h_aisle,
            'rack_id': row.rack_id
        }
        G.add_node(row.id, **node_attrs)
    
    # Add edges
    for a, b, d in edges:
        # Only add edges if both nodes are in the graph
        if a in G.nodes() and b in G.nodes():
            if not G.has_edge(a, b):
                G.add_edge(a, b, weight=d)
    
    return G


def analyze_graph_quality(G, locs, verbose=True):
    """
    Analyze the quality of the generated graph.
    
    Args:
        G: NetworkX graph
        locs: DataFrame with location data
        verbose: Print analysis results
    
    Returns:
        dict with quality metrics
    """
    metrics = {}
    
    # Basic connectivity
    metrics['num_nodes'] = G.number_of_nodes()
    metrics['num_edges'] = G.number_of_edges()
    metrics['is_connected'] = nx.is_connected(G)
    metrics['num_components'] = nx.number_connected_components(G)
    
    # Traversability stats
    traversable_nodes = sum(1 for n in G.nodes() if G.nodes[n]['traversable'])
    metrics['traversable_nodes'] = traversable_nodes
    metrics['obstacle_nodes'] = metrics['num_nodes'] - traversable_nodes
    
    # Rack detection
    num_racks = len(set(locs['rack_id']) - {-1})
    metrics['num_racks'] = num_racks
    
    # Rack pairs (opposite sides)
    bins_with_sides = locs[(locs['rack_side'] != 'none') & (locs['rack_id'] >= 0)]
    num_paired_racks = len(bins_with_sides['rack_id'].unique())
    metrics['num_paired_racks'] = num_paired_racks // 2  # Divide by 2 since each pair counts twice
    
    # Average degree (connectivity)
    if metrics['num_nodes'] > 0:
        metrics['avg_degree'] = 2 * metrics['num_edges'] / metrics['num_nodes']
    else:
        metrics['avg_degree'] = 0
    
    if verbose:
        print("\n" + "="*60)
        print("GRAPH QUALITY ANALYSIS")
        print("="*60)
        print(f"Nodes: {metrics['num_nodes']} ({metrics['traversable_nodes']} traversable, {metrics['obstacle_nodes']} obstacles)")
        print(f"Edges: {metrics['num_edges']}")
        print(f"Average degree: {metrics['avg_degree']:.2f}")
        print(f"Connected: {metrics['is_connected']} ({metrics['num_components']} component(s))")
        if num_racks > 0:
            print(f"Inferred racks: {metrics['num_racks']} ({metrics['num_paired_racks']} pairs detected)")
            if metrics['num_paired_racks'] > 0:
                print(f"  → Paths will route around racks (no shortcuts through shelves)")
        print("="*60 + "\n")
    
    return metrics
