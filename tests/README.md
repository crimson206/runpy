# Miniature BDD Tests

BDD (Behavior-Driven Development) tests for miniature package using Allure framework.

## Test Structure

### Core Functionality Tests
- **test_load_bdd.py**: Package loading from git repositories
- **test_publish_bdd.py**: Package publishing and tagging
- **test_repotree_integration_bdd.py**: Integration tests for repotree system

### Test Features
- Uses real git repositories (bare and working)
- No mocking - tests actual git operations
- Allure reporting for clear test documentation
- BDD style with Given-When-Then structure

## Setup

### Install Dependencies
```bash
pip install pytest allure-pytest gitpython
```

### Run Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_load_bdd.py

# Run with specific marker
pytest -m integration

# Generate Allure report
pytest --alluredir=allure-results
allure serve allure-results
```

## Test Scenarios

### Package Loading
- Load specific version from git repository
- Load latest version using "latest" keyword
- Load from specific branch
- Load multiple packages from configuration file
- Handle errors (non-existent path, invalid version)

### Package Publishing
- Publish with automatic version tagging
- Publish without tagging
- Force overwrite existing tags
- Custom commit messages
- Handle errors (missing pkg.json, repository not found)

### Repotree Integration
- Load packages from pkg.json configuration with dependencies array
- Branch-based versioning (main vs dev branches)
- Package dependency management
- Repository caching

## Writing New Tests

Follow BDD pattern:
```python
@allure.feature("Feature Name")
@allure.story("User Story")
class TestClassName:
    
    @allure.title("Test scenario title")
    @allure.description("""
        Given some precondition
        When action is performed
        Then expected outcome
    """)
    def test_scenario_name(self, fixtures):
        with allure.step("Given precondition"):
            # Setup code
            
        with allure.step("When action performed"):
            # Action code
            
        with allure.step("Then expected outcome"):
            # Assertion code
```

## Fixtures

See `conftest.py` for available fixtures:
- `temp_dir`: Temporary directory for test
- `bare_repo`: Bare git repository
- `working_repo`: Working git repository with initial commit
- `package_repo`: Repository with package structure and tags
- `gitdbs_config`: GitDB configuration file