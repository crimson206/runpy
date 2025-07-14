"""Git tagging functionality with branch-based versioning support."""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from git import Repo

from .cache import get_cache
from .models import PkgJson


def create_tag(
    repo_url: Optional[str] = None,
    tag_name: Optional[str] = None,
    tag_message: Optional[str] = None,
    force: bool = False,
    push: bool = True,
    gitdbs_config: Optional[str] = None,  # Deprecated
    cache_dir: Optional[str] = None,
    # New parameters for repotree
    pkg_json_path: Optional[str] = None,
    root_dir: Optional[str] = None,
    branch: Optional[str] = None,
    default_branch: str = "main",
) -> Dict[str, Any]:
    """Create a git tag with branch-based versioning support.

    For repotree compatibility:
    - Tags on default branch: {root_dir}/{version} or just {version}
    - Tags on other branches: {root_dir}/{branch}/{version}

    Args:
        repo_url: Repository URL (required if not using pkg_json_path)
        tag_name: Tag name (auto-generated if pkg_json_path provided)
        tag_message: Custom tag message
        force: Whether to force overwrite existing tag
        push: Whether to push tag to remote
        gitdbs_config: DEPRECATED
        cache_dir: Cache directory path
        pkg_json_path: Path to pkg.json for auto tag generation
        root_dir: Root directory for tag prefix
        branch: Current branch (for branch-based tagging)
        default_branch: Default branch name (tags without branch prefix)

    Returns:
        Dict containing operation result
    """
    # Auto-generate tag from pkg.json if provided
    if pkg_json_path:
        pkg_json = PkgJson.from_file(Path(pkg_json_path))

        if not pkg_json.version:
            return {"success": False, "message": "No version found in pkg.json"}

        # Determine branch if not provided
        if not branch:
            branch = pkg_json.branch or default_branch

        # Construct tag name based on branch
        version = pkg_json.version.lstrip("v")  # Remove 'v' prefix if present

        # Build tag components
        tag_parts = []

        # Add root directory if specified
        if root_dir and root_dir != ".":
            tag_parts.append(root_dir.strip("/"))

        # Add branch name if not default branch
        if branch and branch != default_branch:
            tag_parts.append(branch)

        # Add version
        tag_parts.append(version)

        # Join tag parts
        tag_name = "/".join(tag_parts)

        # Use repository from pkg.json if not provided
        if not repo_url and pkg_json.db_repo:
            repo_url = pkg_json.db_repo

    # Validate inputs
    if not repo_url:
        return {"success": False, "message": "Repository URL is required"}

    if not tag_name:
        return {"success": False, "message": "Tag name is required"}

    # Set default tag message
    if tag_message is None:
        tag_message = f"Release {tag_name}"

    try:
        # Get cache instance
        cache = get_cache(Path(cache_dir) if cache_dir else None)

        # Get repository from cache
        repo_path = cache.get_repo(repo_url, ensure_latest=True)

        if not repo_path:
            # Clone if not in cache
            repo_path = cache.clone_or_update(repo_url)

        # Get git repository
        git_repo = Repo(repo_path)

        # Check if tag exists
        tag_exists = tag_name in [tag.name for tag in git_repo.tags]

        # Handle existing tag
        if tag_exists:
            if force:
                # Delete local tag
                git_repo.delete_tag(tag_name)
                action = "updated"
            else:
                return {
                    "success": False,
                    "message": f"Tag '{tag_name}' already exists. Use force=True to overwrite.",
                }
        else:
            action = "created"

        # Create new tag
        git_repo.create_tag(tag_name, message=tag_message)

        # Push tag if requested
        if push:
            origin = git_repo.remote("origin")

            if force:
                # Force push tag
                origin.push(refspec=f"refs/tags/{tag_name}", force=True)
            else:
                # Normal push
                origin.push(tags=True)

            action = "pushed"

        return {
            "success": True,
            "action": action,
            "tag_name": tag_name,
            "message": f"Tag '{tag_name}' {action}",
        }

    except Exception as e:
        return {"success": False, "message": f"Failed to create tag: {e}", "error": e}


def tag_pkg(
    pkg_dir: str = ".",
    meta_file: str = "pkg.json",
    force: bool = False,
    push: bool = True,
    cache_dir: Optional[str] = None,
    default_branch: str = "main",
) -> Dict[str, Any]:
    """Create tag for a package based on its pkg.json.

    This is a convenience function that reads package metadata
    and creates appropriate tag with branch-based versioning.

    Args:
        pkg_dir: Package directory containing pkg.json
        meta_file: Package metadata file name
        force: Whether to force overwrite existing tag
        push: Whether to push tag to remote
        cache_dir: Cache directory path
        default_branch: Default branch (no branch prefix in tag)

    Returns:
        Dict containing operation result
    """
    pkg_path = Path(pkg_dir)
    pkg_json_path = pkg_path / meta_file

    if not pkg_json_path.exists():
        return {
            "success": False,
            "message": f"Package file {meta_file} not found in {pkg_dir}",
        }

    # Load package metadata
    pkg_json = PkgJson.from_file(pkg_json_path)

    if not pkg_json.db_repo:
        return {"success": False, "message": "No db-repo found in package metadata"}

    # Create tag using package information
    return create_tag(
        repo_url=pkg_json.db_repo,
        pkg_json_path=str(pkg_json_path),
        root_dir=pkg_json.root_dir,
        branch=pkg_json.branch,
        force=force,
        push=push,
        cache_dir=cache_dir,
        default_branch=default_branch,
    )


def delete_tag(
    repo_url: str, tag_name: str, remote: bool = True, cache_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Delete a tag locally and optionally from remote.

    Args:
        repo_url: Repository URL
        tag_name: Name of the tag to delete
        remote: Whether to delete from remote
        cache_dir: Cache directory path

    Returns:
        Dict with operation result
    """
    try:
        # Get cache instance
        cache = get_cache(Path(cache_dir) if cache_dir else None)

        # Get repository from cache
        repo_path = cache.get_repo(repo_url, ensure_latest=False)

        if not repo_path:
            return {
                "success": False,
                "message": f"Repository {repo_url} not found in cache",
            }

        # Get git repository
        git_repo = Repo(repo_path)

        # Delete local tag
        local_deleted = False
        if tag_name in [tag.name for tag in git_repo.tags]:
            git_repo.delete_tag(tag_name)
            local_deleted = True
            local_msg = f"Deleted local tag '{tag_name}'"
        else:
            local_msg = f"Local tag '{tag_name}' not found"

        # Delete remote tag if requested
        remote_msg = None
        if remote and local_deleted:
            try:
                origin = git_repo.remote("origin")
                origin.push(refspec=f":refs/tags/{tag_name}")
                remote_msg = f"Deleted remote tag '{tag_name}'"
            except Exception as e:
                remote_msg = f"Failed to delete remote tag: {e}"

        return {"success": True, "local": local_msg, "remote": remote_msg}

    except Exception as e:
        return {"success": False, "message": f"Failed to delete tag: {e}", "error": e}
