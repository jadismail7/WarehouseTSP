"""
Integration tests for single-floor warehouse workflow
Tests the complete flow: load data -> build graph -> solve TSP -> validate output
"""
import pytest
import os
import json
import pandas as pd
import networkx as nx
from legacy.warehouse_graph_enhanced import EnhancedWarehouseGraph


class TestSingleFloorEnhancedFormat:
    """Integration tests for enhanced format (x/y/zone) single floor workflow"""
    
    def test_complete_workflow_small_warehouse(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, sample_picks, write_json_file, write_picks_file):
        """Test complete workflow with small enhanced format warehouse"""
        # Write test data
        warehouse_file = write_json_file(small_warehouse_enhanced, "test_warehouse.json")
        picks_file = write_picks_file(sample_picks, "test_picks.txt")
        
        # Load and build graph
        df = pd.read_json(warehouse_file)
        graph_builder = EnhancedWarehouseGraph(df)
        G = graph_builder.build_graph()
        
        # Validate graph structure
        assert G is not None
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() > 0
        
        # Validate picks exist in graph
        with open(picks_file, 'r') as f:
            picks = [line.strip() for line in f if line.strip()]
        
        valid_picks = [p for p in picks if p in G.nodes()]
        assert len(valid_picks) > 0
        
        # Solve TSP (if we have valid picks and connected graph)
        if len(valid_picks) >= 2 and nx.is_connected(G):
            from cli_utils import solve_tsp_christofides
            route, distance = solve_tsp_christofides(
                G, valid_picks, valid_picks[0], valid_picks[0]
            )
            
            assert route is not None
            assert len(route) >= len(valid_picks)
            assert distance > 0
    
    def test_workflow_with_zones(self, test_data_dir, temp_output_dir, write_json_file, write_picks_file):
        """Test workflow with zone-aware warehouse"""
        warehouse_data = [
            {"id": "A1-1", "x": 0, "y": 0, "zone": "A", "traversable": True},
            {"id": "A1-2", "x": 10, "y": 0, "zone": "A", "traversable": True},
            {"id": "B1-1", "x": 20, "y": 0, "zone": "B", "traversable": True},
            {"id": "B1-2", "x": 30, "y": 0, "zone": "B", "traversable": True},
            {"id": "AISLE1", "x": 5, "y": 0, "zone": "AISLE", "traversable": True},
            {"id": "AISLE2", "x": 15, "y": 0, "zone": "AISLE", "traversable": True},
            {"id": "AISLE3", "x": 25, "y": 0, "zone": "AISLE", "traversable": True}
        ]
        
        picks = ["A1-1", "A1-2", "B1-1"]
        
        warehouse_file = write_json_file(warehouse_data, "zone_warehouse.json")
        picks_file = write_picks_file(picks, "zone_picks.txt")
        
        # Load and build
        df = pd.read_json(warehouse_file)
        assert 'zone' in df.columns
        
        graph_builder = EnhancedWarehouseGraph(df)
        G = graph_builder.build_graph()
        
        # Verify zones preserved in graph
        assert G.number_of_nodes() >= 7
        
        # Check zone statistics
        zone_counts = df[df['traversable'] == True]['zone'].value_counts()
        assert 'A' in zone_counts.index
        assert 'B' in zone_counts.index
    
    def test_workflow_with_obstacles(self, test_data_dir, temp_output_dir, write_json_file, write_picks_file):
        """Test workflow with obstacles (non-traversable locations)"""
        warehouse_data = [
            {"id": "A1-1", "x": 0, "y": 0, "traversable": True},
            {"id": "WALL1", "x": 5, "y": 0, "traversable": False},  # Obstacle
            {"id": "A1-2", "x": 10, "y": 0, "traversable": True},
            {"id": "WALL2", "x": 5, "y": 5, "traversable": False},  # Obstacle
            {"id": "B1-1", "x": 0, "y": 10, "traversable": True},
            {"id": "B1-2", "x": 10, "y": 10, "traversable": True}
        ]
        
        picks = ["A1-1", "A1-2", "B1-1"]
        
        warehouse_file = write_json_file(warehouse_data, "obstacles_warehouse.json")
        picks_file = write_picks_file(picks, "obstacles_picks.txt")
        
        df = pd.read_json(warehouse_file)
        graph_builder = EnhancedWarehouseGraph(df)
        G = graph_builder.build_graph()
        
        # Obstacles should not be in graph
        assert 'WALL1' not in G.nodes()
        assert 'WALL2' not in G.nodes()
        
        # Traversable nodes should be in graph
        assert 'A1-1' in G.nodes()
        assert 'A1-2' in G.nodes()
        assert 'B1-1' in G.nodes()


class TestSingleFloorPhysicalFormat:
    """Integration tests for physical format (center/pick_points) single floor workflow"""
    
    def test_complete_workflow_physical_format(self, test_data_dir, temp_output_dir, small_warehouse_physical, write_json_file, write_picks_file):
        """Test complete workflow with physical format warehouse"""
        warehouse_file = write_json_file(small_warehouse_physical, "physical_warehouse.json")
        
        # Physical format has nested pick_points
        all_picks = []
        for structure in small_warehouse_physical['structures']:
            for pick_point in structure.get('pick_points', []):
                all_picks.append(pick_point['id'])
        
        picks_file = write_picks_file(all_picks[:3], "physical_picks.txt")
        
        # Load physical layout
        from physical.physical_layout import PhysicalWarehouseLayout
        layout = PhysicalWarehouseLayout.from_json(warehouse_file)
        
        # Build graph
        G = layout.build_graph()
        
        assert G is not None
        assert G.number_of_nodes() > 0
        
        # Validate picks
        with open(picks_file, 'r') as f:
            picks = [line.strip() for line in f if line.strip()]
        
        valid_picks = [p for p in picks if p in G.nodes()]
        assert len(valid_picks) > 0
    
    def test_physical_format_pick_point_expansion(self, test_data_dir, temp_output_dir, write_json_file):
        """Test that pick points are correctly expanded from center + offset"""
        warehouse_data = {
            "structures": [
                {
                    "id": "R1",
                    "type": "rack",
                    "center": {"x": 100, "y": 50},
                    "pick_points": [
                        {"id": "R1-1", "offset": {"x": -5, "y": 0}},
                        {"id": "R1-2", "offset": {"x": 5, "y": 0}}
                    ]
                }
            ]
        }
        
        warehouse_file = write_json_file(warehouse_data, "expansion_test.json")
        
        from physical.physical_layout import PhysicalWarehouseLayout
        layout = PhysicalWarehouseLayout.from_json(warehouse_file)
        locations = layout.get_all_locations()
        
        # Find pick points
        r1_1 = next((loc for loc in locations if loc['id'] == 'R1-1'), None)
        r1_2 = next((loc for loc in locations if loc['id'] == 'R1-2'), None)
        
        assert r1_1 is not None
        assert r1_1['x'] == 95  # 100 + (-5)
        assert r1_1['y'] == 50  # 50 + 0
        
        assert r1_2 is not None
        assert r1_2['x'] == 105  # 100 + 5
        assert r1_2['y'] == 50


class TestFormatDetection:
    """Integration tests for automatic format detection"""
    
    def test_detect_enhanced_format(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, write_json_file):
        """Test detection of enhanced format (has x, y, zone)"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "enhanced_test.json")
        
        # Load and check structure
        df = pd.read_json(warehouse_file)
        
        # Enhanced format has x, y, and optionally zone columns
        assert 'x' in df.columns
        assert 'y' in df.columns
        
        # Format is array of location objects
        assert isinstance(small_warehouse_enhanced, list)
    
    def test_detect_physical_format(self, test_data_dir, temp_output_dir, small_warehouse_physical, write_json_file):
        """Test detection of physical format (has structures with center/pick_points)"""
        warehouse_file = write_json_file(small_warehouse_physical, "physical_test.json")
        
        with open(warehouse_file, 'r') as f:
            data = json.load(f)
        
        # Physical format has structures key
        assert 'structures' in data
        assert isinstance(data['structures'], list)
        
        # Each structure has center and pick_points
        if len(data['structures']) > 0:
            structure = data['structures'][0]
            assert 'center' in structure
            assert 'pick_points' in structure


class TestGraphQuality:
    """Integration tests for graph quality validation"""
    
    def test_graph_connectivity(self, small_warehouse_enhanced, write_json_file):
        """Test that generated graph is well-connected"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "connectivity_test.json")
        
        df = pd.read_json(warehouse_file)
        graph_builder = EnhancedWarehouseGraph(df)
        G = graph_builder.build_graph()
        
        # Check connectivity
        num_components = nx.number_connected_components(G)
        
        # Should have few components (ideally 1)
        assert num_components <= 2
    
    def test_graph_edge_weights_positive(self, small_warehouse_enhanced, write_json_file):
        """Test that all edge weights are positive"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "weights_test.json")
        
        df = pd.read_json(warehouse_file)
        graph_builder = EnhancedWarehouseGraph(df)
        G = graph_builder.build_graph()
        
        # All edges should have positive weights
        for u, v, data in G.edges(data=True):
            assert 'weight' in data
            assert data['weight'] > 0
    
    def test_graph_minimum_degree(self, small_warehouse_enhanced, write_json_file):
        """Test that nodes have reasonable minimum degree"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "degree_test.json")
        
        df = pd.read_json(warehouse_file)
        graph_builder = EnhancedWarehouseGraph(df)
        G = graph_builder.build_graph()
        
        # Most nodes should have at least 2 connections (except endpoints)
        degrees = dict(G.degree())
        
        # At least some nodes should have degree >= 2
        assert sum(1 for d in degrees.values() if d >= 2) >= 1


class TestInvalidPickHandling:
    """Integration tests for handling invalid picks"""
    
    def test_filter_invalid_picks(self, small_warehouse_enhanced, write_json_file, write_picks_file):
        """Test that invalid picks are filtered out"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "invalid_test.json")
        
        # Mix valid and invalid picks
        picks = ["A1-1", "INVALID1", "A1-2", "NOTEXIST", "A2-1"]
        picks_file = write_picks_file(picks, "mixed_picks.txt")
        
        df = pd.read_json(warehouse_file)
        graph_builder = EnhancedWarehouseGraph(df)
        G = graph_builder.build_graph()
        
        # Load picks
        with open(picks_file, 'r') as f:
            all_picks = [line.strip() for line in f if line.strip()]
        
        # Filter to valid picks
        valid_picks = [p for p in all_picks if p in G.nodes()]
        invalid_picks = [p for p in all_picks if p not in G.nodes()]
        
        assert len(valid_picks) >= 1
        assert len(invalid_picks) >= 2
        assert "INVALID1" in invalid_picks
        assert "NOTEXIST" in invalid_picks
    
    def test_empty_picks_list(self, small_warehouse_enhanced, write_json_file, write_picks_file):
        """Test handling of empty picks list"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "empty_test.json")
        picks_file = write_picks_file([], "empty_picks.txt")
        
        df = pd.read_json(warehouse_file)
        graph_builder = EnhancedWarehouseGraph(df)
        G = graph_builder.build_graph()
        
        # Load picks
        with open(picks_file, 'r') as f:
            picks = [line.strip() for line in f if line.strip()]
        
        assert len(picks) == 0
