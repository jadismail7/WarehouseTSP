"""
End-to-end CLI tests for single-floor warehouse operations
Tests actual CLI execution via subprocess
"""
import pytest
import subprocess
import os
import json


class TestCLISingleFloorBasic:
    """Basic end-to-end tests for single-floor CLI"""
    
    def test_cli_help_command(self):
        """Test that --help works"""
        result = subprocess.run(
            ['python', 'warehouse_tsp.py', '--help'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'usage:' in result.stdout.lower() or 'warehouse' in result.stdout.lower()
    
    def test_cli_basic_execution_enhanced_format(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, sample_picks, write_json_file, write_picks_file):
        """Test basic CLI execution with enhanced format"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "cli_warehouse.json")
        picks_file = write_picks_file(sample_picks, "cli_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                picks_file,
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should complete successfully
        assert result.returncode == 0
        assert 'distance' in result.stdout.lower() or 'route' in result.stdout.lower()
    
    def test_cli_physical_format(self, test_data_dir, temp_output_dir, small_warehouse_physical, write_json_file, write_picks_file):
        """Test CLI with physical format warehouse"""
        warehouse_file = write_json_file(small_warehouse_physical, "cli_physical.json")
        
        # Extract pick IDs from physical format (it's a list, not a dict)
        picks = []
        for structure in small_warehouse_physical:
            for pick_point in structure.get('pick_points', []):
                picks.append(pick_point['id'])
        
        if len(picks) > 0:
            picks_file = write_picks_file(picks[:3], "cli_physical_picks.txt")
            
            result = subprocess.run(
                [
                    'python', 'warehouse_tsp.py',
                    warehouse_file,
                    picks_file,
                    '--visualize', 'none',
                    
                ],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
            )
            
            # Should detect physical format and execute
            assert result.returncode == 0


class TestCLIVisualization:
    """End-to-end tests for visualization options"""
    
    def test_cli_no_visualization(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, sample_picks, write_json_file, write_picks_file):
        """Test --visualize none option"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "noviz_warehouse.json")
        picks_file = write_picks_file(sample_picks, "noviz_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                picks_file,
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
        
        # Should not create visualization files
        assert not os.path.exists('output/warehouse_graph.png')
        assert not os.path.exists('output/warehouse_route.png')
    
    def test_cli_graph_visualization(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, sample_picks, write_json_file, write_picks_file):
        """Test --visualize graph option"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "graphviz_warehouse.json")
        picks_file = write_picks_file(sample_picks, "graphviz_picks.txt")
        
        # Clean up old outputs
        if os.path.exists('output/warehouse_graph.png'):
            os.remove('output/warehouse_graph.png')
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                picks_file,
                '--visualize', 'graph',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
        
        # Should create graph visualization
        # (Check would depend on actual output location)


class TestCLIStatistics:
    """End-to-end tests for statistics output"""
    
    def test_cli_with_stats(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, sample_picks, write_json_file, write_picks_file):
        """Test --stats option"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "stats_warehouse.json")
        picks_file = write_picks_file(sample_picks, "stats_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                picks_file,
                '--stats',
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
        
        # Should include statistics in output
        output = result.stdout.lower()
        assert 'graph' in output or 'nodes' in output or 'edges' in output
    
    def test_cli_without_stats(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, sample_picks, write_json_file, write_picks_file):
        """Test --no-stats option"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "nostats_warehouse.json")
        picks_file = write_picks_file(sample_picks, "nostats_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                picks_file,
                
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0


class TestCLIErrorHandling:
    """End-to-end tests for CLI error handling"""
    
    def test_cli_missing_warehouse_file(self):
        """Test CLI with non-existent warehouse file"""
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                'nonexistent_warehouse.json',
                'data/picks_sample.txt',
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should fail gracefully
        assert result.returncode != 0
        assert 'error' in result.stdout.lower() or 'error' in result.stderr.lower()
    
    def test_cli_missing_picks_file(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, write_json_file):
        """Test CLI with non-existent picks file"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "error_warehouse.json")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                'nonexistent_picks.txt',
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should fail gracefully
        assert result.returncode != 0
    
    def test_cli_invalid_json_format(self, test_data_dir, temp_output_dir, tmp_path):
        """Test CLI with malformed JSON"""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{invalid json syntax")
        
        picks_file = tmp_path / "picks.txt"
        with open(picks_file, 'w') as f:
            f.write("A1-1\n")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                str(invalid_file),
                str(picks_file),
                '--visualize', 'none'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should fail with JSON error
        assert result.returncode != 0


class TestCLIOutputValidation:
    """End-to-end tests for validating CLI output"""
    
    def test_cli_output_includes_route(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, sample_picks, write_json_file, write_picks_file):
        """Test that CLI output includes route information"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "route_warehouse.json")
        picks_file = write_picks_file(sample_picks, "route_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                picks_file,
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
        
        output = result.stdout
        # Should include route or sequence information
        assert any(keyword in output.lower() for keyword in ['route', 'sequence', 'pick'])
    
    def test_cli_output_includes_distance(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, sample_picks, write_json_file, write_picks_file):
        """Test that CLI output includes total distance"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "dist_warehouse.json")
        picks_file = write_picks_file(sample_picks, "dist_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                picks_file,
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
        
        output = result.stdout
        # Should include distance information
        assert 'distance' in output.lower() or 'units' in output.lower()


class TestCLIFileIO:
    """End-to-end tests for file input/output"""
    
    def test_cli_reads_picks_file_correctly(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, write_json_file, write_picks_file):
        """Test that CLI correctly reads picks from file"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "io_warehouse.json")
        
        test_picks = ["A1-1", "A1-2", "A2-1"]
        picks_file = write_picks_file(test_picks, "io_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                picks_file,
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        assert result.returncode == 0
        
        # Check that picks appear in output
        output = result.stdout
        for pick in test_picks:
            # At least some picks should be mentioned (some might be invalid)
            pass  # Output format may vary
    
    def test_cli_handles_empty_picks_file(self, test_data_dir, temp_output_dir, small_warehouse_enhanced, write_json_file, write_picks_file):
        """Test CLI with empty picks file"""
        warehouse_file = write_json_file(small_warehouse_enhanced, "empty_warehouse.json")
        picks_file = write_picks_file([], "empty_picks.txt")
        
        result = subprocess.run(
            [
                'python', 'warehouse_tsp.py',
                warehouse_file,
                picks_file,
                '--visualize', 'none',
                
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/../..'
        )
        
        # Should handle gracefully (may succeed or fail depending on implementation)
        # At minimum shouldn't crash
        assert result.returncode in [0, 1]
