#!/usr/bin/env python3
"""Demo script to test miniature CLI with local bare repositories."""

import os
import json
import shutil
import tempfile
from pathlib import Path
from git import Repo

def create_test_environment():
    """Create a temporary environment with bare repositories for testing."""
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="miniature_test_"))
    print(f"Creating test environment in: {temp_dir}")
    
    # Create bare repositories
    repos_dir = temp_dir / "repos"
    repos_dir.mkdir()
    
    # Create math-utils repository
    math_repo_bare = repos_dir / "math-utils.git"
    math_repo_bare.mkdir()
    bare_repo1 = Repo.init(str(math_repo_bare), bare=True)
    
    # Create working clone to add content
    work_dir = temp_dir / "work"
    work_dir.mkdir()
    math_work = work_dir / "math-utils"
    math_work.mkdir()
    work_repo1 = bare_repo1.clone(str(math_work))
    
    # Add math-utils package content
    pkg_dir = math_work / "src" / "math_utils"
    pkg_dir.mkdir(parents=True)
    
    # Create package files
    (pkg_dir / "__init__.py").write_text('__version__ = "1.0.0"')
    (pkg_dir / "calculator.py").write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")
    
    # Create pkg.json for the package
    (pkg_dir / "pkg.json").write_text(json.dumps({
        "name": "math-utils",
        "version": "1.0.0",
        "description": "Mathematical utility functions",
        "db-repo": f"file://{math_repo_bare}/",
        "root-dir": "src/math_utils",
        "branch": "main"
    }, indent=2))
    
    # Commit and tag
    work_repo1.index.add([
        "src/math_utils/__init__.py",
        "src/math_utils/calculator.py", 
        "src/math_utils/pkg.json"
    ])
    work_repo1.index.commit("Add math-utils package v1.0.0")
    work_repo1.create_tag("src/math_utils/1.0.0", message="Release v1.0.0")
    
    # Add version 1.1.0 with more functions
    (pkg_dir / "calculator.py").write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def power(a, b):
    return a ** b

def factorial(n):
    if n < 0:
        raise ValueError("Factorial of negative number")
    if n <= 1:
        return 1
    return n * factorial(n - 1)
""")
    
    (pkg_dir / "pkg.json").write_text(json.dumps({
        "name": "math-utils", 
        "version": "1.1.0",
        "description": "Mathematical utility functions",
        "db-repo": f"file://{math_repo_bare}/",
        "root-dir": "src/math_utils",
        "branch": "main"
    }, indent=2))
    
    work_repo1.index.add(["src/math_utils/calculator.py", "src/math_utils/pkg.json"])
    work_repo1.index.commit("Add power and factorial functions v1.1.0")
    work_repo1.create_tag("src/math_utils/1.1.0", message="Release v1.1.0")
    
    # Push to bare repository
    work_repo1.remote().push()
    work_repo1.remote().push(tags=True)
    
    # Create config-utils repository
    config_repo_bare = repos_dir / "config-utils.git"
    config_repo_bare.mkdir()
    bare_repo2 = Repo.init(str(config_repo_bare), bare=True)
    
    config_work = work_dir / "config-utils"
    config_work.mkdir()
    work_repo2 = bare_repo2.clone(str(config_work))
    
    # Add config package
    config_pkg_dir = config_work / "configs" / "app-config"
    config_pkg_dir.mkdir(parents=True)
    
    (config_pkg_dir / "settings.json").write_text(json.dumps({
        "app_name": "TestApp",
        "version": "2.0.0",
        "debug": False,
        "database": {
            "host": "localhost",
            "port": 5432
        }
    }, indent=2))
    
    (config_pkg_dir / "pkg.json").write_text(json.dumps({
        "name": "app-config",
        "version": "2.0.0", 
        "description": "Application configuration",
        "db-repo": f"file://{config_repo_bare}/",
        "root-dir": "configs/app-config",
        "branch": "main"
    }, indent=2))
    
    work_repo2.index.add([
        "configs/app-config/settings.json",
        "configs/app-config/pkg.json"
    ])
    work_repo2.index.commit("Add app-config v2.0.0")
    work_repo2.create_tag("configs/app-config/2.0.0", message="Release v2.0.0")
    work_repo2.remote().push()
    work_repo2.remote().push(tags=True)
    
    # Create test workspace
    test_workspace = temp_dir / "test_workspace"
    test_workspace.mkdir()
    
    # Create pkg.json configuration file
    pkg_config = {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": [
            {
                "pkgName": "math-utils",
                "pkgType": "python",
                "version": ">=1.0.0",
                "domain": f"file://{math_repo_bare}/",
                "repoName": "",
                "pathName": "src/math_utils",
                "branch": "main",
                "localDir": "lib/math-utils"
            },
            {
                "pkgName": "app-config",
                "version": "latest",
                "domain": f"file://{config_repo_bare}/",
                "repoName": "",
                "pathName": "configs/app-config", 
                "branch": "main",
                "localDir": "config/app-config"
            }
        ]
    }
    
    (test_workspace / "pkg.json").write_text(json.dumps(pkg_config, indent=2))
    
    return {
        "temp_dir": temp_dir,
        "test_workspace": test_workspace,
        "math_repo": f"file://{math_repo_bare}/",
        "config_repo": f"file://{config_repo_bare}/",
        "pkg_config_file": test_workspace / "pkg.json"
    }

def print_test_commands(env):
    """Print CLI commands to test."""
    print("\n" + "="*60)
    print("TEST COMMANDS")
    print("="*60)
    
    print(f"\n1. Change to test workspace:")
    print(f"   cd {env['test_workspace']}")
    
    print(f"\n2. Test individual package load:")
    print(f"   miniature load --repo {env['math_repo']} --path src/math_utils --version latest")
    print(f"   # Should create ./math_utils/ directory")
    
    print(f"\n3. Test with specific target directory:")
    print(f"   miniature load --repo {env['math_repo']} --path src/math_utils --version 1.0.0 --target-dir my-math")
    print(f"   # Should create ./my-math/ directory")
    
    print(f"\n4. Test loading from configuration file:")
    print(f"   miniature load-from-file --config-file pkg.json")
    print(f"   # Should create ./lib/math-utils/ and ./config/app-config/ directories")
    
    print(f"\n5. Test cache management:")
    print(f"   miniature cache-list")
    print(f"   # Should show cached repositories")
    
    print(f"\n6. Test version constraint:")
    print(f"   miniature load --repo {env['math_repo']} --path src/math_utils --version '>=1.1.0' --target-dir math-v11")
    print(f"   # Should load v1.1.0 with power() and factorial() functions")
    
    print(f"\n\nCLEANUP:")
    print(f"   rm -rf {env['temp_dir']}")
    print("="*60)

def main():
    """Main demo function."""
    print("Creating test environment with bare repositories...")
    
    try:
        env = create_test_environment()
        print(f"✓ Created test repositories in: {env['temp_dir']}")
        print(f"✓ Math-utils repo: {env['math_repo']}")
        print(f"✓ Config repo: {env['config_repo']}")
        print(f"✓ Test workspace: {env['test_workspace']}")
        print(f"✓ Configuration file: {env['pkg_config_file']}")
        
        print_test_commands(env)
        
        # Show pkg.json content
        print(f"\n\nPKG.JSON CONTENT:")
        print("-" * 40)
        with open(env['pkg_config_file']) as f:
            print(f.read())
        
    except Exception as e:
        print(f"✗ Error creating test environment: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())