"""Package publishing functionality with repotree support."""

import json
import os
import shutil
from typing import Optional, Dict, Any
from pathlib import Path
from git import Repo

from .cache import get_cache
from .models import PkgJson
from .tag import tag_pkg


def publish_pkg(
    pkg_dir: str = ".",
    meta_file: str = "pkg.json",
    commit_message: Optional[str] = None,
    push: bool = True,
    tag: bool = True,
    force_tag: bool = False,
    gitdbs_config: Optional[str] = None,  # Deprecated
    cache_dir: Optional[str] = None,
    default_branch: str = "main",
) -> Dict[str, Any]:
    """Publish a package to git repository with optional tagging.

    This function:
    1. Copies package files to local repository cache
    2. Commits changes
    3. Optionally creates version tag (with branch-based versioning)
    4. Optionally pushes to remote

    Args:
        pkg_dir: Directory containing the package to publish
        meta_file: Name of the meta file (default: "pkg.json")
        commit_message: Custom commit message
        push: Whether to push changes to remote
        tag: Whether to create a version tag
        force_tag: Whether to force overwrite existing tag
        gitdbs_config: DEPRECATED
        cache_dir: Cache directory path
        default_branch: Default branch name for tagging

    Returns:
        Dict containing operation result
    """
    # Load package metadata
    pkg_path = Path(pkg_dir)
    meta_file_path = pkg_path / meta_file

    if not meta_file_path.exists():
        return {"success": False, "message": f"Meta file not found: {meta_file_path}"}

    # Load package configuration
    pkg_json = PkgJson.from_file(meta_file_path)

    if not pkg_json.db_repo:
        return {"success": False, "message": "No 'db-repo' found in package metadata"}

    # Get repository URL and paths
    repo_url = pkg_json.db_repo
    root_dir = pkg_json.root_dir or "."
    branch = pkg_json.branch or default_branch

    # Set default commit message
    if commit_message is None:
        commit_message = f"Update {pkg_json.name}"
        if pkg_json.version:
            commit_message += f" v{pkg_json.version}"

    try:
        # Get cache instance
        cache = get_cache(Path(cache_dir) if cache_dir else None)

        # Clone or update repository in cache
        repo_path = cache.clone_or_update(repo_url, branch)

        # Get git repository
        git_repo = Repo(repo_path)

        # Checkout correct branch
        if branch in git_repo.heads:
            git_repo.heads[branch].checkout()
        elif f"origin/{branch}" in git_repo.refs:
            git_repo.create_head(branch, f"origin/{branch}").checkout()
        else:
            # Create new branch
            git_repo.create_head(branch).checkout()

        # Determine target directory in repository
        target_path = repo_path / root_dir
        target_path.mkdir(parents=True, exist_ok=True)

        # Copy package files to repository
        # Get all files except git and cache directories
        for item in pkg_path.iterdir():
            if item.name in [".git", ".gitignore", "__pycache__", ".pytest_cache"]:
                continue

            target_item = target_path / item.name

            if item.is_dir():
                if target_item.exists():
                    shutil.rmtree(target_item)
                shutil.copytree(item, target_item)
            else:
                shutil.copy2(item, target_item)

        # Stage all changes
        git_repo.index.add([str(target_path)])

        # Check if there are changes to commit
        if not git_repo.is_dirty():
            return {
                "success": True,
                "repo_path": str(repo_path),
                "commit_message": "No changes to commit",
                "pushed": False,
                "tag_result": None,
                "message": "No changes to commit",
            }

        # Commit changes
        git_repo.index.commit(commit_message)

        # Push if requested
        pushed = False
        if push:
            origin = git_repo.remote("origin")
            origin.push(branch)
            pushed = True

        # Create tag if requested
        tag_result = None
        if tag and pkg_json.version:
            tag_result = tag_pkg(
                pkg_dir=pkg_dir,
                meta_file=meta_file,
                force=force_tag,
                push=push,
                cache_dir=cache_dir,
                default_branch=default_branch,
            )

            if not tag_result["success"]:
                return {
                    "success": False,
                    "repo_path": str(repo_path),
                    "commit_message": commit_message,
                    "pushed": pushed,
                    "tag_result": tag_result,
                    "message": f"Commit successful but tagging failed: {tag_result['message']}",
                }

        # Build success message
        message_parts = [f"Successfully published {pkg_json.name}"]
        if pushed:
            message_parts.append("pushed to remote")
        if tag_result:
            message_parts.append(f"tagged as {tag_result['tag_name']}")

        return {
            "success": True,
            "repo_path": str(repo_path),
            "commit_message": commit_message,
            "pushed": pushed,
            "tag_result": tag_result,
            "message": ", ".join(message_parts),
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to publish package: {e}",
            "error": e,
        }


def publish_from_config(
    config_file: str,
    package_names: Optional[list] = None,
    commit_message: Optional[str] = None,
    push: bool = True,
    tag: bool = True,
    force_tag: bool = False,
    cache_dir: Optional[str] = None,
) -> list[Dict[str, Any]]:
    """Publish multiple packages from configuration file.

    Args:
        config_file: Path to repotree.json or similar config
        package_names: List of package names to publish (None = all)
        commit_message: Custom commit message
        push: Whether to push changes
        tag: Whether to create tags
        force_tag: Whether to force overwrite tags
        cache_dir: Cache directory path

    Returns:
        List of results for each package
    """
    from .models import RepotreeConfig

    config = RepotreeConfig.from_file(Path(config_file))
    results = []

    for entry in config.get_loaded_entries():
        if package_names and entry.pkg_name not in package_names:
            continue

        # Skip if no local directory
        if not entry.local_dir:
            results.append(
                {
                    "success": False,
                    "package": entry.pkg_name,
                    "message": "No local directory specified",
                }
            )
            continue

        # Check if local directory exists
        local_path = Path(entry.local_dir)
        if not local_path.exists():
            results.append(
                {
                    "success": False,
                    "package": entry.pkg_name,
                    "message": f"Local directory not found: {entry.local_dir}",
                }
            )
            continue

        # Check for pkg.json
        pkg_json_path = local_path / "pkg.json"
        if not pkg_json_path.exists():
            results.append(
                {
                    "success": False,
                    "package": entry.pkg_name,
                    "message": "No pkg.json found in local directory",
                }
            )
            continue

        # Publish the package
        result = publish_pkg(
            pkg_dir=str(local_path),
            commit_message=commit_message,
            push=push,
            tag=tag,
            force_tag=force_tag,
            cache_dir=cache_dir,
        )

        result["package"] = entry.pkg_name
        results.append(result)

    return results
