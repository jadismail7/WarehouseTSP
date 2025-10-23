# Test Suite for Warehouse TSP Solver

This directory contains comprehensive tests for the Warehouse TSP system.

## Test Coverage Summary

- **Unit Tests**: 72 test methods across 4 files
  - `test_graph_construction.py`: 22 tests (distance calc, graph building, aisle detection, rack inference)
  - `test_tsp_solver.py`: 23 tests (Christofides, 2-opt, pick validation, distance calc, connectivity)
  - `test_physical_loader.py`: 24 tests (JSON loading, pick point expansion, obstacle handling)
  - `test_multi_floor.py`: 27 tests (floor prefixing, graph merging, strategies, transitions)

- **Integration Tests**: 2 files covering complete workflows
  - `test_single_floor_workflow.py`: Enhanced format, physical format, format detection, graph quality
  - `test_multi_floor_workflow.py`: Floor merging, transitions, strategies, visualization

- **End-to-End Tests**: 2 files for CLI testing
  - `test_cli_single_floor.py`: Basic execution, visualization, statistics, error handling
  - `test_cli_multi_floor.py`: Multi-floor strategies, per-floor viz, pick distribution

## Test Structure

```
tests/
├── conftest.py                 # pytest fixtures and configuration
├── unit/                       # Unit tests (72 tests)
│   ├── test_graph_construction.py
│   ├── test_tsp_solver.py
│   ├── test_physical_loader.py
│   └── test_multi_floor.py
├── integration/                # Integration tests
│   ├── test_single_floor_workflow.py
│   └── test_multi_floor_workflow.py
└── e2e/                        # End-to-end CLI tests
    ├── test_cli_single_floor.py
    └── test_cli_multi_floor.py
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test categories
```bash
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/e2e/              # End-to-end tests only
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html tests/
```

### Run specific test
```bash
pytest tests/unit/test_graph_construction.py::TestDistanceCalculation::test_zero_distance
```

### Run tests with markers
```bash
pytest -m unit              # Run only unit tests
pytest -m "not slow"        # Skip slow tests
```

## Installation

### Install test dependencies
```bash
pip install -r requirements-test.txt
```

Or install individually:
```bash
pip install pytest pytest-cov
```

## Test Categories

### Unit Tests (72 tests)

**test_graph_construction.py** (22 tests):
- Distance calculations (Euclidean, zero, negative coords)
- Graph construction from DataFrame
- Edge weight validation
- Aisle detection with DBSCAN
- Rack inference and side assignment
- Graph quality metrics (connectivity, degree)
- Edge cases (empty data, single location, obstacles)

**test_tsp_solver.py** (23 tests):
- Christofides algorithm on various graphs
- 2-opt optimization improvements
- Pick location validation
- Route distance calculation
- Graph connectivity checking
- Start/end point preservation
- Edge cases (single node, disconnected graphs)

**test_physical_loader.py** (24 tests):
- JSON loading and parsing
- Pick point coordinate expansion (center + offset)
- Multiple structure types (rack, aisle, cross_aisle)
- Obstacle handling
- Graph construction from physical layout
- Invalid input handling (missing keys, malformed JSON)
- Location retrieval (all locations, pick-only)

**test_multi_floor.py** (27 tests):
- Floor ID prefixing (F1_, F2_, etc.)
- Multi-floor graph merging
- Floor transition penalties
- Unified vs per-floor strategies
- Floor identification from IDs
- Per-floor route analysis
- Empty floor handling

### Integration Tests

**test_single_floor_workflow.py**:
- Complete workflow: load → build graph → solve TSP
- Enhanced format (x/y/zone) processing
- Physical format (center/pick_points) processing
- Format detection
- Zone-aware routing
- Obstacle handling
- Graph quality validation
- Invalid pick filtering

**test_multi_floor_workflow.py**:
- Multi-floor loading and prefixing
- Floor transition edge creation
- Pick distribution across floors
- Unified strategy execution
- Per-floor strategy execution
- Per-floor statistics calculation
- Per-floor visualization
- Large multi-floor warehouses (5+ floors)

### End-to-End Tests

**test_cli_single_floor.py**:
- Basic CLI execution
- --help command
- Enhanced and physical formats via CLI
- Visualization options (none/graph/route/both)
- Statistics options (--stats/--no-stats)
- Error handling (missing files, invalid JSON)
- Output validation (route, distance)
- File I/O operations

**test_cli_multi_floor.py**:
- Multi-floor CLI arguments
- --warehouse-layout for multiple floors
- --multi-floor-strategy (unified/per-floor)
- Per-floor visualization output
- Per-floor statistics
- Strategy comparison
- Floor transition penalties
- Pick distribution scenarios
- Error handling (mixed formats, duplicates)

## Coverage Goals

- **Unit Tests**: >90% coverage of core algorithms
- **Integration Tests**: >80% coverage of workflows
- **Overall**: >85% code coverage
- **Critical paths**: 100% coverage (TSP solving, graph building)

## Running Tests Locally

```bash
# Run all tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows

# Run specific categories
pytest tests/unit/              # Fast unit tests
pytest tests/integration/       # Medium integration tests
pytest tests/e2e/              # Slower end-to-end tests

# Run with verbose output
pytest -v tests/

# Stop on first failure
pytest -x tests/
```

## Continuous Integration

Tests should be run automatically on:
- Every commit (via pre-commit hooks)
- Pull requests (via GitHub Actions/CI)
- Before releases
- Nightly builds for regression testing

### Example GitHub Actions workflow:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Coverage Goals

- Unit tests: >90% coverage
- Integration tests: >80% coverage
- Overall: >85% coverage
