# Project Rules for AI Assistants

## Hexagonal Architecture Rules

- **Terminology**: Use "provider" for I/O implementations, "interface" for contracts, "domain" for business logic
- **builder.py**: Only this file imports concrete providers. All other code depends solely on interfaces and models
- **Provider Implementation**: 
  - `__init__()` can have any signature/parameters needed for that provider
  - After initialization, providers must implement ALL interface methods with EXACT signatures
  - No additional public methods beyond the interface contract

## Style Guide

### Python Code Style
- **Type Hints**: Full type annotations required for all functions, parameters, and return types
- **Pylance Strict Mode**: Code must pass Pylance strict type checking with zero errors
- **Variable Annotations**: Explicitly annotate container types when initialized empty (e.g., `items: List[Item] = []`)
- **No `Any` Types**: Avoid using `Any` unless absolutely necessary; prefer specific types or protocols
- **Return Types**: Always specify return types, including `None` for procedures
- **Avoid Optional**: Minimize use of `Optional` types when practical; design functions to return concrete types
- **Early Returns (Guard Clauses)**: Check failure conditions at the start of functions and return/raise early, then write main logic with reduced nesting

## Testing Philosophy

- **Test at the boundaries**: Focus on testing interfaces and public contracts, not implementation details
- **Behavior over implementation**: Verify correct outputs and behavior, not how the code achieves it
- **Backend Framework**: Use pytest for all Python tests
- **Frontend Framework**: Use Vitest and React Testing Library for all React component tests
- **Test Organization**: Tests are organized into three categories:
  - `tests/unit/` - Fast, isolated tests with no I/O or external dependencies
  - `tests/integration/` - Tests that verify multiple components work together
  - `tests/e2e/` - End-to-end tests that test the full system

### After Code Changes
When updating code, you must ALWAYS complete these steps as the final verification:
1. **Run relevant unit tests** using the `runTests` tool to verify your changes work correctly
2. **Verify code passes Pylance strict type checking** with zero errors using the `get_errors` tool
3. Do NOT run integration or e2e tests unless specifically requested

**CRITICAL**: Running tests is MANDATORY after any code change - this is your last step before considering the task complete.

### After Bug Fixes
- After fixing a bug, you must update or add tests to ensure this bug cannot happen again—unless the existing tests already fail due to the bug. If the tests already fail, you do not need to add a new test, as the bug is already caught by the current test suite.

## Running Development Servers

**Prefer VSCode tasks:** Run Backend, Run Frontend, Run All (Backend + Frontend)

## Running Tests

### All Tests (Backend + Frontend)
```powershell
cd 'C:\Path\To\Your\Workspace\src\backend'; .\env\Scripts\Activate.ps1; pytest; cd ..\frontend; npm test
```

### Backend Tests
**Must run from `src/backend` directory with virtual environment activated:**
```powershell
# All backend tests
cd 'C:\Path\To\Your\Workspace\src\backend'; .\env\Scripts\Activate.ps1; pytest

# Unit tests only (fast, no I/O)
pytest tests/unit/

# Integration tests (tests multiple components together)
pytest tests/integration/

# E2E tests (full system tests)
pytest tests/e2e/
```

### Frontend Tests
**Must run from `src/frontend` directory:**
```powershell
# All frontend tests
cd 'C:\Path\To\Your\Workspace\src\frontend'; npm test

# Unit tests only
npm test -- tests/unit/

# Integration tests
npm test -- tests/integration/

# E2E tests
npm test -- tests/e2e/
```
*(Replace `C:\Path\To\Your\Workspace` with your actual repository path)*


# Avoiding
Do not use pwsh scripts for running tests. Use Built-In > runTests