"""Common test fixtures and configurations."""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from git import Repo


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def bare_repo(temp_dir):
    """Create a bare git repository for testing."""
    repo_path = temp_dir / "test-repo.git"
    repo = Repo.init(str(repo_path), bare=True)
    return repo_path


@pytest.fixture
def working_repo(temp_dir):
    """Create a working git repository with initial commit."""
    repo_path = temp_dir / "working-repo"
    repo = Repo.init(str(repo_path))

    # Create initial file
    test_file = repo_path / "README.md"
    test_file.write_text("# Test Repository\n")

    # Add and commit
    repo.index.add([str(test_file)])
    repo.index.commit("Initial commit")

    return repo_path


@pytest.fixture
def package_repo(temp_dir):
    """Create a git repository with a package structure."""
    repo_path = temp_dir / "package-repo"
    repo = Repo.init(str(repo_path))

    # Create package structure
    pkg_dir = repo_path / "packages" / "test-package"
    pkg_dir.mkdir(parents=True)

    # Create package files
    (pkg_dir / "pkg.json").write_text(
        """{
    "name": "test-package",
    "version": "1.0.0",
    "description": "Test package for miniature"
}"""
    )

    (pkg_dir / "index.py").write_text(
        'def hello():\n    return "Hello from test package"'
    )

    # Add and commit
    repo.index.add([str(pkg_dir / "pkg.json"), str(pkg_dir / "index.py")])
    repo.index.commit("Add test package")

    # Create some tags
    repo.create_tag("packages/test-package/0.9.0", message="Previous version")
    repo.create_tag("packages/test-package/1.0.0", message="Current version")

    return repo_path


@pytest.fixture
def gitdbs_config(temp_dir):
    """Create a gitdbs configuration file."""
    config_dir = temp_dir / ".miniature"
    config_dir.mkdir()

    config_file = config_dir / "gitdbs.json"
    config_file.write_text(
        '''[
    {
        "name": "test-repo",
        "description": "Test repository",
        "db-repo": "https://github.com/test/repo",
        "local_path": "'''
        + str(temp_dir / "local-repos" / "test-repo")
        + """"
    }
]"""
    )

    return str(config_file)
