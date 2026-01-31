# Backend Testing

**IMPORTANT**: All commands must be run from the `src/backend` directory with the virtual environment activated.

## Setup

1. Navigate to backend directory:
```powershell
cd src\backend
```

2. Activate virtual environment:
```powershell
.\env\Scripts\Activate.ps1
```

3. Install test dependencies (if not already installed):
```powershell
pip install -e ".[dev]"
```

## Running Tests

Run all tests:
```powershell
pytest
```

Run with verbose output:
```powershell
pytest -v
```

Run with coverage report:
```powershell
pytest --cov=dnd_backend --cov-report=html --cov-report=term
```

View coverage report:
```powershell
# Open htmlcov/index.html in your browser
start htmlcov\index.html
```

## Test Structure

- `conftest.py` - Shared fixtures for all tests
- `test_models.py` - Tests for Pydantic models
- `test_providers.py` - Tests for blob storage providers
- `test_storage.py` - Tests for character storage CRUD operations
- `test_routes.py` - Tests for FastAPI endpoints

## Running Specific Tests

```powershell
# Run a specific test file
pytest tests/test_models.py

# Run a specific test class
pytest tests/test_routes.py::TestCharacterRoutes

# Run a specific test
pytest tests/test_routes.py::TestCharacterRoutes::test_create_character_success

# Run tests and show print statements
pytest -s

# Run with short traceback format (easier to read)
pytest --tb=short
```
