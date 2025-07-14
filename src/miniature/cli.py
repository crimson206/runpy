"""CLI interface for miniature package management system."""

from runpycli import Runpy
from typing import Optional, List, Dict, Any
import json

from .load import load_pkg, load_pkgs_from_file
from .publish import publish_pkg
from .tag import tag_pkg
from .push import push_pkg
from .cache import get_cache
from .utils import fix_git_filemode, fix_cache_filemode, is_windows_filesystem

cli = Runpy()


@cli.register
def load(
    repo: str,
    version: Optional[str] = None,
    target_dir: Optional[str] = None,
    branch: str = "main",
    clean: bool = False,
    cache_dir: Optional[str] = None,
    symlink: bool = False,
) -> Dict[str, Any]:
    """Load a repository from git.
    
    Args:
        repo: Repository URL
        version: Version/tag to load (e.g., "v1.0.0", ">=0.3.2", "latest")
        target_dir: Directory to copy to (default: repo-name or repo-branch)
        branch: Branch to use if no version specified (default: "main")
        clean: Whether to clean existing target directory
        cache_dir: Cache directory path
        symlink: Use symlink instead of copying (faster, saves space)
    
    Returns:
        Dict containing operation result
    """
    result = load_pkg(
        repo=repo,
        version=version,
        target_dir=target_dir,
        branch=branch,
        clean=clean,
        cache_dir=cache_dir,
        use_symlink=symlink,
    )
    
    # Format output
    if result.get("success"):
        print(f"\n\033[92m✓ SUCCESS\033[0m")
        print(f"  Repository: {repo}")
        print(f"  Branch:     {branch}")
        print(f"  Version:    {result.get('version', 'N/A')}")
        print(f"  Target:     {result.get('target_dir')}")
        if symlink:
            print(f"  Type:       Symlink")
    else:
        print(f"\n\033[91m✗ FAILED\033[0m")
        print(f"  Repository: {repo}")
        print(f"  Branch:     {branch}")
        print(f"  Error:      {result.get('message', 'Unknown error')}")
    
    return result


@cli.register 
def load_from_file(
    config_file: str,
    packages: Optional[str] = None,
    clean: bool = False,
    cache_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Load packages from a configuration file.
    
    Args:
        config_file: Path to pkg.json, miniature.json, or repotree.json
        packages: Comma-separated list of package names to load (default: all)
        clean: Whether to clean existing target directories
        cache_dir: Cache directory path
    
    Returns:
        List of results for each package
    """
    package_names = packages.split(",") if packages else None
    results = load_pkgs_from_file(
        config_file=config_file,
        package_names=package_names,
        clean=clean,
        cache_dir=cache_dir,
    )
    
    # Print detailed results
    print("\n" + "="*60)
    print("LOAD RESULTS")
    print("="*60)
    
    successful = 0
    for i, result in enumerate(results, 1):
        success = result.get("success")
        if success:
            successful += 1
            status = "✓ SUCCESS"
            color = "\033[92m"  # Green
        else:
            status = "✗ FAILED"
            color = "\033[91m"  # Red
        
        print(f"\n{color}{status}\033[0m Package {i}/{len(results)}")
        print(f"  Repository: {result.get('repo', 'N/A')}")
        print(f"  Branch:     {result.get('branch', 'N/A')}")
        print(f"  Target:     {result.get('target_dir', 'N/A')}")
        
        if success:
            print(f"  Version:    {result.get('version', 'N/A')}")
        else:
            # Extract key error message
            error_msg = result.get('message', 'Unknown error')
            if 'not found' in error_msg.lower():
                print(f"  Error:      Branch not found in remote repository")
            elif 'already exists' in error_msg.lower():
                print(f"  Error:      Target directory already exists")
            else:
                # Show first line of error only
                first_line = error_msg.split('\n')[0]
                print(f"  Error:      {first_line}")
    
    print("\n" + "-"*60)
    print(f"Summary: {successful}/{len(results)} packages loaded successfully")
    print("="*60)
    
    return results


@cli.register
def publish(
    pkg_dir: str = ".",
    meta_file: str = "pkg.json",
    message: Optional[str] = None,
    push: bool = True,
    tag: bool = True,
    force_tag: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Publish a package to git repository with optional tagging.
    
    Args:
        pkg_dir: Directory containing the package (default: ".")
        meta_file: Name of the meta file (default: "pkg.json")
        message: Custom commit message
        push: Whether to push changes to remote
        tag: Whether to create a version tag
        force_tag: Whether to force overwrite existing tag
        cache_dir: Cache directory path
    
    Returns:
        Dict containing operation result
    """
    result = publish_pkg(
        pkg_dir=pkg_dir,
        meta_file=meta_file,
        commit_message=message,
        push=push,
        tag=tag,
        force_tag=force_tag,
        cache_dir=cache_dir,
    )
    
    # Format output
    if result.get("success"):
        print(f"\n\033[92m✓ SUCCESS\033[0m")
        print(f"  Package:    {pkg_dir}")
        print(f"  Repository: {result.get('repo_path', 'N/A')}")
        print(f"  Message:    {result.get('commit_message', 'N/A')}")
        if tag and result.get('tag_result'):
            print(f"  Tag:        {result['tag_result'].get('tag_name', 'N/A')}")
        print(f"  Pushed:     {'Yes' if result.get('pushed') else 'No'}")
    else:
        print(f"\n\033[91m✗ FAILED\033[0m")
        print(f"  Package:    {pkg_dir}")
        print(f"  Error:      {result.get('message', 'Unknown error')}")
    
    return result


@cli.register
def tag_package(
    pkg_dir: str = ".",
    meta_file: str = "pkg.json",
    force: bool = False,
    push: bool = True,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a version tag for a package.
    
    Args:
        pkg_dir: Directory containing the package (default: ".")
        meta_file: Name of the meta file (default: "pkg.json")
        force: Whether to force overwrite existing tag
        push: Whether to push tag to remote
        cache_dir: Cache directory path
    
    Returns:
        Dict containing operation result
    """
    return tag_pkg(
        pkg_dir=pkg_dir,
        meta_file=meta_file,
        force=force,
        push=push,
        cache_dir=cache_dir,
    )


@cli.register
def push(
    pkg_dir: str = ".",
    meta_file: str = "pkg.json",
    message: Optional[str] = None,
    push_remote: bool = True,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Push a package directory to repository (without tagging).
    
    Args:
        pkg_dir: Directory containing the package (default: ".")
        meta_file: Name of the meta file (default: "pkg.json")
        message: Custom commit message
        push_remote: Whether to push changes to remote
        cache_dir: Cache directory path
    
    Returns:
        Dict containing operation result
    """
    return push_pkg(
        pkg_dir=pkg_dir,
        meta_file=meta_file,
        commit_message=message,
        push=push_remote,
        cache_dir=cache_dir,
    )


@cli.register
def cache_list(cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """List all cached repositories.
    
    Args:
        cache_dir: Cache directory path
    
    Returns:
        Dict of cached repositories
    """
    cache = get_cache(cache_dir)
    repos = cache.list_cached_repos()
    
    if not repos:
        print("No repositories in cache")
        return {}
    
    print(f"Cached repositories ({len(repos)}):")
    for url, info in repos.items():
        print(f"  - {url}")
        print(f"    Path: {info['path']}")
        print(f"    Last updated: {info['last_updated']}")
    
    return repos


@cli.register
def cache_clear(cache_dir: Optional[str] = None, confirm: bool = False) -> Dict[str, str]:
    """Clear the repository cache.
    
    Args:
        cache_dir: Cache directory path
        confirm: Skip confirmation prompt
    
    Returns:
        Status message
    """
    if not confirm:
        response = input("Are you sure you want to clear the cache? (y/N): ")
        if response.lower() != 'y':
            return {"status": "cancelled", "message": "Cache clear cancelled"}
    
    cache = get_cache(cache_dir)
    cache.clear_cache()
    
    return {"status": "success", "message": "Cache cleared successfully"}


@cli.register
def cache_remove(repo_url: str, cache_dir: Optional[str] = None) -> Dict[str, str]:
    """Remove a specific repository from cache.
    
    Args:
        repo_url: Repository URL to remove
        cache_dir: Cache directory path
    
    Returns:
        Status message
    """
    cache = get_cache(cache_dir)
    cache.remove_repo(repo_url)
    
    return {"status": "success", "message": f"Removed {repo_url} from cache"}


@cli.register
def fix_filemode(path: str = ".", recursive: bool = False) -> Dict[str, Any]:
    """Fix git filemode tracking for repositories (Windows filesystem issue).
    
    This command disables git's filemode tracking which causes all files to 
    appear modified when working on Windows filesystems (WSL with /mnt/).
    
    Args:
        path: Path to repository or directory containing repositories
        recursive: Find and fix all git repositories recursively
    
    Returns:
        Status of the operation
    """
    result = fix_git_filemode(path, recursive)
    
    if result["success"]:
        print(f"\n\033[92m✓ SUCCESS\033[0m")
        print(f"  Fixed {len(result['fixed'])} repositories")
    else:
        print(f"\n\033[91m✗ ISSUES FOUND\033[0m")
        print(f"  Fixed: {len(result['fixed'])}")
        print(f"  Errors: {len(result['errors'])}")
        for error in result['errors']:
            print(f"    - {error['path']}: {error['error']}")
    
    return result


@cli.register
def fix_cache_modes(cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """Fix git filemode for all repositories in miniature cache.
    
    Args:
        cache_dir: Cache directory path (defaults to ~/.miniature/cache)
    
    Returns:
        Status of the operation
    """
    result = fix_cache_filemode(cache_dir)
    
    if result["success"]:
        print(f"\n\033[92m✓ SUCCESS\033[0m")
        print(f"  Fixed {len(result['fixed'])} cached repositories")
        print(f"  Cache: {cache_dir or '~/.miniature/cache'}")
    else:
        print(f"\n\033[91m✗ ISSUES FOUND\033[0m")
        print(f"  Message: {result['message']}")
        if result.get('errors'):
            for error in result['errors']:
                print(f"    - {error['path']}: {error['error']}")
    
    return result


@cli.register
def check_windows_fs(path: str = ".") -> Dict[str, bool]:
    """Check if a path is on Windows filesystem (WSL).
    
    Args:
        path: Path to check
    
    Returns:
        Dict with check result
    """
    is_windows = is_windows_filesystem(path)
    
    if is_windows:
        print(f"\n\033[93m⚠ WARNING\033[0m")
        print(f"  Path '{path}' is on Windows filesystem")
        print(f"  Consider using 'miniature fix-filemode' to avoid git issues")
    else:
        print(f"\n\033[92m✓ INFO\033[0m")
        print(f"  Path '{path}' is on Linux filesystem")
        print(f"  No filemode issues expected")
    
    return {"is_windows_filesystem": is_windows, "path": path}


if __name__ == "__main__":
    cli.app()