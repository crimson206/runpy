#!/usr/bin/env python
"""Example script demonstrating loading dependencies from pkg.json"""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from miniature.load import load_pkgs_from_file

def main():
    """Load dependencies from pkg.json file."""
    # Path to pkg.json with dependencies
    config_file = Path(__file__).parent / "pkg.json"
    
    print(f"Loading dependencies from: {config_file}")
    print("-" * 50)
    
    try:
        # Load all dependencies
        results = load_pkgs_from_file(str(config_file))
        
        for result in results:
            if result["success"]:
                print(f"✓ Successfully loaded: {result.get('path', 'unknown')}")
                print(f"  Repository: {result.get('repo', 'unknown')}")
                print(f"  Version: {result.get('version', 'unknown')}")
                print(f"  Target: {result.get('target_dir', 'unknown')}")
            else:
                print(f"✗ Failed to load package: {result['message']}")
            print()
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())