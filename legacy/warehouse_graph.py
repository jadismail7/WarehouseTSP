"""
Warehouse Graph Construction Module

Handles the core logic for building a warehouse graph from location data,
including aisle detection and connection rules.
"""

import math
import networkx as nx
from sklearn.cluster import DBSCAN
from collections import defaultdict


def calculate_distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def detect_aisles(locs, x_tolerance=3, y_tolerance=3, min_aisle_size=3):
    """
    Detect vertical and horizontal aisles by clustering locations
    that share similar x or y coordinates.
    
    Also detects which side of the aisle each location is on to prevent
    direct connections across opposite shelf faces.
    
    Args:
        locs: DataFrame with location data
        x_tolerance: Clustering tolerance for x-coordinates (vertical aisles)
        y_tolerance: Clustering tolerance for y-coordinates (horizontal aisles)
        min_aisle_size: Minimum number of nodes to be considered a true aisle
                       (prevents classifying isolated pairs as aisles)
    
    Returns:
        DataFrame with added columns: v_aisle, h_aisle, aisle_pair, aisle_side
    """
    coords = locs[['x', 'y']].values
    
    # Detect vertical aisles (similar x-coordinates)
    x_coords = locs['x'].values.reshape(-1, 1)
    vertical_clusters = DBSCAN(eps=x_tolerance, min_samples=min_aisle_size).fit(x_coords)
    
    # Detect horizontal aisles (similar y-coordinates)
    y_coords = locs['y'].values.reshape(-1, 1)
    horizontal_clusters = DBSCAN(eps=y_tolerance, min_samples=min_aisle_size).fit(y_coords)
    
    locs['v_aisle'] = vertical_clusters.labels_
    locs['h_aisle'] = horizontal_clusters.labels_
    
    # Detect aisle sides for paired vertical aisles
    # If two vertical aisles are close together (< 2*x_tolerance), they form opposite sides
    locs['aisle_pair'] = -1  # -1 means not part of a pair
    locs['aisle_side'] = 'none'  # 'left', 'right', or 'none'
    
    v_aisle_centers = {}
    for aisle_id in set(locs['v_aisle']) - {-1}:
        aisle_nodes = locs[locs['v_aisle'] == aisle_id]
        center_x = aisle_nodes['x'].mean()
        v_aisle_centers[aisle_id] = center_x
    
    # Find pairs of vertical aisles that are close together
    paired_aisles = set()
    pair_id = 0
    aisle_ids = sorted(v_aisle_centers.keys())
    
    for i, aisle1 in enumerate(aisle_ids):
        if aisle1 in paired_aisles:
            continue
        for aisle2 in aisle_ids[i+1:]:
            if aisle2 in paired_aisles:
                continue
            
            distance = abs(v_aisle_centers[aisle1] - v_aisle_centers[aisle2])
            # If aisles are close (within reasonable distance), consider them opposite sides
            # Typical aisle width is 10-15 units based on your data
            if distance <= 15:  # Adjust based on typical aisle spacing
                # Mark both aisles as paired
                left_aisle = aisle1 if v_aisle_centers[aisle1] < v_aisle_centers[aisle2] else aisle2
                right_aisle = aisle2 if left_aisle == aisle1 else aisle1
                
                locs.loc[locs['v_aisle'] == left_aisle, 'aisle_pair'] = pair_id
                locs.loc[locs['v_aisle'] == left_aisle, 'aisle_side'] = 'left'
                locs.loc[locs['v_aisle'] == right_aisle, 'aisle_pair'] = pair_id
                locs.loc[locs['v_aisle'] == right_aisle, 'aisle_side'] = 'right'
                
                paired_aisles.add(aisle1)
                paired_aisles.add(aisle2)
                pair_id += 1
                break
    
    return locs


def build_aisle_graph(locs, max_intra_aisle_dist=20, max_cross_aisle_dist=15, ensure_connectivity=True, 
                      only_connect_intersections=True, prevent_cross_aisle_shortcuts=True, verbose=True):
    """
    Build a graph by:
    1. Connecting nodes within the same aisle (vertical or horizontal)
    2. Connecting nodes across nearby aisles at intersection points
    3. Connecting special nodes (docks, staging, etc.) to nearest aisle entries
    4. Ensuring full connectivity by connecting disconnected components
    5. Preventing direct connections across opposite shelf faces
    
    Args:
        locs: DataFrame with location data (must have aisle detection columns)
        max_intra_aisle_dist: Maximum distance between sequential aisle nodes
        max_cross_aisle_dist: Maximum distance for cross-aisle connections
        ensure_connectivity: Ensure all components are connected
        only_connect_intersections: If True, only create cross-aisle connections at
                                   nodes that are also part of horizontal aisles
                                   (true intersection points)
        prevent_cross_aisle_shortcuts: If True, prevents connecting nodes on opposite
                                      sides of the same aisle pair (they must go around)
    
    Returns:
        List of edges as (node1_id, node2_id, distance) tuples
    """
    edges = []
    coords = locs[['x', 'y']].values
    ids = locs['id'].tolist()
    
    # Group nodes by vertical aisles
    v_aisles = defaultdict(list)
    for idx, row in locs.iterrows():
        if row['v_aisle'] >= 0:  # -1 means not in a cluster
            v_aisles[row['v_aisle']].append(idx)
    
    # Group nodes by horizontal aisles
    h_aisles = defaultdict(list)
    for idx, row in locs.iterrows():
        if row['h_aisle'] >= 0:
            h_aisles[row['h_aisle']].append(idx)
    
    # Identify intersection nodes (nodes that are part of both vertical and horizontal aisles)
    intersection_nodes = set()
    for idx, row in locs.iterrows():
        if row['v_aisle'] >= 0 and row['h_aisle'] >= 0:
            intersection_nodes.add(idx)
    
    # Identify aisle pairs (for logging only)
    aisle_pairs = locs[locs['aisle_pair'] >= 0]
    num_pairs = len(aisle_pairs['aisle_pair'].unique()) if len(aisle_pairs) > 0 else 0
    if num_pairs > 0 and verbose:
        print(f"Detected {num_pairs} aisle pair(s) with opposite shelves")
    
    # Connect nodes within same vertical aisle (sort by y-coordinate)
    for aisle_id, node_indices in v_aisles.items():
        if len(node_indices) < 2:
            continue
        # Sort by y-coordinate
        sorted_nodes = sorted(node_indices, key=lambda i: locs.loc[i, 'y'])
        for i in range(len(sorted_nodes) - 1):
            idx1, idx2 = sorted_nodes[i], sorted_nodes[i + 1]
            dist = calculate_distance(coords[idx1], coords[idx2])
            if dist <= max_intra_aisle_dist:
                edges.append((ids[idx1], ids[idx2], dist))
    
    # Connect nodes within same horizontal aisle (sort by x-coordinate)
    for aisle_id, node_indices in h_aisles.items():
        if len(node_indices) < 2:
            continue
        # Sort by x-coordinate
        sorted_nodes = sorted(node_indices, key=lambda i: locs.loc[i, 'x'])
        for i in range(len(sorted_nodes) - 1):
            idx1, idx2 = sorted_nodes[i], sorted_nodes[i + 1]
            dist = calculate_distance(coords[idx1], coords[idx2])
            if dist <= max_intra_aisle_dist:
                # Check if this would create a shortcut across opposite shelf faces
                if prevent_cross_aisle_shortcuts:
                    pair1 = locs.loc[idx1, 'aisle_pair']
                    pair2 = locs.loc[idx2, 'aisle_pair']
                    side1 = locs.loc[idx1, 'aisle_side']
                    side2 = locs.loc[idx2, 'aisle_side']
                    
                    # Allow connections if they're at the ends of the aisle (y-coordinate extremes)
                    # This allows going around the aisle
                    is_at_aisle_end = False
                    if pair1 >= 0 and pair1 == pair2 and side1 != side2:
                        # Check if both nodes are at extreme y positions for their aisle pair
                        pair_nodes = locs[locs['aisle_pair'] == pair1]
                        y_min = pair_nodes['y'].min()
                        y_max = pair_nodes['y'].max()
                        y1 = locs.loc[idx1, 'y']
                        y2 = locs.loc[idx2, 'y']
                        
                        # Allow if both are near the min or max end
                        tolerance = 5  # y-coordinate tolerance for "end of aisle"
                        if (abs(y1 - y_min) <= tolerance and abs(y2 - y_min) <= tolerance) or \
                           (abs(y1 - y_max) <= tolerance and abs(y2 - y_max) <= tolerance):
                            is_at_aisle_end = True
                    
                    # Only add if they're NOT on opposite sides OR if they're at aisle ends
                    if not (pair1 >= 0 and pair1 == pair2 and side1 != side2) or is_at_aisle_end:
                        edges.append((ids[idx1], ids[idx2], dist))
                else:
                    edges.append((ids[idx1], ids[idx2], dist))
    
    # Find cross-aisle connections
    if only_connect_intersections:
        # Only connect at true intersection points (nodes in both vertical and horizontal aisles)
        # This prevents mid-aisle connections
        for i in intersection_nodes:
            for j in intersection_nodes:
                if i >= j:
                    continue
                # Skip if already in same aisle
                if (locs.loc[i, 'v_aisle'] == locs.loc[j, 'v_aisle'] and locs.loc[i, 'v_aisle'] >= 0):
                    continue
                if (locs.loc[i, 'h_aisle'] == locs.loc[j, 'h_aisle'] and locs.loc[i, 'h_aisle'] >= 0):
                    continue
                
                # Check if this would create a shortcut across opposite shelf faces
                if prevent_cross_aisle_shortcuts:
                    pair1 = locs.loc[i, 'aisle_pair']
                    pair2 = locs.loc[j, 'aisle_pair']
                    side1 = locs.loc[i, 'aisle_side']
                    side2 = locs.loc[j, 'aisle_side']
                    
                    # Don't connect opposite sides of the same aisle pair
                    if pair1 >= 0 and pair1 == pair2 and side1 != side2:
                        continue
                
                dist = calculate_distance(coords[i], coords[j])
                if dist <= max_cross_aisle_dist:
                    edges.append((ids[i], ids[j], dist))
    else:
        # Original behavior: connect any close nodes across aisles
        for i in range(len(locs)):
            for j in range(i + 1, len(locs)):
                # Skip if already in same aisle
                if (locs.loc[i, 'v_aisle'] == locs.loc[j, 'v_aisle'] and locs.loc[i, 'v_aisle'] >= 0):
                    continue
                if (locs.loc[i, 'h_aisle'] == locs.loc[j, 'h_aisle'] and locs.loc[i, 'h_aisle'] >= 0):
                    continue
                
                # Check if this would create a shortcut across opposite shelf faces
                if prevent_cross_aisle_shortcuts:
                    pair1 = locs.loc[i, 'aisle_pair']
                    pair2 = locs.loc[j, 'aisle_pair']
                    side1 = locs.loc[i, 'aisle_side']
                    side2 = locs.loc[j, 'aisle_side']
                    
                    # Don't connect opposite sides of the same aisle pair
                    if pair1 >= 0 and pair1 == pair2 and side1 != side2:
                        continue
                
                dist = calculate_distance(coords[i], coords[j])
                if dist <= max_cross_aisle_dist:
                    edges.append((ids[i], ids[j], dist))
    
    # Connect isolated nodes (not in any aisle) to nearest neighbors (connect to multiple for redundancy)
    isolated = locs[(locs['v_aisle'] == -1) & (locs['h_aisle'] == -1)].index
    for iso_idx in isolated:
        # Find 2 nearest neighbors for better connectivity
        distances = []
        for idx in locs.index:
            if idx == iso_idx:
                continue
            dist = calculate_distance(coords[iso_idx], coords[idx])
            distances.append((idx, dist))
        
        # Sort by distance and connect to 2 nearest
        distances.sort(key=lambda x: x[1])
        for idx, dist in distances[:2]:
            edges.append((ids[iso_idx], ids[idx], dist))
    
    # Ensure connectivity by checking and connecting components
    if ensure_connectivity:
        # Build temporary graph to check connectivity
        temp_G = nx.Graph()
        for _, row in locs.iterrows():
            temp_G.add_node(row['id'])
        for a, b, d in edges:
            temp_G.add_edge(a, b)
        
        # Connect disconnected components
        components = list(nx.connected_components(temp_G))
        if len(components) > 1:
            # Connect each component to its nearest neighbor in another component
            for i in range(len(components) - 1):
                comp1 = components[i]
                comp2 = components[i + 1]
                
                min_dist = float('inf')
                best_pair = None
                
                for node1 in comp1:
                    idx1 = locs[locs['id'] == node1].index[0]
                    for node2 in comp2:
                        idx2 = locs[locs['id'] == node2].index[0]
                        dist = calculate_distance(coords[idx1], coords[idx2])
                        if dist < min_dist:
                            min_dist = dist
                            best_pair = (node1, node2, dist)
                
                if best_pair:
                    edges.append(best_pair)
    
    return edges


def create_graph_from_edges(locs, edges):
    """
    Create a NetworkX graph from location data and edges.
    
    Args:
        locs: DataFrame with location data
        edges: List of (node1_id, node2_id, distance) tuples
    
    Returns:
        NetworkX Graph object
    """
    G = nx.Graph()
    
    # Add nodes with attributes
    for _, row in locs.iterrows():
        G.add_node(row.id, x=row.x, y=row.y, v_aisle=row.v_aisle, h_aisle=row.h_aisle,
                   aisle_pair=row.aisle_pair, aisle_side=row.aisle_side)
    
    # Add edges
    for a, b, d in edges:
        if not G.has_edge(a, b):  # Avoid duplicate edges
            G.add_edge(a, b, weight=d)
    
    return G
