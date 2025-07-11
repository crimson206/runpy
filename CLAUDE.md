# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python module for automated Git version management that aims to simplify common Git operations by providing purpose-specific functions instead of raw Git CLI commands. The project is converting shell-based Git versioning tools to Python functions, following a one-function-per-file development approach.

### Current Implementation Status
- ✅ **Tag Management** (`src/git_versioning/tag.py`): Complete implementation using pyshell
  - `list_tags()`: List all tags or get specific tag info
  - `create_tag()`: Create annotated or lightweight tags
  - `changes_since_tag()`: Get changes since a specific tag
- 🚧 **Diff Operations**: Not yet implemented
- 🚧 **Clone Operations**: Not yet implemented
- 🚧 **Repository Operations**: Not yet implemented

## Key Development Commands

### Installation and Dependencies
```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install only production dependencies
pip install -e .

# Note: pyshell is installed from GitHub, not PyPI
# It's automatically installed with the above commands
```

### Running Tests
```bash
# Run all tests with Allure reporting
pytest

# Run specific test file
pytest tests/features/test_diff.py

# Run tests with specific marker
pytest -m unit
pytest -m integration
pytest -m "not slow"  # Skip slow tests

# Generate and view Allure report
allure serve allure-results
```

### CLI Usage
```bash
# Using full name
git-versioning <command>

# Using short alias
gv <command>

# View available commands
gv --help

# View function documentation
gv docs <function_name>

# View function schema
gv schema <function_name>
```

### Development Workflow
The project uses BDD (Behavior Driven Development) with Allure for testing. Business logic takes precedence over unit tests - tests should validate requirements, not constrain implementation.

## Project Architecture

### Core Functionality Goals
Based on `prompt/user.md`, the module will provide:

1. **Diff Operations**: Compare changes between commits, working directory, and specific tags
   - `diff_working_tree()`: Compare working directory with HEAD
   - `diff_commits()`: Compare two commits
   - `diff_tags()`: Compare two tags
   - `diff_since_tag()`: Show all changes since a specific tag

2. **Tag Management**: List tags, create tags, compare against tags ✅ COMPLETED
   - `list_tags()`: List all tags or get specific tag info
   - `create_tag()`: Create annotated or lightweight tags  
   - `changes_since_tag()`: Get changes since a specific tag

3. **Repository Operations**: Work with external repositories (not just current directory)
   - `get_repo_info()`: Get repository metadata (remotes, branches, status)
   - `fetch_tags()`: Fetch tags from remote repository
   - `push_tag()`: Push specific tag to remote
   
4. **Clone Operations**: Clone repositories at specific tags
   - `clone_at_tag()`: Clone repository and checkout specific tag
   - `shallow_clone()`: Perform shallow clone with depth limit
   - `clone_branch()`: Clone specific branch only

### File Structure Convention
- **One main function per file**: Each Python file should contain one primary function following the pyshell development approach
- **Helper functions allowed**: Supporting functions can exist in the same file
- **CLI conversion**: Functions will be automatically converted to CLI commands using runpycli

### Testing Structure
```
tests/
├── features/       # BDD tests using pytest-bdd and Allure
│   ├── test_diff.py
│   ├── test_tag.py
│   └── test_clone.py
├── steps/         # Reusable test steps
│   ├── git_steps.py
│   ├── diff_steps.py
│   └── validation_steps.py
└── unit/          # Supplementary unit tests (only when necessary)
```

### BDD Testing Guidelines
Follow the Allure BDD guide in `prompt/allure.md`:
- Use Given-When-Then structure
- Create reusable steps with `@allure.step` decorator
- Focus on business requirements, not implementation details
- Tests should be readable as documentation
- Test markers available: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

## Reference Implementation
The project references shell scripts from `.runsh/cache/`, particularly `merge_and_tag.sh`, which demonstrates the type of Git operations being converted to Python functions.

## Implementation Guidelines

### pyshell Usage Pattern
The project uses a custom `pyshell` library (from GitHub, not PyPI) for Git CLI operations instead of GitPython. Here's the established pattern from `tag.py`:
```python
from pyshell import shell, ShellError

# Execute git commands
try:
    result = shell(f"cd {repo_path} && git command")
except ShellError as e:
    raise ValueError(f"Operation failed: {e}")
```

### Error Handling
- Use `ValueError` for user-facing errors (invalid input, Git operation failures)
- Wrap `ShellError` exceptions with meaningful context
- Always validate input parameters (e.g., tag existence, repository validity)

### Function Return Types
- Use type hints with `typing` module
- Return `Dict[str, Any]` for complex data structures
- Support `Optional` returns when no data exists
- Use `Path` from pathlib for file paths

### Testing Approach
- BDD tests in `tests/features/` should cover user scenarios
- Use test steps from `tests/steps/` for reusable Git operations
- Each function should have comprehensive BDD test coverage
- Unit tests are supplementary - only add when BDD doesn't suffice
- Tests automatically generate Allure reports in `allure-results/`

## Common Development Tasks

### Adding a New Git Function
1. Create a new file in `src/git_versioning/` (one function per file)
2. Use pyshell for Git operations (see `tag.py` for patterns)
3. Add comprehensive docstrings with Args/Returns/Raises sections
4. Create BDD tests in `tests/features/test_<function>.py`
5. Add reusable test steps in `tests/steps/<function>_steps.py`
6. Register the function in `src/git_versioning/cli.py`:
   ```python
   from .new_function import new_function
   cli.register(new_function)
   ```

### Working with Test Fixtures
- `temp_git_repo`: Provides a temporary Git repository
- `another_temp_repo`: Provides a second temporary repository for external repo tests
- Use `GitSteps` for common Git operations in tests
- Use specific steps classes (e.g., `TagSteps`) for feature-specific operations

### Common Git Command Patterns
```python
# Check if something exists
try:
    shell(f"cd {repo_path} && git rev-parse {ref}")
    exists = True
except ShellError:
    exists = False

# Get list output
output = shell(f"cd {repo_path} && git tag --list").strip()
items = output.split('\n') if output else []

# Get JSON-like data
log_format = "--format=%H|%s|%an|%ct"
raw = shell(f"cd {repo_path} && git log {log_format}").strip()
for line in raw.split('\n'):
    parts = line.split('|')
    # Process parts...

# Handle paths with spaces
repo_path = Path(user_path).resolve()
shell(f'cd "{repo_path}" && git command')
```

### CLI Integration
The module is designed to work with runpycli (>= 0.6.0) for automatic CLI generation:
- Functions will be exposed as CLI commands automatically
- Use clear, descriptive parameter names
- Provide default values where sensible (e.g., `repo_path=Path(".")`)
- Return structured data that can be formatted for CLI output
- Supports multiple input formats (JSON, YAML, etc.)
- Automatically generates `docs` and `schema` commands

## Data Structure Conventions

### Standard Return Formats
Follow these patterns for consistency across functions:

```python
# Tag information
{
    "name": "v1.0.0",
    "commit": "abc123...",
    "message": "Release message",
    "type": "annotated",  # or "lightweight"
    "date": "2024-01-01T12:00:00",
    "author": {"name": "John Doe", "email": "john@example.com"}
}

# Commit information
{
    "sha": "abc123...",
    "message": "Commit message",
    "author": "John Doe",
    "date": "2024-01-01T12:00:00"
}

# File changes
{
    "added_files": ["file1.py", "file2.py"],
    "modified_files": ["file3.py"],
    "deleted_files": ["file4.py"],
    "files_changed": 4,
    "total_commits": 10
}

# Diff results
{
    "has_changes": True,
    "files": [
        {
            "path": "src/file.py",
            "status": "modified",  # added, modified, deleted, renamed
            "additions": 10,
            "deletions": 5
        }
    ],
    "summary": {"additions": 15, "deletions": 8, "files": 2}
}
```

### Date Formatting
- Always use ISO format: `datetime.fromtimestamp(ts).isoformat()`
- Parse Git timestamps as integers
- Include timezone info when available

## Important Context
- The project uses pyshell (custom GitHub version, not PyPI) for Git operations
- Python 3.10+ is required
- Tag management is fully implemented and serves as the reference implementation
- Follow the established patterns from `tag.py` for consistency
- The project aims to provide a higher-level, more intuitive API than raw Git commands
- Current version: 0.1.0
- Author: Sisung Kim (sisung.kim1@gmail.com)