"""
Multi-Floor Warehouse Module

Handles warehouses with multiple floors by:
1. Loading separate JSON files for each floor
2. Building unified or per-floor graphs
3. Supporting multiple TSP strategies:
   - Unified TSP with high inter-floor penalties
   - Per-floor TSP with intelligent merging
"""

import json
import pandas as pd
import networkx as nx
from collections import defaultdict

from legacy.warehouse_graph_enhanced import (
    detect_aisles_with_dimensions,
    build_enhanced_graph,
    create_graph_from_edges
)
from legacy.routing import solve_tsp, calculate_route_distance


class MultiFloorWarehouse:
    """
    Manages a multi-floor warehouse with separate layouts per floor.
    """
    
    def __init__(self, floor_files, inter_floor_penalty=1000.0):
        """
        Initialize multi-floor warehouse.
        
        Args:
            floor_files: List of JSON file paths, one per floor
            inter_floor_penalty: Distance penalty for moving between floors (default: 1000)
        """
        self.floor_files = floor_files
        self.inter_floor_penalty = inter_floor_penalty
        self.floors = {}  # {floor_num: DataFrame}
        self.floor_graphs = {}  # {floor_num: NetworkX graph}
        self.floor_edges = {}  # {floor_num: edge list}
        self.unified_graph = None
        self.unified_locs = None
        
        self._load_floors()
    
    def _load_floors(self):
        """Load all floor layouts from JSON files."""
        print(f"\nLoading {len(self.floor_files)} floor(s)...")
        
        for floor_num, floor_file in enumerate(self.floor_files, start=1):
            print(f"  Floor {floor_num}: {floor_file}")
            
            with open(floor_file) as f:
                data = json.load(f)
            
            # Create DataFrame with floor number
            locs = pd.DataFrame(data)
            locs['floor'] = floor_num
            
            # Make IDs unique across floors by prefixing with floor number
            locs['original_id'] = locs['id']
            locs['id'] = locs['id'].apply(lambda x: f"F{floor_num}_{x}")
            
            print(f"    Locations: {len(locs)}")
            
            self.floors[floor_num] = locs
    
    def build_per_floor_graphs(self, max_intra_aisle_dist=25, max_cross_aisle_dist=20, 
                                min_clearance=1.0, verbose=False):
        """
        Build separate graphs for each floor.
        
        Returns:
            dict: {floor_num: NetworkX graph}
        """
        print("\nBuilding per-floor graphs...")
        
        for floor_num, locs in self.floors.items():
            print(f"  Floor {floor_num}:")
            
            # Detect aisles and racks
            locs = detect_aisles_with_dimensions(locs, x_tolerance=5, y_tolerance=5, min_aisle_size=3)
            
            # Build graph
            edges = build_enhanced_graph(locs, max_intra_aisle_dist, max_cross_aisle_dist,
                                        min_clearance, verbose)
            G = create_graph_from_edges(locs, edges)
            
            # Store results
            self.floors[floor_num] = locs  # Update with aisle/rack info
            self.floor_edges[floor_num] = edges
            self.floor_graphs[floor_num] = G
            
            num_racks = len(set(locs['rack_id']) - {-1})
            print(f"    Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}, Racks: {num_racks}")
        
        return self.floor_graphs
    
    def build_unified_graph(self, stair_locations=None, elevator_locations=None):
        """
        Build a unified graph connecting all floors with high-penalty inter-floor edges.
        
        Args:
            stair_locations: List of (floor, location_original_id) tuples for stair access points
            elevator_locations: List of (floor, location_original_id) tuples for elevator access
        
        Returns:
            tuple: (unified_graph, unified_locations_df)
        """
        print("\nBuilding unified multi-floor graph...")
        
        # First build per-floor graphs if not done
        if not self.floor_graphs:
            self.build_per_floor_graphs()
        
        # Combine all floors into one DataFrame
        all_locs = pd.concat([locs for locs in self.floors.values()], ignore_index=True)
        self.unified_locs = all_locs
        
        # Create unified graph by combining all floor graphs
        G = nx.Graph()
        
        # Add all nodes and edges from individual floors
        for floor_num, floor_graph in self.floor_graphs.items():
            G.add_nodes_from(floor_graph.nodes(data=True))
            G.add_edges_from(floor_graph.edges(data=True))
        
        # Add inter-floor connections
        inter_floor_edges = 0
        
        # Default: Connect stairs and elevators if specified
        if stair_locations or elevator_locations:
            access_points = []
            
            if stair_locations:
                access_points.extend([('stair', floor, orig_id) for floor, orig_id in stair_locations])
            
            if elevator_locations:
                access_points.extend([('elevator', floor, orig_id) for floor, orig_id in elevator_locations])
            
            # Connect access points between consecutive floors
            access_by_type_and_id = defaultdict(list)
            for access_type, floor, orig_id in access_points:
                key = (access_type, orig_id)
                access_by_type_and_id[key].append((floor, f"F{floor}_{orig_id}"))
            
            # Connect same access points on different floors
            for key, floor_locs in access_by_type_and_id.items():
                floor_locs.sort()  # Sort by floor number
                for i in range(len(floor_locs) - 1):
                    floor1, loc1 = floor_locs[i]
                    floor2, loc2 = floor_locs[i + 1]
                    
                    if loc1 in G.nodes() and loc2 in G.nodes():
                        G.add_edge(loc1, loc2, weight=self.inter_floor_penalty)
                        inter_floor_edges += 1
        
        else:
            # Fallback: Connect all staging/dock areas between floors with high penalty
            print("  No access points specified, connecting staging/dock areas between floors")
            
            for floor1 in sorted(self.floors.keys()):
                for floor2 in sorted(self.floors.keys()):
                    if floor2 <= floor1:
                        continue
                    
                    # Get staging/dock areas
                    locs1 = self.floors[floor1]
                    locs2 = self.floors[floor2]
                    
                    # Find traversable access points (staging or dock)
                    access1 = locs1[(locs1['type'].isin(['staging', 'dock'])) & (locs1['traversable'] == True)]
                    access2 = locs2[(locs2['type'].isin(['staging', 'dock'])) & (locs2['traversable'] == True)]
                    
                    # Connect first staging area from each floor
                    if len(access1) > 0 and len(access2) > 0:
                        node1 = access1.iloc[0]['id']
                        node2 = access2.iloc[0]['id']
                        
                        print(f"    Connecting Floor {floor1} ↔ Floor {floor2}")
                        print(f"      Node1: {node1} (in graph: {node1 in G.nodes()})")
                        print(f"      Node2: {node2} (in graph: {node2 in G.nodes()})")
                        
                        if node1 in G.nodes() and node2 in G.nodes():
                            G.add_edge(node1, node2, weight=self.inter_floor_penalty)
                            inter_floor_edges += 1
                            print(f"      ✓ Connected with penalty {self.inter_floor_penalty}")
        
        self.unified_graph = G
        
        print(f"  Total nodes: {G.number_of_nodes()}")
        print(f"  Total edges: {G.number_of_edges()}")
        print(f"  Inter-floor edges: {inter_floor_edges} (penalty: {self.inter_floor_penalty})")
        print(f"  Connected: {nx.is_connected(G)}")
        
        return G, all_locs
    
    def solve_unified_tsp(self, picks, start=None, end=None):
        """
        Solve TSP across all floors using unified graph with inter-floor penalties.
        
        Args:
            picks: List of pick location original IDs (without floor prefix)
            start: Starting location original ID (will use floor 1 if not prefixed)
            end: Ending location original ID
        
        Returns:
            tuple: (route, total_distance, pick_sequence, floor_transitions)
        """
        if not self.unified_graph:
            raise ValueError("Must call build_unified_graph() first")
        
        print("\n" + "="*70)
        print("SOLVING TSP: UNIFIED APPROACH")
        print("="*70)
        
        # Map picks to their floor-prefixed IDs
        prefixed_picks = []
        pick_to_floor = {}
        
        for pick in picks:
            found = False
            for floor_num, locs in self.floors.items():
                if pick in locs['original_id'].values:
                    prefixed_id = f"F{floor_num}_{pick}"
                    prefixed_picks.append(prefixed_id)
                    pick_to_floor[pick] = floor_num
                    found = True
                    break
            
            if not found:
                print(f"WARNING: Pick location '{pick}' not found in any floor")
        
        # Determine start/end
        if start and not start.startswith('F'):
            # Find start on first floor it appears
            for floor_num, locs in self.floors.items():
                if start in locs['original_id'].values:
                    start = f"F{floor_num}_{start}"
                    break
        
        if not start:
            start = self.unified_locs[self.unified_locs['type'] == 'staging'].iloc[0]['id']
        
        if end and not end.startswith('F'):
            for floor_num, locs in self.floors.items():
                if end in locs['original_id'].values:
                    end = f"F{floor_num}_{end}"
                    break
        
        if not end:
            end = start
        
        # Build route
        route_to_optimize = [start] + prefixed_picks
        if end != start:
            route_to_optimize.append(end)
        
        print(f"\nOptimizing route for {len(prefixed_picks)} picks across {len(self.floors)} floors")
        
        # Solve TSP
        best_order = solve_tsp(self.unified_graph, route_to_optimize, cycle=False, method='christofides')
        
        if not best_order:
            return None, None, None, None
        
        # Calculate distance
        total_distance = calculate_route_distance(self.unified_graph, best_order)
        
        # Extract pick sequence
        pick_sequence = [loc for loc in best_order if loc in prefixed_picks]
        
        # Analyze floor transitions
        floor_transitions = self._analyze_floor_transitions(best_order)
        
        return best_order, total_distance, pick_sequence, floor_transitions
    
    def solve_per_floor_tsp(self, picks, start=None, end=None, merge_strategy='sequential'):
        """
        Solve TSP separately on each floor, then merge results.
        
        Args:
            picks: List of pick location original IDs
            start: Starting location original ID
            end: Ending location original ID
            merge_strategy: 'sequential' (floor order) or 'optimal' (minimize transitions)
        
        Returns:
            tuple: (route, total_distance, pick_sequence, floor_transitions)
        """
        if not self.floor_graphs:
            self.build_per_floor_graphs()
        
        print("\n" + "="*70)
        print(f"SOLVING TSP: PER-FLOOR APPROACH ({merge_strategy.upper()})")
        print("="*70)
        
        # Group picks by floor
        picks_by_floor = defaultdict(list)
        for pick in picks:
            found = False
            for floor_num, locs in self.floors.items():
                if pick in locs['original_id'].values:
                    prefixed_id = f"F{floor_num}_{pick}"
                    picks_by_floor[floor_num].append(prefixed_id)
                    found = True
                    break
            if not found:
                print(f"WARNING: Pick '{pick}' not found")
        
        print(f"\nPicks distribution:")
        for floor_num in sorted(picks_by_floor.keys()):
            print(f"  Floor {floor_num}: {len(picks_by_floor[floor_num])} picks")
        
        # Solve TSP on each floor
        floor_routes = {}
        floor_distances = {}
        
        for floor_num in sorted(picks_by_floor.keys()):
            floor_picks = picks_by_floor[floor_num]
            
            if len(floor_picks) == 0:
                continue
            
            print(f"\nOptimizing Floor {floor_num}...")
            
            # Find start point on this floor (staging/dock)
            floor_locs = self.floors[floor_num]
            floor_start = floor_locs[floor_locs['type'].isin(['staging', 'dock'])].iloc[0]['id']
            
            # Build route
            route_to_optimize = [floor_start] + floor_picks
            
            # Solve TSP
            floor_route = solve_tsp(self.floor_graphs[floor_num], route_to_optimize, 
                                   cycle=False, method='christofides')
            
            if floor_route:
                floor_dist = calculate_route_distance(self.floor_graphs[floor_num], floor_route)
                floor_routes[floor_num] = floor_route
                floor_distances[floor_num] = floor_dist
                print(f"  Distance: {floor_dist:.2f} units, Waypoints: {len(floor_route)}")
        
        # Merge routes
        if merge_strategy == 'sequential':
            merged_route = self._merge_sequential(floor_routes)
        else:  # optimal
            merged_route = self._merge_optimal(floor_routes, picks_by_floor)
        
        # Calculate total distance (sum of floor distances + inter-floor penalties)
        total_distance = sum(floor_distances.values())
        floor_transitions = self._analyze_floor_transitions(merged_route)
        total_distance += floor_transitions['num_transitions'] * self.inter_floor_penalty
        
        # Extract pick sequence
        all_picks = [p for picks in picks_by_floor.values() for p in picks]
        pick_sequence = [loc for loc in merged_route if loc in all_picks]
        
        return merged_route, total_distance, pick_sequence, floor_transitions
    
    def _merge_sequential(self, floor_routes):
        """Merge floor routes in sequential order (1, 2, 3, ...)"""
        merged = []
        for floor_num in sorted(floor_routes.keys()):
            if floor_num == min(floor_routes.keys()):
                merged.extend(floor_routes[floor_num])
            else:
                # Skip first node (start point) to avoid duplication
                merged.extend(floor_routes[floor_num][1:])
        return merged
    
    def _merge_optimal(self, floor_routes, picks_by_floor):
        """Merge floor routes to minimize transitions (greedy nearest floor)"""
        # For now, same as sequential but could be enhanced
        # to choose floor order based on pick density
        return self._merge_sequential(floor_routes)
    
    def _analyze_floor_transitions(self, route):
        """Analyze how many times the route changes floors."""
        transitions = []
        prev_floor = None
        
        for node in route:
            # Extract floor number from node ID (F1_xxx -> 1)
            floor = int(node.split('_')[0][1:]) if node.startswith('F') else 1
            
            if prev_floor is not None and floor != prev_floor:
                transitions.append((prev_floor, floor))
            
            prev_floor = floor
        
        return {
            'num_transitions': len(transitions),
            'transitions': transitions,
            'floors_visited': sorted(set([int(n.split('_')[0][1:]) for n in route if n.startswith('F')]))
        }
    
    def get_floor_locations(self):
        """Get combined locations DataFrame with floor information."""
        if self.unified_locs is not None:
            return self.unified_locs
        return pd.concat([locs for locs in self.floors.values()], ignore_index=True)


def compare_strategies(warehouse, picks, start=None, end=None):
    """
    Compare unified vs per-floor TSP strategies.
    
    Returns:
        dict: Comparison results
    """
    print("\n" + "="*70)
    print("COMPARING TSP STRATEGIES")
    print("="*70)
    
    results = {}
    
    # Strategy 1: Unified TSP
    route1, dist1, picks1, trans1 = warehouse.solve_unified_tsp(picks, start, end)
    results['unified'] = {
        'route': route1,
        'distance': dist1,
        'picks': picks1,
        'transitions': trans1,
        'waypoints': len(route1) if route1 else 0
    }
    
    # Strategy 2: Per-floor TSP (sequential)
    route2, dist2, picks2, trans2 = warehouse.solve_per_floor_tsp(picks, start, end, 'sequential')
    results['per_floor_sequential'] = {
        'route': route2,
        'distance': dist2,
        'picks': picks2,
        'transitions': trans2,
        'waypoints': len(route2) if route2 else 0
    }
    
    # Print comparison
    print("\n" + "="*70)
    print("STRATEGY COMPARISON")
    print("="*70)
    
    print(f"\n{'Strategy':<25} {'Distance':<15} {'Transitions':<15} {'Waypoints':<15}")
    print("-"*70)
    
    for strategy, data in results.items():
        strategy_name = strategy.replace('_', ' ').title()
        num_trans = data['transitions']['num_transitions'] if data['transitions'] else 0
        print(f"{strategy_name:<25} {data['distance']:>12.1f}u  {num_trans:>13}  {data['waypoints']:>13}")
    
    return results
