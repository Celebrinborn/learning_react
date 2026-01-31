/**
 * Frontend Test Suite README
 * 
 * This directory contains unit tests for React components and hooks using Vitest
 * and React Testing Library. Tests follow behavior-driven style ("it does X")
 * and focus on testing at the edges (user-visible behavior, not implementation).
 */

# Frontend Testing Guide

**IMPORTANT**: All commands must be run from the `src/frontend` directory.

## Setup

1. Navigate to frontend directory:
```powershell
cd src\frontend
```

2. Install dependencies (if not already done):
```powershell
npm install
```

## Running Tests

Run all tests:
```powershell
npm test
```

Run tests in watch mode (re-runs on file changes):
```powershell
npm run test:watch
```

Run tests with UI (visual test runner):
```powershell
npm run test:ui
```

Run with coverage report:
```powershell
npm run test:coverage
```

## Test Philosophy

### Test at the Edges
- Focus on **what the user sees and does**
- Test **behavior**, not implementation details
- Avoid testing internal state or private methods

### "It Does" Style
Tests describe behavior from the user's perspective:
```typescript
it('displays the title text', () => { ... })
it('calls logout when button is clicked', () => { ... })
it('renders children content', () => { ... })
```

### What to Test
✅ **DO test:**
- Rendered output (text, elements, images)
- User interactions (clicks, typing, form submissions)
- Conditional rendering based on props/state
- Accessibility (roles, labels, keyboard navigation)

❌ **DON'T test:**
- CSS class names or styling details
- Internal component state
- Implementation details (how something is done)
- Third-party libraries (assume they work)

## Test Structure

- `setup.ts` - Test environment configuration
- `*.test.tsx` - Component and hook tests

## Running Specific Tests

```powershell
# Run a specific test file
npm test Box.test.tsx

# Run tests matching a pattern
npm test -- --grep "TopNav"

# Run in watch mode for specific file
npm test -- Box.test.tsx --watch
```

## Common Patterns

### Rendering with Providers
```typescript
const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={webLightTheme}>
      {component}
    </FluentProvider>
  );
};
```

### Testing User Interactions
```typescript
const user = userEvent.setup();
await user.click(button);
await user.type(input, 'text');
```

### Mocking Modules
```typescript
vi.mock('../providers/auth', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
  },
}));
```

## Coverage Goals

Aim for high coverage of:
- All exported components
- Custom hooks
- Critical user flows
- Error states and edge cases
