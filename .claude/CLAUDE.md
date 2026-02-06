# Project Rules for Claude AI

## Hexagonal Architecture
- Use "provider" for I/O, "interface" for contracts, "domain" for business logic
- Only `builder.py` imports concrete providers; all other code depends on interfaces/models
- Providers must implement all interface methods with exact signatures; no extra public methods

## Python Style Guide
- Full type hints for all functions, parameters, and return types
- Code must pass strict type checking (Pylance, pyright) with zero errors
- Explicit variable annotations for empty containers (e.g., `items: List[Item] = []`)
- Avoid `Any` unless necessary; prefer specific types
- Always specify return types, including `None`
- Minimize use of `Optional`; design for concrete types
- Use early returns (guard clauses) to reduce nesting

## Testing Philosophy
- Test interfaces and public contracts, not implementation details
- Verify correct outputs and behavior, not internal logic
- Backend: Use pytest
- Frontend: Use Vitest + React Testing Library
- Test organization:
  - `tests/unit/`: Fast, isolated, no I/O
  - `tests/integration/`: Multiple components together
  - `tests/e2e/`: Full system

### After Code Changes
1. Run relevant unit tests to verify changes
2. Verify strict type checking passes with zero errors
3. Do NOT run integration/e2e tests unless requested

### After Bug Fixes
- After fixing a bug, you must update or add tests to ensure this bug cannot happen again—unless the existing tests already fail due to the bug. If the tests already fail, you do not need to add a new test, as the bug is already caught by the current test suite.

**MANDATORY:** Always run tests after any code change before considering the task complete.

## Running Development Servers
- Prefer VSCode tasks: Run Backend, Run Frontend, Run All

## Running Tests

### All Tests (Backend + Frontend)
```
cd 'C:/Path/To/Your/Workspace/src/backend'; .\env\Scripts\Activate.ps1; pytest; cd ../frontend; npm test
```

### Backend Tests
- Run from `src/backend` with virtual environment activated:
```
cd 'C:/Path/To/Your/Workspace/src/backend'; .\env\Scripts\Activate.ps1; pytest
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Frontend Tests
- Run from `src/frontend`:
```
cd 'C:/Path/To/Your/Workspace/src/frontend'; npm test
npm test -- tests/unit/
npm test -- tests/integration/
npm test -- tests/e2e/
```
*(Replace `C:/Path/To/Your/Workspace` with your actual repo path)*

## Avoid
- Do not use PowerShell scripts for running tests. Use built-in test runners.
