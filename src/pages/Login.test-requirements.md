# Login Component - Test Requirements

## Overview
BDD-style black-box testing specification for the Login component. Tests should focus on **behavior at boundaries** (what the component does) rather than implementation details (how it does it).

## Testing Approach
- **Framework**: Vitest with React Testing Library
- **Style**: Mocha-style `describe/it` syntax
- **Focus**: User behavior and edge cases
- **Mocking**: Mock external dependencies (AuthContext, Router, localStorage)
- **No Network Calls**: All auth operations should be mocked

---

## Test Suite Structure

### `describe('Login Component')`

#### **Rendering & Initial State**

##### `describe('when component first renders')`
- `it('displays the login heading')`
  - **Given**: Component renders
  - **Then**: Shows "Login" heading
  
- `it('displays the welcome subtitle')`
  - **Given**: Component renders
  - **Then**: Shows "Welcome to D&D Stats Sheet"

- `it('displays username input field')`
  - **Given**: Component renders
  - **Then**: Username field is visible with proper label
  - **Edge**: Field should have accessible label (for screen readers)

- `it('displays password input field')`
  - **Given**: Component renders
  - **Then**: Password field is visible with proper label
  - **Edge**: Field type should be "password" (masked input)

- `it('displays submit button')`
  - **Given**: Component renders
  - **Then**: "Login" button is present and enabled

- `it('displays stub authentication note')`
  - **Given**: Component renders
  - **Then**: Shows note about stub auth system

---

#### **Form Validation (HTML5 Built-in)**

##### `describe('form validation')`
- `it('prevents submission when username is empty')`
  - **Given**: Password has value but username is empty
  - **When**: User clicks submit
  - **Then**: Form does not submit (browser validation)
  - **Edge Case**: Tests boundary of required field

- `it('prevents submission when password is empty')`
  - **Given**: Username has value but password is empty
  - **When**: User clicks submit
  - **Then**: Form does not submit (browser validation)
  - **Edge Case**: Tests boundary of required field

- `it('prevents submission when both fields are empty')`
  - **Given**: Both fields empty
  - **When**: User clicks submit
  - **Then**: Form does not submit (browser validation)
  - **Edge Case**: Tests complete absence of input

---

#### **User Interactions**

##### `describe('when user types in username field')`
- `it('updates username value')`
  - **Given**: Component is rendered
  - **When**: User types "testuser" in username field
  - **Then**: Input displays "testuser"
  - **Black Box**: Don't test state, test visible output

- `it('handles special characters in username')`
  - **Given**: Component is rendered
  - **When**: User types "@user#123!"
  - **Then**: Input accepts and displays special characters
  - **Edge Case**: Tests boundary of input acceptance

- `it('handles very long username input')`
  - **Given**: Component is rendered
  - **When**: User types 1000 character string
  - **Then**: Input accepts the value (no maxLength constraint)
  - **Edge Case**: Tests upper boundary behavior

##### `describe('when user types in password field')`
- `it('masks password input')`
  - **Given**: Component is rendered
  - **When**: User types "secret123" in password field
  - **Then**: Input shows masked characters (type="password")
  - **Black Box**: Tests observable behavior, not implementation

- `it('handles empty space as valid password character')`
  - **Given**: Component is rendered
  - **When**: User types "pass word"
  - **Then**: Input accepts spaces
  - **Edge Case**: Whitespace handling

---

#### **Form Submission**

##### `describe('when user submits valid credentials')`
- `it('calls login function with entered credentials')`
  - **Given**: Username="testuser", Password="testpass"
  - **When**: User clicks submit button
  - **Then**: Mock login function is called with ("testuser", "testpass")
  - **Black Box**: Tests the contract/interface

- `it('navigates to home page on successful login')`
  - **Given**: Mock login succeeds
  - **When**: User submits form
  - **Then**: User is redirected to "/" route
  - **Edge Case**: Tests success path boundary

- `it('handles login with whitespace in credentials')`
  - **Given**: Username=" user " (with spaces)
  - **When**: User submits form
  - **Then**: Credentials passed as-is (no trimming)
  - **Edge Case**: Tests whitespace boundary behavior

##### `describe('when login fails')`
- `it('does not navigate away on login error')`
  - **Given**: Mock login throws error
  - **When**: User submits form
  - **Then**: User remains on login page
  - **Edge Case**: Tests error boundary

- `it('logs error to console on login failure')`
  - **Given**: Mock login rejects with error
  - **When**: User submits form
  - **Then**: Error is logged to console
  - **Black Box**: Tests observable side effect (console.error)

---

#### **Edge Cases & Boundaries**

##### `describe('boundary conditions')`
- `it('handles rapid multiple submissions')`
  - **Given**: Form is valid
  - **When**: User clicks submit button 5 times rapidly
  - **Then**: Login is called multiple times (no debouncing)
  - **Edge Case**: Tests race condition boundary

- `it('handles form submission via Enter key in username field')`
  - **Given**: Username field is focused with valid data
  - **When**: User presses Enter
  - **Then**: Form submits
  - **Edge Case**: Keyboard interaction boundary

- `it('handles form submission via Enter key in password field')`
  - **Given**: Password field is focused with valid data
  - **When**: User presses Enter
  - **Then**: Form submits
  - **Edge Case**: Keyboard interaction boundary

##### `describe('when AuthContext is unavailable')`
- `it('throws error if used outside AuthProvider')`
  - **Given**: Component rendered without AuthProvider
  - **When**: Component tries to use useAuth hook
  - **Then**: Error is thrown
  - **Edge Case**: Tests provider boundary

---

#### **Accessibility**

##### `describe('accessibility requirements')`
- `it('associates labels with inputs correctly')`
  - **Given**: Component renders
  - **Then**: Username input has associated label
  - **Then**: Password input has associated label
  - **Black Box**: Tests semantic HTML behavior

- `it('allows keyboard navigation through form')`
  - **Given**: Component renders
  - **When**: User tabs through form
  - **Then**: Focus moves: username → password → submit button
  - **Edge Case**: Keyboard-only interaction

---

## Mocking Strategy

### **AuthContext Mock**
```typescript
const mockLogin = vi.fn();
const mockAuthContext = {
  user: null,
  login: mockLogin,
  logout: vi.fn(),
  isLoading: false
};
```

### **Router Mock**
```typescript
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  ...vi.importActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));
```

---

## What NOT to Test (Implementation Details)
❌ Internal state (`username`, `password` state variables)  
❌ How `useState` hooks are called  
❌ The exact DOM structure or CSS classes (unless critical to behavior)  
❌ The order of `onChange` handler definitions  
❌ Whether component uses hooks vs class methods  

## What TO Test (Behavior & Boundaries)
✅ What the user sees  
✅ What happens when user interacts  
✅ What gets called when (contracts)  
✅ Edge cases: empty, null, extreme values  
✅ Error states and boundaries  
✅ Accessibility behavior  

---

## Test File Location
`src/pages/Login.test.tsx` (co-located with `Login.tsx`)

## Future AI Agent Instructions
1. Implement tests using `describe` and `it` blocks as specified above
2. Use `render()` from React Testing Library
3. Query elements by accessible roles/labels (not test IDs unless necessary)
4. Use `userEvent` for interactions (more realistic than `fireEvent`)
5. Each test should be independent (no shared state between tests)
6. Mock external dependencies at the top of the file
7. Follow the "Arrange-Act-Assert" pattern
8. Keep tests focused on ONE behavior per `it` block
