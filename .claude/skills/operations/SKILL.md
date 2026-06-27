# operations Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `operations` Python repository. It covers file organization, import/export styles, commit message practices, and testing patterns. By following these guidelines, contributors can maintain consistency and quality across the codebase.

## Coding Conventions

### File Naming
- Use **snake_case** for all Python files.
  - Example: `data_processor.py`, `user_utils.py`

### Import Style
- Prefer **relative imports** within the package.
  - Example:
    ```python
    from .helpers import calculate_total
    from .models import User
    ```

### Export Style
- Use **named exports** to explicitly define what is available from a module.
  - Example:
    ```python
    __all__ = ['calculate_total', 'User']
    ```

### Commit Messages
- Messages are **freeform** with no strict prefix requirements.
- Average length: ~67 characters.
  - Example:
    ```
    Fix bug in transaction reconciliation logic
    ```

## Workflows

### Adding a New Module
**Trigger:** When you need to add new functionality.
**Command:** `/add-module`

1. Create a new Python file using snake_case (e.g., `new_feature.py`).
2. Implement your logic, using relative imports as needed.
3. Export public functions/classes via `__all__`.
4. Write corresponding tests in a file matching `*.test.*`.
5. Commit changes with a clear, descriptive message.

### Running Tests
**Trigger:** After making changes or before merging.
**Command:** `/run-tests`

1. Identify test files matching the pattern `*.test.*`.
2. Run tests using your preferred Python test runner (e.g., `pytest`, `unittest`).
   - Example:
     ```
     pytest
     ```
3. Review test output and fix any failures.

### Refactoring Code
**Trigger:** When improving code structure or readability.
**Command:** `/refactor`

1. Update file and function names to follow snake_case.
2. Ensure all imports are relative within the package.
3. Adjust `__all__` in modules to reflect any changes.
4. Update or add tests as needed.
5. Commit with a message describing the refactor.

## Testing Patterns

- Test files follow the pattern: `*.test.*` (e.g., `user_utils.test.py`).
- Testing framework is not explicitly defined; use your preferred Python test runner.
- Place tests alongside or near the modules they cover.
- Example test file:
  ```python
  # user_utils.test.py
  from .user_utils import get_user_name

  def test_get_user_name():
      assert get_user_name(1) == "Alice"
  ```

## Commands
| Command       | Purpose                                         |
|---------------|-------------------------------------------------|
| /add-module   | Scaffold and add a new module                   |
| /run-tests    | Run all test files in the repository            |
| /refactor     | Refactor code to follow repository conventions  |
```