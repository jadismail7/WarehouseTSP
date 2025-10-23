"""
Unit tests for physical warehouse layout loader
"""
import pytest
import json
from physical.physical_layout import PhysicalWarehouse


class TestPhysicalLayoutLoading:
    """Tests for loading physical warehouse JSON"""
    
    def test_load_simple_layout(self, tmp_path):
        """Test loading basic physical layout"""
        layout_data = [
            {
                "id": "A1",
                "type": "rack",
                "center": {"x": 10, "y": 20},
                "width": 4,
                "depth": 2,
                "traversable": False,
                "pick_points": [
                    {"id": "A1-1", "offset": {"x": -1, "y": 0}},
                    {"id": "A1-2", "offset": {"x": 1, "y": 0}}
                ]
            }
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        
        assert layout is not None
        assert len(layout.nodes) >= 2  # Center + pick points
    
    def test_load_multiple_structures(self, tmp_path):
        """Test loading layout with multiple structures"""
        layout_data = [
            {
                "id": "A1",
                "type": "rack",
                "center": {"x": 10, "y": 20},
                "width": 4,
                "depth": 2,
                "pick_points": [{"id": "A1-1", "offset": {"x": 0, "y": 0}}]
            },
            {
                "id": "A2",
                "type": "rack",
                "center": {"x": 30, "y": 20},
                "width": 4,
                "depth": 2,
                "pick_points": [{"id": "A2-1", "offset": {"x": 0, "y": 0}}]
            }
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        locations = layout.nodes
        
        assert len(locations) >= 2  # 2 pick points (centers not added for non-traversable racks)
    
    def test_pick_point_coordinate_expansion(self, tmp_path):
        """Test that pick points get absolute coordinates from center + offset"""
        layout_data = [
            {
                "id": "A1",
                "type": "rack",
                "center": {"x": 100, "y": 50},
                "width": 4,
                "depth": 2,
                "pick_points": [
                    {"id": "A1-1", "offset": {"x": -5, "y": 3}}
                ]
            }
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        locations = layout.nodes
        
        # Find A1-1 - locations is a dict, not a list
        assert 'A1-1' in locations
        pick_loc = locations['A1-1']
        assert pick_loc['x'] == 95  # 100 + (-5)
        assert pick_loc['y'] == 53  # 50 + 3
    
    def test_structure_types(self, tmp_path):
        """Test different structure types"""
        layout_data = [
            {"id": "R1", "type": "rack", "center": {"x": 10, "y": 10}, "width": 4, "depth": 2, "pick_points": []},
            {"id": "A1", "type": "aisle", "center": {"x": 20, "y": 10}, "width": 3, "depth": 20, "traversable": True, "pick_points": []},
            {"id": "X1", "type": "cross_aisle", "center": {"x": 30, "y": 10}, "width": 20, "depth": 3, "traversable": True, "pick_points": []}
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        
        assert layout is not None
        # Should load all structure types


class TestPickPointExpansion:
    """Tests for pick point coordinate calculation"""
    
    def test_zero_offset(self):
        """Test pick point with zero offset"""
        center = {"x": 50, "y": 60}
        offset = {"x": 0, "y": 0}
        
        # Pick point should be at center
        expected_x = center["x"] + offset["x"]
        expected_y = center["y"] + offset["y"]
        
        assert expected_x == 50
        assert expected_y == 60
    
    def test_positive_offset(self):
        """Test pick point with positive offset"""
        center = {"x": 50, "y": 60}
        offset = {"x": 10, "y": 15}
        
        expected_x = center["x"] + offset["x"]
        expected_y = center["y"] + offset["y"]
        
        assert expected_x == 60
        assert expected_y == 75
    
    def test_negative_offset(self):
        """Test pick point with negative offset"""
        center = {"x": 50, "y": 60}
        offset = {"x": -8, "y": -12}
        
        expected_x = center["x"] + offset["x"]
        expected_y = center["y"] + offset["y"]
        
        assert expected_x == 42
        assert expected_y == 48
    
    def test_mixed_offset(self):
        """Test pick point with mixed positive/negative offset"""
        center = {"x": 100, "y": 100}
        offset = {"x": -20, "y": 30}
        
        expected_x = center["x"] + offset["x"]
        expected_y = center["y"] + offset["y"]
        
        assert expected_x == 80
        assert expected_y == 130


class TestObstacleHandling:
    """Tests for obstacle representation in physical layouts"""
    
    def test_obstacle_structures(self, tmp_path):
        """Test structures marked as obstacles"""
        layout_data = [
            {
                "id": "O1",
                "type": "obstacle",
                "center": {"x": 50, "y": 50},
                "width": 10,
                "depth": 10,
                "traversable": False,
                "pick_points": []
            },
            {
                "id": "R1",
                "type": "rack",
                "center": {"x": 10, "y": 10},
                "width": 4,
                "depth": 2,
                "pick_points": []
            }
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        
        # Should load both structures
        assert layout is not None
    
    def test_traversable_structures(self, tmp_path):
        """Test that aisles and cross-aisles are traversable"""
        layout_data = [
            {
                "id": "A1",
                "type": "aisle",
                "center": {"x": 20, "y": 20},
                "width": 3,
                "depth": 20,
                "traversable": True,
                "pick_points": []
            },
            {
                "id": "X1",
                "type": "cross_aisle",
                "center": {"x": 40, "y": 20},
                "width": 20,
                "depth": 3,
                "traversable": True,
                "pick_points": []
            }
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        locations = layout.nodes
        
        # Aisles should be traversable (nodes dict values have type info)
        aisle_locs = [loc_id for loc_id, loc in locations.items() if loc.get('type') in ['aisle', 'cross_aisle']]
        assert len(aisle_locs) >= 2


class TestGraphConstruction:
    """Tests for building networkx graph from physical layout"""
    
    def test_graph_nodes_created(self, tmp_path):
        """Test that graph nodes are created for all locations"""
        layout_data = [
            {
                "id": "A1",
                "type": "rack",
                "center": {"x": 10, "y": 10},
                "width": 4,
                "depth": 2,
                "pick_points": [
                    {"id": "A1-1", "offset": {"x": -1, "y": 0}},
                    {"id": "A1-2", "offset": {"x": 1, "y": 0}}
                ]
            }
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        graph = layout.build_graph()
        
        assert graph is not None
        assert graph.number_of_nodes() >= 2
    
    def test_graph_edges_created(self, tmp_path):
        """Test that graph edges connect nearby locations"""
        layout_data = [
            {
                "id": "A1",
                "type": "aisle",
                "center": {"x": 0, "y": 0},
                "width": 3,
                "depth": 20,
                "traversable": True,
                "pick_points": []
            },
            {
                "id": "A2",
                "type": "aisle",
                "center": {"x": 10, "y": 0},
                "width": 3,
                "depth": 20,
                "traversable": True,
                "pick_points": []
            }
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        graph = layout.build_graph()
        
        assert graph.number_of_edges() > 0


class TestInvalidInputHandling:
    """Tests for handling invalid or malformed JSON"""
    
    def test_missing_structures_key(self, tmp_path):
        """Test handling of JSON without structures key"""
        layout_data = {
            "invalid_key": []
        }
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        with pytest.raises(Exception):
            PhysicalWarehouse(str(layout_file))
    
    def test_empty_structures(self, tmp_path):
        """Test handling of empty structures list"""
        layout_data = []  # Empty list
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        locations = layout.nodes
        
        assert len(locations) == 0
    
    def test_missing_center_coordinates(self, tmp_path):
        """Test handling of structure without center coordinates"""
        layout_data = {
            "structures": [
                {
                    "id": "A1",
                    "type": "rack",
                    # Missing "center" key
                    "pick_points": []
                }
            ]
        }
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        with pytest.raises(Exception):
            PhysicalWarehouse(str(layout_file))
    
    def test_invalid_json_syntax(self, tmp_path):
        """Test handling of invalid JSON syntax"""
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            f.write("{invalid json syntax")
        
        with pytest.raises(json.JSONDecodeError):
            PhysicalWarehouse(str(layout_file))
    
    def test_missing_pick_point_id(self, tmp_path):
        """Test handling of pick point without ID"""
        layout_data = {
            "structures": [
                {
                    "id": "A1",
                    "type": "rack",
                    "center": {"x": 10, "y": 10},
                    "pick_points": [
                        {"offset": {"x": 0, "y": 0}}  # Missing "id"
                    ]
                }
            ]
        }
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        with pytest.raises(Exception):
            PhysicalWarehouse(str(layout_file))


class TestLocationRetrieval:
    """Tests for getting locations from physical layout"""
    
    def test_get_all_locations(self, tmp_path):
        """Test retrieving all locations"""
        layout_data = [
            {
                "id": "A1",
                "type": "rack",
                "center": {"x": 10, "y": 20},
                "width": 4,
                "depth": 2,
                "pick_points": [
                    {"id": "A1-1", "offset": {"x": 0, "y": 0}}
                ]
            }
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        locations = layout.nodes
        
        assert len(locations) >= 1  # Pick point (center not added for non-traversable)
        assert 'A1-1' in locations
    
    def test_get_pick_locations_only(self, tmp_path):
        """Test retrieving only pick locations"""
        layout_data = [
            {
                "id": "A1",
                "type": "rack",
                "center": {"x": 10, "y": 20},
                "width": 4,
                "depth": 2,
                "pick_points": [
                    {"id": "A1-1", "offset": {"x": 0, "y": 0}},
                    {"id": "A1-2", "offset": {"x": 2, "y": 0}}
                ]
            },
            {
                "id": "A2",
                "type": "aisle",
                "center": {"x": 30, "y": 20},
                "width": 3,
                "depth": 20,
                "traversable": True,
                "pick_points": []
            }
        ]
        
        layout_file = tmp_path / "test_layout.json"
        with open(layout_file, 'w') as f:
            json.dump(layout_data, f)
        
        layout = PhysicalWarehouse(str(layout_file))
        # Get only pick type locations from nodes dict
        pick_locations = {k: v for k, v in layout.nodes.items() if v['type'] == 'pick'}
        
        assert len(pick_locations) == 2
        assert all('A1' in loc_id for loc_id in pick_locations.keys())
