import json
import os
import shutil
from typing import Optional, Dict, Any
from pathlib import Path
from pyshell import shell, ShellError
from .cache import get_cache


def push_pkg(
    pkg_dir: str = ".",
    meta_file: str = "pkg.json",
    commit_message: Optional[str] = None,
    push: bool = True,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Push a package directory to a local repository specified in meta file.

    Args:
        pkg_dir: Directory containing the package to publish
        meta_file: Name of the meta file (default: "pkg.json")
        commit_message: Custom commit message (default: "Update from {dirname}")
        push: Whether to push changes to remote (default: True)
        cache_dir: Cache directory path

    Returns:
        Dict containing operation result with keys:
        - success: bool
        - repo_path: str (path to local repository)
        - commit_message: str
        - pushed: bool
        - message: str

    Raises:
        FileNotFoundError: If meta file doesn't exist
        ShellError: If git operations fail
    """
    # Construct full path to meta file
    meta_file_path = os.path.join(pkg_dir, meta_file)

    # Validate meta file exists
    if not os.path.exists(meta_file_path):
        raise FileNotFoundError(f"Meta file not found: {meta_file_path}")

    # Load package configuration
    with open(meta_file_path, "r") as f:
        pkg_config = json.load(f)

    repo_url = pkg_config.get("db-repo")
    branch = pkg_config.get("branch", "main")
    root_dir = pkg_config.get("root-dir", "")

    if not repo_url:
        raise ValueError(f"No 'db-repo' found in {meta_file}")

    # Get cache instance and repository path
    cache = get_cache(Path(cache_dir) if cache_dir else None)
    local_repo_path = cache.get_repo_path(repo_url)

    # Clone or update repository if needed
    if not local_repo_path.exists():
        local_repo_path = cache.clone_or_update(repo_url, branch)

    # Set default commit message
    if commit_message is None:
        dirname = os.path.basename(os.path.abspath(pkg_dir))
        commit_message = f"Update from {dirname}"

    try:
        # Checkout appropriate branch
        shell(f"cd {local_repo_path} && git checkout {branch}")

        # Copy files from package directory to repo's root-dir
        target_path = (
            os.path.join(str(local_repo_path), root_dir)
            if root_dir
            else str(local_repo_path)
        )

        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        shutil.copytree(pkg_dir, target_path)

        # Check if there are any changes to commit
        try:
            status_output = shell(f"cd {local_repo_path} && git status --porcelain")

            if not status_output.strip():
                return {
                    "success": True,
                    "repo_path": str(local_repo_path),
                    "commit_message": commit_message,
                    "pushed": False,
                    "message": "No changes to commit - repository is up to date",
                }

        except ShellError:
            # If git status fails, continue anyway
            pass

        # Stage and commit changes
        shell(
            f"""
            cd {local_repo_path}
            git add .
            git commit -m "{commit_message}"
        """
        )

        if push:
            shell(f"cd {local_repo_path} && git push origin {branch}")
            result = {
                "success": True,
                "repo_path": local_repo_path,
                "commit_message": commit_message,
                "pushed": True,
                "message": "Successfully published to repository",
            }
        else:
            result = {
                "success": True,
                "repo_path": local_repo_path,
                "commit_message": commit_message,
                "pushed": False,
                "message": "Changes committed but not pushed",
            }

        return result

    except ShellError as e:
        raise
    except Exception as e:
        raise


def push_pkg_from_json(
    pkg_json_path: str,
    commit_message: Optional[str] = None,
    push: bool = True,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Push a package using full path to pkg.json file.

    This is a convenience function that extracts the directory and file name
    from the full pkg.json path.

    Args:
        pkg_json_path: Full path to pkg.json file
        commit_message: Custom commit message
        push: Whether to push changes to remote (default: True)
        cache_dir: Cache directory path

    Returns:
        Dict containing operation result

    Raises:
        FileNotFoundError: If pkg.json doesn't exist
        ShellError: If git operations fail
    """
    pkg_dir = os.path.dirname(os.path.abspath(pkg_json_path))
    meta_file = os.path.basename(pkg_json_path)

    return push_pkg(pkg_dir, meta_file, commit_message, push, cache_dir)
