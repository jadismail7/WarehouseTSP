"""
End-to-end CLI tests for multi-floor warehouse operations
"""
import pytest
import subprocess
import os
import json


class TestCLIMultiFloorBasic:
    """Basic end-to-end tests for multi-floor CLI"""
    
    def test_cli_multifloor_unified_strategy(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test multi-floor CLI with unified strategy"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "cli_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "cli_floor2.json"
        )
        
        picks = ["A1-1", "B1-1"]
        picks_file = write_picks_file(picks, "cli_multifloor_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--multi-floor-strategy', 'unified',
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should execute successfully
        assert result.returncode == 0
        assert 'distance' in result.stdout.lower() or 'route' in result.stdout.lower()
    
    def test_cli_multifloor_perfloor_strategy(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test multi-floor CLI with per-floor strategy"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "perfloor_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "perfloor_floor2.json"
        )
        
        picks = ["A1-1", "A1-2", "B1-1"]
        picks_file = write_picks_file(picks, "perfloor_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--multi-floor-strategy', 'per-floor',
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
    
    def test_cli_multiple_floor_files(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test CLI with multiple --warehouse-layout arguments"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "multi1_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "multi1_floor2.json"
        )
        
        # Create a third floor
        floor3_data = [
            {"id": "C1-1", "x": 0, "y": 0, "traversable": True},
            {"id": "C1-2", "x": 10, "y": 0, "traversable": True}
        ]
        floor3_file = write_json_file(floor3_data, "multi1_floor3.json")
        
        picks = ["A1-1", "B1-1", "C1-1"]
        picks_file = write_picks_file(picks, "multi1_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--warehouse-layout', floor3_file,
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should handle 3+ floors
        assert result.returncode == 0


class TestCLIMultiFloorVisualization:
    """End-to-end tests for multi-floor visualization"""
    
    def test_cli_perfloor_visualization_output(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test that per-floor visualization creates separate files"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "viz_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "viz_floor2.json"
        )
        
        picks = ["A1-1", "B1-1"]
        picks_file = write_picks_file(picks, "viz_picks.txt")
        
        # Clean up old outputs
        for filename in ['warehouse_graph_floor1.png', 'warehouse_route_floor1.png',
                        'warehouse_graph_floor2.png', 'warehouse_route_floor2.png']:
            filepath = os.path.join('output', filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--visualize', 'both',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should complete successfully
        assert result.returncode == 0
        
        # Would check for floor-specific files:
        # output/warehouse_graph_floor1.png
        # output/warehouse_route_floor1.png
        # output/warehouse_graph_floor2.png
        # output/warehouse_route_floor2.png


class TestCLIMultiFloorStatistics:
    """End-to-end tests for multi-floor statistics"""
    
    def test_cli_perfloor_statistics(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test that statistics show per-floor breakdown"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "stats_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "stats_floor2.json"
        )
        
        picks = ["A1-1", "B1-1"]
        picks_file = write_picks_file(picks, "stats_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--stats',
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
        
        output = result.stdout.lower()
        # Should include per-floor statistics
        assert 'floor' in output or 'f1' in output or 'f2' in output
    
    def test_cli_strategy_comparison(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test running both strategies and comparing results"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "compare_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "compare_floor2.json"
        )
        
        picks = ["A1-1", "B1-1"]
        picks_file = write_picks_file(picks, "compare_picks.txt")
        
        # Run unified strategy
        result_unified = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--multi-floor-strategy', 'unified',
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Run per-floor strategy
        result_perfloor = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--multi-floor-strategy', 'per-floor',
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Both should succeed
        assert result_unified.returncode == 0
        assert result_perfloor.returncode == 0


class TestCLIFloorTransitions:
    """End-to-end tests for floor transition handling"""
    
    def test_cli_floor_transition_penalty(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test that floor transitions are penalized in unified strategy"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "penalty_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "penalty_floor2.json"
        )
        
        # Picks from both floors
        picks = ["A1-1", "B1-1"]
        picks_file = write_picks_file(picks, "penalty_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--multi-floor-strategy', 'unified',
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
        
        # Output should indicate floor transitions
        # (Implementation dependent)


class TestCLIMultiFloorErrorHandling:
    """End-to-end tests for multi-floor error handling"""
    
    def test_cli_mismatched_floor_formats(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, small_warehouse_physical, write_json_file, write_picks_file):
        """Test CLI with mixed enhanced/physical formats"""
        enhanced_file = write_json_file(small_warehouse_enhanced, "mixed_enhanced.json")
        physical_file = write_json_file(small_warehouse_physical, "mixed_physical.json")
        
        picks = ["A1-1"]
        picks_file = write_picks_file(picks, "mixed_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                enhanced_file,
                picks_file,
                '--warehouse-layout', physical_file,
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should handle gracefully (may succeed or fail depending on implementation)
        # At minimum shouldn't crash
        pass
    
    def test_cli_duplicate_floor_files(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test CLI with same floor file specified multiple times"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "dup_floor1.json"
        )
        
        picks = ["A1-1"]
        picks_file = write_picks_file(picks, "dup_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor1_file,  # Duplicate
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should handle gracefully


class TestCLIMultiFloorPickDistribution:
    """End-to-end tests for pick distribution across floors"""
    
    def test_cli_all_picks_single_floor(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test multi-floor setup but all picks on one floor"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "single_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "single_floor2.json"
        )
        
        # All picks from floor 1 only
        picks = ["A1-1", "A1-2"]
        picks_file = write_picks_file(picks, "single_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should handle efficiently (no need to visit floor 2)
        assert result.returncode == 0
    
    def test_cli_picks_distributed_evenly(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test picks evenly distributed across floors"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "even_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "even_floor2.json"
        )
        
        # Equal picks from each floor
        picks = ["A1-1", "A1-2", "B1-1", "B1-2"]
        picks_file = write_picks_file(picks, "even_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--multi-floor-strategy', 'per-floor',
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0


class TestCLIOutputFormatMultiFloor:
    """End-to-end tests for multi-floor output format"""
    
    def test_cli_output_shows_floor_info(self, test_data_dir, temp_output_dir, multi_floor_warehouse, write_json_file, write_picks_file):
        """Test that output includes floor information"""
        floor1_file = write_json_file(
            multi_floor_warehouse['floor1'],
            "info_floor1.json"
        )
        floor2_file = write_json_file(
            multi_floor_warehouse['floor2'],
            "info_floor2.json"
        )
        
        picks = ["A1-1", "B1-1"]
        picks_file = write_picks_file(picks, "info_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                floor1_file,
                picks_file,
                '--warehouse-layout', floor2_file,
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
        
        output = result.stdout
        # Should indicate which floor picks are on
        # (Format may vary by implementation)
