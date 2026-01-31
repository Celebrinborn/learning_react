# Project Rules for AI Assistants

## Hexagonal Architecture Rules

- **Terminology**: Use "provider" for I/O implementations, "interface" for contracts, "domain" for business logic
- **builder.py**: Only this file imports concrete providers. All other code depends solely on interfaces and models
- **Provider Implementation**: 
  - `__init__()` can have any signature/parameters needed for that provider
  - After initialization, providers must implement ALL interface methods with EXACT signatures
  - No additional public methods beyond the interface contract

## Testing Philosophy

- **Test at the boundaries**: Focus on testing interfaces and public contracts, not implementation details
- **Behavior over implementation**: Verify correct outputs and behavior, not how the code achieves it
- **Backend Framework**: Use pytest for all Python tests
- **Frontend Framework**: Use Vitest and React Testing Library for all React component tests

## Running Tests

### Backend Tests
**Must run from `src/backend` directory with virtual environment activated:**
```powershell
cd 'C:\Path\To\Your\Workspace\src\backend'; .\env\Scripts\Activate.ps1; pytest
```

### Frontend Tests
**Must run from `src/frontend` directory:**
```powershell
cd 'C:\Path\To\Your\Workspace\src\frontend'; npm test
```
*(Replace `C:\Path\To\Your\Workspace` with your actual repository path)*
