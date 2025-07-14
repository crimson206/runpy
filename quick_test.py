#!/usr/bin/env python3
"""Quick test script for miniature CLI functionality."""

import os
import sys
import json
import tempfile
from pathlib import Path
from git import Repo

def create_simple_repo():
    """Create a simple test repository."""
    temp_dir = Path(tempfile.mkdtemp(prefix="mini_test_"))
    
    # Create bare repo
    bare_repo = temp_dir / "test-repo.git"
    bare_repo.mkdir()
    bare = Repo.init(str(bare_repo), bare=True)
    
    # Create working clone
    work_dir = temp_dir / "work"
    work_dir.mkdir()
    work = bare.clone(str(work_dir))
    
    # Add simple package
    (work_dir / "hello.py").write_text('def greet(name):\n    return f"Hello, {name}!"')
    (work_dir / "pkg.json").write_text(json.dumps({
        "name": "hello-pkg",
        "version": "1.0.0",
        "description": "Simple greeting package"
    }, indent=2))
    
    work.index.add(["hello.py", "pkg.json"])
    work.index.commit("Initial package")
    work.create_tag("v1.0.0", message="Version 1.0.0")
    work.remote().push()
    work.remote().push(tags=True)
    
    return str(bare_repo), temp_dir

def test_direct_import():
    """Test miniature functions directly."""
    print("Testing direct import...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from miniature.load import load_pkg
        print("✓ Import successful")
        
        # Create test repo
        repo_path, temp_dir = create_simple_repo()
        test_workspace = temp_dir / "workspace"
        test_workspace.mkdir()
        
        os.chdir(str(test_workspace))
        print(f"✓ Created test repo: file://{repo_path}")
        print(f"✓ Changed to workspace: {test_workspace}")
        
        # Test load_pkg function
        result = load_pkg(
            repo=f"file://{repo_path}",
            path=".",
            version="latest"
        )
        
        if result["success"]:
            print(f"✓ Package loaded successfully to: {result['target_dir']}")
            print(f"✓ Version: {result['version']}")
            
            # Check if files exist
            target = Path(result["target_dir"])
            if (target / "hello.py").exists():
                print("✓ hello.py file exists")
            if (target / "pkg.json").exists():
                print("✓ pkg.json file exists")
                
            # Show directory contents
            print(f"\nDirectory contents of {target}:")
            for item in target.iterdir():
                print(f"  - {item.name}")
                
        else:
            print(f"✗ Load failed: {result['message']}")
            
        print(f"\nCleanup: rm -rf {temp_dir}")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def main():
    """Run quick tests."""
    print("Miniature Quick Test")
    print("=" * 40)
    
    if test_direct_import():
        print("\n✓ All tests passed!")
        print("\nTo test CLI after installation:")
        print("  pip install -e .")
        print("  python test_cli_demo.py  # For full demo")
    else:
        print("\n✗ Tests failed!")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())