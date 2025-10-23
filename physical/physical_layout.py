"""
Physical Warehouse Layout Module

Handles warehouse layouts with physical dimensions (center, width, depth).
Creates graphs based on obstacle-aware pathfinding, considering which areas
are traversable and which are blocked by racks, equipment, etc.
"""

import json
import math
import numpy as np
import networkx as nx
from shapely.geometry import Polygon, LineString, Point
from collections import defaultdict


class WarehouseObject:
    """Represents a physical object in the warehouse with dimensions."""
    
    def __init__(self, obj_data):
        self.id = obj_data['id']
        self.center_x = obj_data['center']['x']
        self.center_y = obj_data['center']['y']
        self.width = obj_data['width']
        self.depth = obj_data['depth']
        self.type = obj_data['type']
        self.traversable = obj_data.get('traversable', False)
        self.pick_points = obj_data.get('pick_points', [])
        
        # Create bounding box polygon
        half_w = self.width / 2
        half_d = self.depth / 2
        self.polygon = Polygon([
            (self.center_x - half_w, self.center_y - half_d),
            (self.center_x + half_w, self.center_y - half_d),
            (self.center_x + half_w, self.center_y + half_d),
            (self.center_x - half_w, self.center_y + half_d)
        ])
    
    def get_pick_locations(self):
        """Get all pick point locations for this object."""
        locations = []
        for pick in self.pick_points:
            x = self.center_x + pick['offset']['x']
            y = self.center_y + pick['offset']['y']
            locations.append({
                'id': pick['id'],
                'x': x,
                'y': y,
                'parent': self.id
            })
        return locations
    
    def contains_point(self, x, y):
        """Check if a point is inside this object."""
        return self.polygon.contains(Point(x, y))
    
    def intersects_line(self, x1, y1, x2, y2):
        """Check if a line segment intersects this object."""
        line = LineString([(x1, y1), (x2, y2)])
        return self.polygon.intersects(line)


class PhysicalWarehouse:
    """Represents a warehouse with physical dimensions and obstacles."""
    
    def __init__(self, json_file):
        """Load warehouse layout from JSON file."""
        with open(json_file) as f:
            data = json.load(f)
        
        self.objects = [WarehouseObject(obj) for obj in data]
        self.obstacles = [obj for obj in self.objects if not obj.traversable]
        self.traversable_areas = [obj for obj in self.objects if obj.traversable]
        
        # Extract all pick points and traversable centers
        self.nodes = {}
        for obj in self.objects:
            # Add pick points
            for loc in obj.get_pick_locations():
                self.nodes[loc['id']] = {
                    'x': loc['x'],
                    'y': loc['y'],
                    'type': 'pick',
                    'parent': loc['parent']
                }
            
            # Add centers of traversable areas (aisles, staging, etc.)
            if obj.traversable:
                self.nodes[obj.id] = {
                    'x': obj.center_x,
                    'y': obj.center_y,
                    'type': obj.type,
                    'parent': None
                }
    
    def is_path_clear(self, x1, y1, x2, y2, tolerance=0.1):
        """
        Check if a straight path between two points is clear of obstacles.
        
        Args:
            x1, y1: Start point
            x2, y2: End point
            tolerance: Small buffer to avoid edge cases
        
        Returns:
            bool: True if path is clear, False if blocked
        """
        line = LineString([(x1, y1), (x2, y2)])
        
        # Check against all non-traversable obstacles
        for obstacle in self.obstacles:
            # Use a small buffer to be slightly conservative
            if obstacle.polygon.buffer(tolerance).intersects(line):
                # Additional check: if both points are pick points of the same rack,
                # they might be on opposite sides - this is OK
                return False
        
        return True
    
    def get_nearby_nodes(self, node_id, max_distance=20):
        """
        Get nodes within max_distance that could potentially connect.
        
        Args:
            node_id: Source node ID
            max_distance: Maximum distance to consider
        
        Returns:
            List of (node_id, distance) tuples
        """
        source = self.nodes[node_id]
        nearby = []
        
        for other_id, other in self.nodes.items():
            if other_id == node_id:
                continue
            
            dist = math.sqrt((source['x'] - other['x'])**2 + 
                           (source['y'] - other['y'])**2)
            
            if dist <= max_distance:
                nearby.append((other_id, dist))
        
        return sorted(nearby, key=lambda x: x[1])
    
    def build_graph(self, max_connection_dist=30, verbose=True):
        """
        Build a graph considering physical obstacles.
        
        Args:
            max_connection_dist: Maximum distance for direct connections
            verbose: Print progress information
        
        Returns:
            NetworkX Graph
        """
        if verbose:
            print(f"Building physical warehouse graph...")
            print(f"  Total nodes: {len(self.nodes)}")
            print(f"  Obstacles: {len(self.obstacles)}")
            print(f"  Traversable areas: {len(self.traversable_areas)}")
        
        G = nx.Graph()
        
        # Add all nodes
        for node_id, node_data in self.nodes.items():
            G.add_node(node_id, 
                      x=node_data['x'], 
                      y=node_data['y'],
                      type=node_data['type'],
                      parent=node_data['parent'])
        
        # Build edges by checking visibility
        edges_added = 0
        edges_blocked = 0
        
        for node_id in self.nodes:
            nearby = self.get_nearby_nodes(node_id, max_connection_dist)
            source = self.nodes[node_id]
            
            for other_id, dist in nearby:
                # Skip if edge already exists (undirected graph)
                if G.has_edge(node_id, other_id):
                    continue
                
                other = self.nodes[other_id]
                
                # Check if path is clear
                if self.is_path_clear(source['x'], source['y'], 
                                     other['x'], other['y']):
                    G.add_edge(node_id, other_id, weight=dist)
                    edges_added += 1
                else:
                    edges_blocked += 1
        
        if verbose:
            print(f"  Edges added: {edges_added}")
            print(f"  Edges blocked by obstacles: {edges_blocked}")
            print(f"  Graph connected: {nx.is_connected(G)}")
        
        # Check for disconnected components
        if not nx.is_connected(G):
            components = list(nx.connected_components(G))
            if verbose:
                print(f"  Warning: {len(components)} disconnected components")
            
            # Try to connect components by finding closest pairs
            self._connect_components(G, components, verbose)
        
        return G
    
    def _connect_components(self, G, components, verbose=True):
        """Connect disconnected components by finding safe paths."""
        # Keep connecting until all components are merged
        while len(components) > 1:
            best_connection = None
            best_dist = float('inf')
            comp_pair = None
            
            # Try all pairs of components
            for i in range(len(components)):
                comp1 = list(components[i])
                for j in range(i + 1, len(components)):
                    comp2 = list(components[j])
                    
                    # Find closest pair that has clear path
                    for n1 in comp1:
                        p1 = self.nodes[n1]
                        for n2 in comp2:
                            p2 = self.nodes[n2]
                            dist = math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)
                            
                            if dist < best_dist and self.is_path_clear(p1['x'], p1['y'], 
                                                                        p2['x'], p2['y']):
                                best_dist = dist
                                best_connection = (n1, n2, dist)
                                comp_pair = (i, j)
            
            if best_connection:
                G.add_edge(best_connection[0], best_connection[1], 
                          weight=best_connection[2])
                if verbose:
                    print(f"  Connected components: {best_connection[0]} <-> {best_connection[1]} (dist: {best_dist:.2f})")
                
                # Merge the two components
                merged = components[comp_pair[0]].union(components[comp_pair[1]])
                components = [comp for i, comp in enumerate(components) 
                             if i not in comp_pair] + [merged]
            else:
                # Can't connect any more components with clear paths
                if verbose:
                    print(f"  Warning: Could not connect all components (remaining: {len(components)})")
                break
    
    def get_bounds(self):
        """Get the bounding box of the warehouse."""
        all_x = [node['x'] for node in self.nodes.values()]
        all_y = [node['y'] for node in self.nodes.values()]
        
        # Include object boundaries
        for obj in self.objects:
            half_w = obj.width / 2
            half_d = obj.depth / 2
            all_x.extend([obj.center_x - half_w, obj.center_x + half_w])
            all_y.extend([obj.center_y - half_d, obj.center_y + half_d])
        
        return {
            'x_min': min(all_x),
            'x_max': max(all_x),
            'y_min': min(all_y),
            'y_max': max(all_y)
        }


def load_physical_warehouse(json_file):
    """
    Load a physical warehouse layout and build its graph.
    
    Args:
        json_file: Path to warehouse JSON file
    
    Returns:
        tuple: (NetworkX Graph, PhysicalWarehouse object)
    """
    warehouse = PhysicalWarehouse(json_file)
    graph = warehouse.build_graph()
    return graph, warehouse
