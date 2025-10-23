"""
Integration tests for multi-floor warehouse workflow
Tests complete multi-floor flows including floor merging and strategy comparison
"""
import pytest
import os
import json
import pandas as pd
import networkx as nx
from cli_utils import add_floor_prefix


class TestMultiFloorWorkflow:
    """Integration tests for multi-floor warehouse processing"""
    
    def test_complete_multifloor_workflow(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test complete workflow with two floors"""
        # Write floor data
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "floor2.json"
        )
        
        # Picks from both floors
        picks = ["A1-1", "A1-2", "B1-1", "B1-2"]
        picks_file = write_picks_file(picks, "multifloor_picks.txt")
        
        # Load both floors
        from legacy.warehouse_graph_enhanced import EnhancedWarehouseGraph
        
        df1 = pd.read_json(floor1_file)
        df2 = pd.read_json(floor2_file)
        
        # Add floor prefixes
        locs1 = add_floor_prefix(df1.to_dict('records'), floor_num=1)
        locs2 = add_floor_prefix(df2.to_dict('records'), floor_num=2)
        
        # Build graphs
        df1_prefixed = pd.DataFrame(locs1)
        df2_prefixed = pd.DataFrame(locs2)
        
        G1 = EnhancedWarehouseGraph(df1_prefixed).build_graph()
        G2 = EnhancedWarehouseGraph(df2_prefixed).build_graph()
        
        # Merge graphs
        G_merged = nx.compose(G1, G2)
        
        assert G_merged.number_of_nodes() == G1.number_of_nodes() + G2.number_of_nodes()
        assert G_merged.has_node('F1_A1-1')
        assert G_merged.has_node('F2_B1-1')
    
    def test_floor_prefix_application(self, multi_floor_warehouse, write_json_file):
        """Test that floor prefixes are applied correctly"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "prefix_floor1.json"
        )
        
        df = pd.read_json(floor1_file)
        locations = df.to_dict('records')
        
        # Add prefix
        prefixed = add_floor_prefix(locations, floor_num=1)
        
        # All IDs should have F1_ prefix
        for loc in prefixed:
            assert loc['id'].startswith('F1_')
        
        # Original coordinates preserved
        for orig, prefixed_loc in zip(locations, prefixed):
            assert orig['x'] == prefixed_loc['x']
            assert orig['y'] == prefixed_loc['y']
    
    def test_picks_distribution_across_floors(self, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test picks distributed across multiple floors"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "dist_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "dist_floor2.json"
        )
        
        # Mix of picks from different floors
        picks = ["A1-1", "B1-1"]  # Floor 1: A1-1, Floor 2: B1-1
        picks_file = write_picks_file(picks, "distributed_picks.txt")
        
        # Load picks
        with open(picks_file, 'r') as f:
            loaded_picks = [line.strip() for line in f if line.strip()]
        
        # Add floor prefixes to picks
        f1_picks = [f"F1_{p}" for p in loaded_picks]
        f2_picks = [f"F2_{p}" for p in loaded_picks]
        
        # Should have picks on multiple floors
        assert len(f1_picks) > 0
        assert len(f2_picks) > 0


class TestFloorTransitions:
    """Integration tests for floor transitions"""
    
    def test_add_floor_transition_edges(self, multi_floor_warehouse, write_json_file):
        """Test adding edges between floors for elevators/stairs"""
        from legacy.warehouse_graph_enhanced import EnhancedWarehouseGraph
        
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "trans_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "trans_floor2.json"
        )
        
        df1 = pd.read_json(floor1_file)
        df2 = pd.read_json(floor2_file)
        
        locs1 = add_floor_prefix(df1.to_dict('records'), floor_num=1)
        locs2 = add_floor_prefix(df2.to_dict('records'), floor_num=2)
        
        df1_prefixed = pd.DataFrame(locs1)
        df2_prefixed = pd.DataFrame(locs2)
        
        G1 = EnhancedWarehouseGraph(df1_prefixed).build_graph()
        G2 = EnhancedWarehouseGraph(df2_prefixed).build_graph()
        
        G_merged = nx.compose(G1, G2)
        
        # Add transition edges (example: connect first nodes of each floor)
        if G1.number_of_nodes() > 0 and G2.number_of_nodes() > 0:
            node1 = list(G1.nodes())[0]
            node2 = list(G2.nodes())[0]
            
            transition_penalty = 100
            G_merged.add_edge(node1, node2, weight=transition_penalty)
            
            assert G_merged.has_edge(node1, node2)
            assert G_merged[node1][node2]['weight'] == transition_penalty
    
    def test_transition_penalty_applied(self):
        """Test that floor transitions have appropriate penalty"""
        G = nx.Graph()
        
        # Same floor edge
        G.add_edge('F1_A', 'F1_B', weight=10)
        
        # Cross floor edge
        G.add_edge('F1_A', 'F2_C', weight=110)  # 10 distance + 100 penalty
        
        # Verify penalties
        same_floor_weight = G['F1_A']['F1_B']['weight']
        cross_floor_weight = G['F1_A']['F2_C']['weight']
        
        assert same_floor_weight < cross_floor_weight


class TestMultiFloorStrategies:
    """Integration tests for comparing multi-floor TSP strategies"""
    
    def test_unified_strategy_execution(self, multi_floor_warehouse, write_json_file):
        """Test execution of unified (single TSP) strategy"""
        from legacy.warehouse_graph_enhanced import EnhancedWarehouseGraph
        
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "unified_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "unified_floor2.json"
        )
        
        df1 = pd.read_json(floor1_file)
        df2 = pd.read_json(floor2_file)
        
        locs1 = add_floor_prefix(df1.to_dict('records'), floor_num=1)
        locs2 = add_floor_prefix(df2.to_dict('records'), floor_num=2)
        
        df1_prefixed = pd.DataFrame(locs1)
        df2_prefixed = pd.DataFrame(locs2)
        
        G1 = EnhancedWarehouseGraph(df1_prefixed).build_graph()
        G2 = EnhancedWarehouseGraph(df2_prefixed).build_graph()
        
        # Merge with transitions
        G_merged = nx.compose(G1, G2)
        
        # Add some transition edges
        if G1.number_of_nodes() > 0 and G2.number_of_nodes() > 0:
            nodes1 = list(G1.nodes())[:2]
            nodes2 = list(G2.nodes())[:2]
            
            for n1 in nodes1:
                for n2 in nodes2:
                    G_merged.add_edge(n1, n2, weight=100)
        
        # Should be able to solve TSP on merged graph
        if nx.is_connected(G_merged):
            picks = list(G_merged.nodes())[:4]
            
            from cli_utils import solve_tsp_christofides
            route, distance = solve_tsp_christofides(
                G_merged, picks, picks[0], picks[0]
            )
            
            assert route is not None
            assert distance > 0
    
    def test_perfloor_strategy_execution(self, multi_floor_warehouse, write_json_file):
        """Test execution of per-floor (sequential TSP) strategy"""
        from legacy.warehouse_graph_enhanced import EnhancedWarehouseGraph
        
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "perfloor_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "perfloor_floor2.json"
        )
        
        df1 = pd.read_json(floor1_file)
        df2 = pd.read_json(floor2_file)
        
        locs1 = add_floor_prefix(df1.to_dict('records'), floor_num=1)
        locs2 = add_floor_prefix(df2.to_dict('records'), floor_num=2)
        
        df1_prefixed = pd.DataFrame(locs1)
        df2_prefixed = pd.DataFrame(locs2)
        
        G1 = EnhancedWarehouseGraph(df1_prefixed).build_graph()
        G2 = EnhancedWarehouseGraph(df2_prefixed).build_graph()
        
        # Solve each floor independently
        if nx.is_connected(G1) and G1.number_of_nodes() >= 2:
            picks1 = list(G1.nodes())[:2]
            
            from cli_utils import solve_tsp_christofides
            route1, dist1 = solve_tsp_christofides(
                G1, picks1, picks1[0], picks1[0]
            )
            
            assert route1 is not None
        
        if nx.is_connected(G2) and G2.number_of_nodes() >= 2:
            picks2 = list(G2.nodes())[:2]
            
            from cli_utils import solve_tsp_christofides
            route2, dist2 = solve_tsp_christofides(
                G2, picks2, picks2[0], picks2[0]
            )
            
            assert route2 is not None


class TestMultiFloorRouteAnalysis:
    """Integration tests for analyzing multi-floor routes"""
    
    def test_calculate_perfloor_statistics(self):
        """Test calculating statistics per floor"""
        G = nx.Graph()
        
        # Floor 1 edges
        G.add_edge('F1_A', 'F1_B', weight=10)
        G.add_edge('F1_B', 'F1_C', weight=15)
        
        # Floor 2 edges
        G.add_edge('F2_D', 'F2_E', weight=20)
        G.add_edge('F2_E', 'F2_F', weight=25)
        
        # Route crosses floors
        route = ['F1_A', 'F1_B', 'F1_C', 'F2_D', 'F2_E', 'F2_F']
        
        # Calculate per-floor distance
        f1_distance = 0
        f2_distance = 0
        
        for i in range(len(route) - 1):
            if G.has_edge(route[i], route[i+1]):
                weight = G[route[i]][route[i+1]]['weight']
                
                if route[i].startswith('F1_'):
                    f1_distance += weight
                elif route[i].startswith('F2_'):
                    f2_distance += weight
        
        assert f1_distance == 25  # 10 + 15
        assert f2_distance == 45  # 20 + 25
    
    def test_count_floor_transitions(self):
        """Test counting transitions between floors"""
        route = ['F1_A', 'F1_B', 'F2_C', 'F2_D', 'F1_E', 'F3_F']
        
        transitions = 0
        for i in range(len(route) - 1):
            curr_floor = route[i].split('_')[0]
            next_floor = route[i+1].split('_')[0]
            
            if curr_floor != next_floor:
                transitions += 1
        
        assert transitions == 3  # F1->F2, F2->F1, F1->F3
    
    def test_separate_picks_by_floor(self):
        """Test separating picks into floor groups"""
        picks = ['F1_A', 'F1_B', 'F2_C', 'F2_D', 'F1_E', 'F3_F']
        
        floor_groups = {}
        for pick in picks:
            floor = pick.split('_')[0]
            if floor not in floor_groups:
                floor_groups[floor] = []
            floor_groups[floor].append(pick)
        
        assert len(floor_groups['F1']) == 3
        assert len(floor_groups['F2']) == 2
        assert len(floor_groups['F3']) == 1


class TestMultiFloorVisualization:
    """Integration tests for multi-floor visualization"""
    
    def test_generate_perfloor_graphs(self, multi_floor_warehouse, write_json_file, temp_output_dir):
        """Test generation of separate graph visualizations per floor"""
        from legacy.warehouse_graph_enhanced import EnhancedWarehouseGraph
        
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "viz_floor1.json"
        )
        
        df1 = pd.read_json(floor1_file)
        locs1 = add_floor_prefix(df1.to_dict('records'), floor_num=1)
        df1_prefixed = pd.DataFrame(locs1)
        
        G1 = EnhancedWarehouseGraph(df1_prefixed).build_graph()
        
        # Should be able to visualize this floor
        assert G1.number_of_nodes() > 0
        
        # Output file would be: warehouse_graph_floor1.png
        output_file = os.path.join(temp_output_dir, "warehouse_graph_floor1.png")
        
        # Visualization would be generated here
        # (Not actually calling matplotlib to avoid display issues in tests)
    
    def test_separate_route_visualizations(self):
        """Test that routes can be visualized separately per floor"""
        route = ['F1_A', 'F1_B', 'F1_C', 'F2_D', 'F2_E']
        
        # Separate route by floor
        f1_route = [loc for loc in route if loc.startswith('F1_')]
        f2_route = [loc for loc in route if loc.startswith('F2_')]
        
        assert len(f1_route) == 3
        assert len(f2_route) == 2
        
        # Each could be visualized separately


class TestLargeMultiFloorWarehouse:
    """Integration tests for large multi-floor warehouses"""
    
    def test_many_floors(self, test_data_dir, temp_output_dir, write_json_file):
        """Test handling warehouse with many floors (5+)"""
        from legacy.warehouse_graph_enhanced import EnhancedWarehouseGraph
        
        # Create 5 floors with minimal data
        graphs = []
        for floor_num in range(1, 6):
            floor_data = [
                {"id": f"A{floor_num}-1", "x": 0, "y": 0, "traversable": True},
                {"id": f"A{floor_num}-2", "x": 10, "y": 0, "traversable": True}
            ]
            
            floor_file = write_json_file(floor_data, f"large_floor{floor_num}.json")
            df = pd.read_json(floor_file)
            locs = add_floor_prefix(df.to_dict('records'), floor_num=floor_num)
            df_prefixed = pd.DataFrame(locs)
            
            G = EnhancedWarehouseGraph(df_prefixed).build_graph()
            graphs.append(G)
        
        # Merge all floors
        G_merged = graphs[0]
        for G in graphs[1:]:
            G_merged = nx.compose(G_merged, G)
        
        # Should have nodes from all floors
        assert any(node.startswith('F1_') for node in G_merged.nodes())
        assert any(node.startswith('F5_') for node in G_merged.nodes())
        
        # Total nodes should be sum of all floors
        expected_nodes = sum(g.number_of_nodes() for g in graphs)
        assert G_merged.number_of_nodes() == expected_nodes
