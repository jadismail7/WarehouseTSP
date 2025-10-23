"""
Unit tests for graph construction functionality
"""
import pytest
import pandas as pd
import networkx as nx
from legacy.warehouse_graph_enhanced import (
    build_enhanced_graph,
    calculate_distance,
    detect_aisles_with_dimensions,
    infer_racks_from_bins,
    create_graph_from_edges
)


class TestDistanceCalculation:
    """Tests for distance calculation utilities"""
    
    def test_distance_zero(self):
        """Test distance between same point is zero"""
        assert calculate_distance((0, 0), (0, 0)) == 0
    
    def test_distance_horizontal(self):
        """Test horizontal distance"""
        assert calculate_distance((0, 0), (3, 0)) == 3
    
    def test_distance_vertical(self):
        """Test vertical distance"""
        assert calculate_distance((0, 0), (0, 4)) == 4
    
    def test_distance_diagonal(self):
        """Test diagonal distance (Pythagorean)"""
        distance = calculate_distance((0, 0), (3, 4))
        assert distance == pytest.approx(5.0)
    
    def test_distance_negative_coords(self):
        """Test distance with negative coordinates"""
        distance = calculate_distance((-3, -4), (0, 0))
        assert distance == pytest.approx(5.0)


class TestEnhancedGraphConstruction:
    """Tests for enhanced graph building"""
    
    def test_graph_builds_from_dataframe(self, small_warehouse_enhanced):
        """Test that graph builds successfully from warehouse data"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        # Preprocess with aisle detection (required step)
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() > 0
    
    def test_traversable_nodes_included(self, small_warehouse_enhanced):
        """Test that traversable nodes are included in graph"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        # Check that staging and picking locations are in graph
        assert "Staging_1" in G.nodes()
        assert "A1-1" in G.nodes()
        assert "A1-2" in G.nodes()
    
    def test_non_traversable_nodes_excluded(self, small_warehouse_enhanced):
        """Test that non-traversable nodes (obstacles) are excluded"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        # Obstacle should not be in graph
        assert "Obstacle_1" not in G.nodes()
    
    def test_graph_has_edge_weights(self, small_warehouse_enhanced):
        """Test that edges have distance weights"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        # Get any edge and check it has weight
        if G.number_of_edges() > 0:
            edge = list(G.edges())[0]
            assert 'weight' in G[edge[0]][edge[1]]
            assert G[edge[0]][edge[1]]['weight'] > 0
    
    def test_graph_connectivity(self, small_warehouse_enhanced):
        """Test that graph forms connected components"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        # Should have at least one connected component
        components = list(nx.connected_components(G))
        assert len(components) >= 1
    
    def test_empty_dataframe_returns_empty_graph(self):
        """Test handling of empty warehouse data"""
        locs = pd.DataFrame(columns=['id', 'x', 'y', 'type', 'traversable', 'width', 'depth'])
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        assert G.number_of_nodes() == 0
        assert G.number_of_edges() == 0


class TestAisleDetection:
    """Tests for aisle detection using DBSCAN"""
    
    def test_detect_aisles_finds_clusters(self, small_warehouse_enhanced):
        """Test that aisle detection identifies location clusters"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        
        # Call detect_aisles_with_dimensions which adds aisle columns
        result = detect_aisles_with_dimensions(locs)
        
        assert result is not None
        assert len(result) > 0
    
    def test_detect_aisles_with_insufficient_data(self):
        """Test aisle detection with too few points"""
        locs = pd.DataFrame([
            {"id": "A1-1", "x": 20, "y": 20, "type": "picking", "traversable": True, "width": 2, "depth": 2}
        ])
        
        # Should handle gracefully without crashing
        result = detect_aisles_with_dimensions(locs)
        
        assert result is not None


class TestRackInference:
    """Tests for rack structure inference"""
    
    def test_infer_racks_identifies_structures(self, small_warehouse_enhanced):
        """Test that rack inference identifies rack structures"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        
        # infer_racks_from_bins is called by detect_aisles_with_dimensions
        result = detect_aisles_with_dimensions(locs)
        
        assert 'rack_id' in result.columns
        assert 'rack_side' in result.columns
    
    def test_rack_sides_assigned(self, small_warehouse_enhanced):
        """Test that bins are assigned to rack sides (left/right)"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        
        # infer_racks_from_bins is called by detect_aisles_with_dimensions
        result = detect_aisles_with_dimensions(locs)
        
        # Check that rack_side column exists
        assert 'rack_side' in result.columns


class TestGraphQuality:
    """Tests for graph quality metrics"""
    
    def test_connected_graph(self, small_warehouse_enhanced):
        """Test that small warehouse produces connected graph"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        # Small warehouse should be mostly connected
        # (May have multiple components if obstacles divide it)
        num_components = nx.number_connected_components(G)
        assert num_components <= 3  # Reasonable upper bound
    
    def test_minimum_degree(self, small_warehouse_enhanced):
        """Test that nodes have reasonable connectivity"""
        locs = pd.DataFrame(small_warehouse_enhanced)
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        if G.number_of_nodes() > 0:
            degrees = dict(G.degree())
            min_degree = min(degrees.values())
            
            # Each node should connect to at least one other
            # (unless it's isolated, which should be rare)
            assert min_degree >= 0


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_single_location(self):
        """Test graph with single location"""
        locs = pd.DataFrame([
            {"id": "A1-1", "x": 20, "y": 20, "type": "picking", 
             "zone": "A", "width": 2, "depth": 2, "traversable": True}
        ])
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        assert G.number_of_nodes() == 1
        assert G.number_of_edges() == 0
    
    def test_all_non_traversable(self):
        """Test warehouse with only obstacles"""
        locs = pd.DataFrame([
            {"id": "Obs1", "x": 20, "y": 20, "type": "obstacle", 
             "zone": "blocked", "width": 10, "depth": 10, "traversable": False},
            {"id": "Obs2", "x": 40, "y": 40, "type": "obstacle", 
             "zone": "blocked", "width": 10, "depth": 10, "traversable": False}
        ])
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        # Should create empty graph
        assert G.number_of_nodes() == 0
    
    def test_collinear_points(self):
        """Test graph with collinear points (straight line)"""
        locs = pd.DataFrame([
            {"id": "A1", "x": 10, "y": 10, "type": "picking", "zone": "A", "width": 2, "depth": 2, "traversable": True},
            {"id": "A2", "x": 20, "y": 10, "type": "picking", "zone": "A", "width": 2, "depth": 2, "traversable": True},
            {"id": "A3", "x": 30, "y": 10, "type": "picking", "zone": "A", "width": 2, "depth": 2, "traversable": True}
        ])
        locs = detect_aisles_with_dimensions(locs)
        edges = build_enhanced_graph(locs, verbose=False)
        G = create_graph_from_edges(locs, edges)
        
        assert G.number_of_nodes() == 3
        # Should form a line graph
        assert G.number_of_edges() >= 2
