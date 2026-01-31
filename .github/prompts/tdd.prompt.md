---
description: Test-Driven Development (TDD) - Red, Green, Refactor
---

# TDD Mode

Follow the red-green-refactor cycle for all code changes.

## Process Steps

### 1. CLARIFY
- Understand what behavior needs to change or be added
- Identify specific inputs and expected outputs
- Determine which components/functions will be affected
- Ask clarifying questions if requirements are ambiguous

### 2. PROPOSE PLAN
Present the plan in this format:

**Goal:** [What behavior we're adding/changing - 1 line]

**Affected Components:**
- [Component/Module 1]: [What changes]
- [Component/Module 2]: [What changes]

**Test Strategy:**
- Existing tests to verify: [list]
- New/modified tests needed: [list]

**Implementation Approach:**
```
[Brief outline of the code changes]
```

**Exit:** Wait for user approval before proceeding

### 3. GREEN - Validate Existing Tests
```bash
# Run existing tests to confirm they pass
runTests tool with relevant test files
```
✓ Confirm: "All existing tests pass (GREEN)"

### 4. RED - Write Failing Tests
- Write new tests or modify existing tests for target behavior
- **Test at boundaries**: Verify interfaces and public contracts, not implementations
- Tests should fail because new behavior isn't implemented yet

```bash
# Run tests to verify they fail
runTests tool with modified test files
```
✗ Confirm: "New tests fail as expected (RED) - [reason for failure]"

### 5. GREEN - Implement to Pass Tests
- Make minimal code changes to pass tests
- Focus on working code, not perfect code
- Run tests frequently

```bash
# Run tests after implementation
runTests tool with all relevant test files
```
✓ Confirm: "All tests now pass (GREEN)"

### 6. REFACTOR - Improve Code Quality
While maintaining GREEN:
- Remove duplication
- Improve naming
- Simplify logic
- Apply design patterns

After each refactoring step:
```bash
# Verify tests still pass
runTests tool
get_errors tool for Pylance check
```
✓ Confirm: "Tests pass after refactoring (GREEN), no type errors"

### 7. FINAL VERIFICATION
```bash
# Run all relevant unit tests
runTests tool with all test files

# Check for type errors
get_errors tool
```
✓ Confirm: "All tests pass, zero type errors, requirements met"

## Key Principles

- **Test Behavior, Not Implementation**: Tests verify what code does, not how
- **Test at the Boundaries**: Focus on interfaces, public APIs, and contracts
- **Small Steps**: Make incremental changes, run tests frequently
- **Red Before Green**: Always see a test fail before making it pass
- **Keep Tests Fast**: Unit tests run in milliseconds
- **One Concept Per Test**: Each test verifies a single behavior

## Output Format

Present each phase clearly:

```
📋 CLARIFY
[Understanding of requirements]
[Questions if any]

📝 PLAN
[Goal, affected components, test strategy, approach]

✅ GREEN (Existing)
[Test results showing baseline passing]

❌ RED (New Tests)
[Test results showing expected failures]

✅ GREEN (Implementation)
[Test results showing tests now pass]

🔧 REFACTOR
[Improvements made, tests still passing]

✓ FINAL
[All tests pass, no errors, complete]
```

## When NOT to Use TDD

- Quick prototypes or exploratory code
- User explicitly requests implementation without tests
- Fixing trivial typos or formatting
- Working with external systems where mocking is impractical

## Remember

**Tests are executable documentation** - they show how code is meant to be used and what behavior is expected.

**CRITICAL**: Use `runTests` tool after every code change. This is MANDATORY, not optional.
