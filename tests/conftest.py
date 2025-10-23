"""
Pytest configuration and shared fixtures for warehouse TSP tests
"""
import pytest
import json
import os
import tempfile
from pathlib import Path

# Add parent directory to path so we can import modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_data_dir():
    """Return path to test data directory"""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def small_warehouse_enhanced():
    """Small test warehouse in enhanced format (x, y, type, zone)"""
    return [
        {"id": "Staging_1", "x": 10, "y": 10, "type": "staging", "zone": "receiving", 
         "width": 8, "depth": 6, "traversable": True},
        {"id": "A1-1", "x": 20, "y": 20, "type": "picking", "zone": "A", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "A1-2", "x": 20, "y": 30, "type": "picking", "zone": "A", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "A2-1", "x": 30, "y": 20, "type": "picking", "zone": "A", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "A2-2", "x": 30, "y": 30, "type": "picking", "zone": "A", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "B1-1", "x": 45, "y": 20, "type": "picking", "zone": "B", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "B1-2", "x": 45, "y": 30, "type": "picking", "zone": "B", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "CrossAisle_1", "x": 35, "y": 25, "type": "intersection", "zone": "cross_aisle", 
         "width": 6, "depth": 6, "traversable": True},
        {"id": "Obstacle_1", "x": 50, "y": 50, "type": "obstacle", "zone": "blocked", 
         "width": 10, "depth": 10, "traversable": False}
    ]


@pytest.fixture
def small_warehouse_physical():
    """Small test warehouse in physical format (center, pick_points)"""
    return [
        {
            "id": "Staging_Area",
            "center": {"x": 20, "y": 20},
            "width": 10,
            "depth": 8,
            "type": "staging",
            "traversable": True
        },
        {
            "id": "Rack_A1",
            "center": {"x": 40, "y": 30},
            "width": 3,
            "depth": 20,
            "type": "rack",
            "traversable": False,
            "pick_points": [
                {"id": "A1-1", "offset": {"x": -2, "y": -8}},
                {"id": "A1-2", "offset": {"x": -2, "y": 0}},
                {"id": "A1-3", "offset": {"x": -2, "y": 8}},
                {"id": "A1-4", "offset": {"x": 2, "y": -8}},
                {"id": "A1-5", "offset": {"x": 2, "y": 0}},
                {"id": "A1-6", "offset": {"x": 2, "y": 8}}
            ]
        },
        {
            "id": "MainAisle",
            "center": {"x": 30, "y": 30},
            "width": 6,
            "depth": 40,
            "type": "aisle",
            "traversable": True,
            "pick_points": [
                {"id": "Aisle_N", "offset": {"x": 0, "y": -15}},
                {"id": "Aisle_C", "offset": {"x": 0, "y": 0}},
                {"id": "Aisle_S", "offset": {"x": 0, "y": 15}}
            ]
        }
    ]


@pytest.fixture
def sample_picks():
    """Sample pick list"""
    return ["A1-1", "A1-2", "A2-1", "B1-1"]


@pytest.fixture
def write_json_file(temp_output_dir):
    """Helper to write JSON data to temporary file"""
    def _write(data, filename):
        filepath = temp_output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return filepath
    return _write


@pytest.fixture
def write_picks_file(temp_output_dir):
    """Helper to write picks list to temporary file"""
    def _write(picks, filename):
        filepath = temp_output_dir / filename
        with open(filepath, 'w') as f:
            f.write('\n'.join(picks))
        return filepath
    return _write


@pytest.fixture
def multi_floor_warehouse():
    """Two-floor warehouse configuration"""
    floor1 = [
        {"id": "Staging_1", "x": 10, "y": 10, "type": "staging", "zone": "receiving", 
         "width": 8, "depth": 6, "traversable": True},
        {"id": "A1-1", "x": 20, "y": 20, "type": "picking", "zone": "A", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "A1-2", "x": 20, "y": 30, "type": "picking", "zone": "A", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "B1-1", "x": 35, "y": 20, "type": "picking", "zone": "B", 
         "width": 2, "depth": 2, "traversable": True}
    ]
    
    floor2 = [
        {"id": "Staging_1", "x": 10, "y": 10, "type": "staging", "zone": "receiving", 
         "width": 8, "depth": 6, "traversable": True},
        {"id": "C1-1", "x": 20, "y": 20, "type": "picking", "zone": "C", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "C1-2", "x": 20, "y": 30, "type": "picking", "zone": "C", 
         "width": 2, "depth": 2, "traversable": True},
        {"id": "D1-1", "x": 35, "y": 20, "type": "picking", "zone": "D", 
         "width": 2, "depth": 2, "traversable": True}
    ]
    
    return {"floor1": floor1, "floor2": floor2}


@pytest.fixture(autouse=True)
def cleanup_output_files():
    """Automatically clean up test output files after each test"""
    yield
    # Cleanup happens after test
    output_dir = Path("output")
    if output_dir.exists():
        test_files = [
            "test_*.png",
            "warehouse_test_*.png",
            "*_test_*.png"
        ]
        for pattern in test_files:
            for file in output_dir.glob(pattern):
                try:
                    file.unlink()
                except:
                    pass
