"""Utility functions for miniature."""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from git import Repo


def fix_git_filemode(path: str, recursive: bool = False) -> Dict[str, Any]:
    """Fix git filemode tracking for repositories on Windows filesystems.
    
    This disables git's filemode tracking which causes all files to appear
    modified when working on Windows filesystems (WSL with /mnt/).
    
    Args:
        path: Path to repository or directory containing repositories
        recursive: If True, fix all git repositories found recursively
        
    Returns:
        Dict with success status and affected repositories
    """
    path = Path(path).resolve()
    fixed_repos = []
    errors = []
    
    if recursive:
        # Find all git repositories recursively
        git_repos = []
        for root, dirs, files in os.walk(path):
            if '.git' in dirs:
                git_repos.append(Path(root))
                # Don't recurse into .git directories
                dirs.remove('.git')
    else:
        # Check if single path is a git repository
        if (path / '.git').exists():
            git_repos = [path]
        else:
            return {
                "success": False,
                "message": f"No git repository found at {path}",
                "fixed": [],
                "errors": []
            }
    
    # Fix filemode for each repository
    for repo_path in git_repos:
        try:
            # Use git command for reliability
            result = subprocess.run(
                ['git', 'config', 'core.filemode', 'false'],
                cwd=str(repo_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                fixed_repos.append(str(repo_path))
                print(f"✓ Fixed filemode for: {repo_path}")
            else:
                errors.append({
                    "path": str(repo_path),
                    "error": result.stderr.strip() or "Unknown error"
                })
                print(f"✗ Failed to fix: {repo_path}")
                
        except Exception as e:
            errors.append({
                "path": str(repo_path),
                "error": str(e)
            })
            print(f"✗ Error fixing {repo_path}: {e}")
    
    return {
        "success": len(errors) == 0,
        "message": f"Fixed {len(fixed_repos)} repositories, {len(errors)} errors",
        "fixed": fixed_repos,
        "errors": errors
    }


def is_windows_filesystem(path: str) -> bool:
    """Check if path is on Windows filesystem (WSL).
    
    Args:
        path: Path to check
        
    Returns:
        True if path is on Windows filesystem
    """
    return str(Path(path).resolve()).startswith('/mnt/')


def fix_cache_filemode(cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """Fix git filemode for all repositories in miniature cache.
    
    Args:
        cache_dir: Cache directory path (defaults to ~/.miniature/cache)
        
    Returns:
        Dict with success status and affected repositories
    """
    if cache_dir:
        cache_path = Path(cache_dir)
    else:
        cache_path = Path.home() / ".miniature" / "cache"
    
    if not cache_path.exists():
        return {
            "success": False,
            "message": f"Cache directory not found: {cache_path}",
            "fixed": [],
            "errors": []
        }
    
    print(f"Fixing filemode for all repositories in cache: {cache_path}")
    return fix_git_filemode(str(cache_path), recursive=True)


def should_disable_filemode(path: str) -> bool:
    """Determine if filemode should be disabled for a path.
    
    This checks if we're on a Windows filesystem or if there are
    filemode issues detected.
    
    Args:
        path: Path to check
        
    Returns:
        True if filemode should be disabled
    """
    # Always disable on Windows filesystems
    if is_windows_filesystem(path):
        return True
    
    # Additional checks could be added here
    return False