# MotoMatch Development Guide

## Build & Run Commands
- **Development server**: `python run_fixed_app.py`
- **No warnings**: `python run_fixed_app.py --no-warnings` or `run_no_warnings.bat`
- **Production**: `python run_fixed_app.py --production`
- **Dependencies**: `pip install -r requirements.txt`

## Test Commands
- **All tests**: `python -m unittest tests/test_algorithms.py`
- **Single test**: `python -m unittest tests.test_algorithms.TestPageRank.test_pagerank_algorithm`
- **Algorithm test**: `python test_algorithms.py`

## Code Style Guidelines
- **Imports**: stdlib → third-party → local (with blank lines between groups)
- **Naming**: snake_case for functions/vars, PascalCase for classes, UPPER_SNAKE_CASE for constants
- **Private methods**: prefix with underscore `_method_name`
- **Error handling**: Use try-except with `logger.error(f"Error: {str(e)}")` pattern
- **Docstrings**: Triple quotes with Args/Returns sections, include type hints
- **Comments**: Bilingual (Spanish/English) acceptable

## Database
- **Neo4j config**: bolt://localhost:7687, user: neo4j, password: 22446688
- **Mock data fallback**: Set `USE_MOCK_DATA=True` in config if Neo4j unavailable
