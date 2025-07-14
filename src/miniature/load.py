"""Package loading functionality aligned with repotree requirements."""

import os
import re
import json
import shutil
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from .cache import get_cache, RepositoryCache
from .models import PackageDefinition, RepotreeConfig, PkgJson
from git import Repo
import packaging.version
import packaging.specifiers


def load_pkg(
    repo: Optional[str] = None,
    version: Optional[str] = None,
    target_dir: Optional[str] = None,
    branch: str = "main",
    clean: bool = False,
    gitdbs_config: Optional[str] = None,  # Deprecated
    cache_dir: Optional[str] = None,
    # New parameters for repotree
    package_def: Optional[PackageDefinition] = None,
    use_symlink: bool = False,
) -> Dict[str, Any]:
    """Load a package from a git repository using cache.

    Args:
        repo: Repository URL (can be constructed from package_def)
        version: Version/tag to load (e.g., "v1.0.0", ">=0.3.2", "latest")
        target_dir: Directory to copy/link to
        branch: Branch to use if no version specified
        clean: Whether to clean existing target directory
        gitdbs_config: DEPRECATED - Path to gitdbs config file
        cache_dir: Cache directory path
        package_def: PackageDefinition object with full repotree config
        use_symlink: Whether to create symlink instead of copying

    Returns:
        Dict containing operation result
    """
    # Handle package_def for repotree compatibility
    if package_def:
        repo = repo or package_def.get_repo_url()
        branch = branch if branch != "main" else package_def.get_branch_or_tag()
        target_dir = target_dir or package_def.local_dir

        # Handle as_pkg for version constraints
        if package_def.as_pkg:
            version = version or package_def.as_pkg.version

    # Validate inputs
    if not repo:
        return {"success": False, "message": "Repository URL is required"}

    # Set default target directory
    if target_dir is None:
        # Extract repository name from URL
        repo_name = repo.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        # Add branch suffix if not main/master
        if branch not in ['main', 'master']:
            target_dir = f"{repo_name}-{branch}"
        else:
            target_dir = repo_name

    target_path = Path(target_dir)

    # Clean target directory if requested
    if clean and target_path.exists():
        if target_path.is_symlink():
            target_path.unlink()
        else:
            shutil.rmtree(target_path)

    try:
        # Get cache instance
        cache = get_cache(Path(cache_dir) if cache_dir else None)

        # Clone or update repository in cache
        repo_path = cache.clone_or_update(repo, branch)

        # Get the git repository
        git_repo = Repo(repo_path)

        # Determine version to checkout
        actual_version = None

        if version:
            if version == "latest":
                # Get latest tag for the repository
                latest_tag = _find_latest_tag(git_repo)
                if latest_tag:
                    git_repo.git.checkout(latest_tag)
                    actual_version = latest_tag
                else:
                    # No tags, use current branch
                    actual_version = git_repo.active_branch.name
            else:
                # Check if it's a direct tag/commit or version spec
                if "/" in version or _is_commit_sha(version):
                    # Direct reference
                    git_repo.git.checkout(version)
                    actual_version = version
                else:
                    # Version specification - find matching tag
                    matching_tag = _find_matching_tag(git_repo, version)
                    if matching_tag:
                        git_repo.git.checkout(matching_tag)
                        actual_version = matching_tag
                    else:
                        return {
                            "success": False,
                            "message": f"No tag found matching version {version}",
                        }
        else:
            # Checkout branch
            if branch in git_repo.heads:
                git_repo.heads[branch].checkout()
            elif f"origin/{branch}" in git_repo.refs:
                git_repo.create_head(branch, f"origin/{branch}").checkout()
            actual_version = branch

        # Create target directory parent if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy or symlink entire repository
        if use_symlink:
            cache.create_symlink(repo, target_path, ".", branch)
        else:
            # Copy entire repository
            shutil.copytree(repo_path, target_path, dirs_exist_ok=True)
            
            # If target is on Windows filesystem (WSL), disable filemode tracking
            from .utils import should_disable_filemode, fix_git_filemode
            if should_disable_filemode(str(target_path)):
                try:
                    fix_git_filemode(str(target_path))
                    print(f"Note: Disabled git filemode tracking for Windows filesystem")
                except Exception:
                    pass  # Silently ignore if fix fails

        # Handle custom config if present
        if package_def and package_def.custom_config.install:
            print(
                f"Note: Run '{package_def.custom_config.install}' to install the package"
            )

        return {
            "success": True,
            "target_dir": str(target_path),
            "repo": repo,
            "branch": branch,
            "version": actual_version,
            "message": f"Successfully loaded repository from {repo} (branch: {branch})",
        }

    except Exception as e:
        return {
            "success": False,
            "target_dir": str(target_path),
            "repo": repo,
            "branch": branch,
            "version": version or branch,
            "message": f"Failed to load repository: {e}",
            "error": e,
        }


def load_pkgs_from_file(
    config_file: str,
    package_names: Optional[List[str]] = None,
    clean: bool = False,
    gitdbs_config: Optional[str] = None,  # Deprecated
    cache_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Load packages from a configuration file.

    Supports pkg.json (with dependencies), miniature.json, and repotree.json formats.

    Args:
        config_file: Path to config file (pkg.json, miniature.json, or repotree.json)
        package_names: List of package names to load (None = load all)
        clean: Whether to clean existing target directories
        gitdbs_config: DEPRECATED
        cache_dir: Cache directory path

    Returns:
        List of results for each package
    """
    config_path = Path(config_file)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_path, "r") as f:
        data = json.load(f)

    results = []

    # Check if it's pkg.json format (has "dependencies" array and optionally "name")
    if "dependencies" in data and isinstance(data["dependencies"], list):
        # Load as pkg.json with dependencies
        pkg_config = PkgJson.from_file(config_path)

        for entry in pkg_config.dependencies:
            if package_names and entry.pkg_name not in package_names:
                continue

            # Set loaded=True for dependencies we want to load
            entry.loaded = True

            result = load_pkg(
                package_def=entry,
                clean=clean,
                cache_dir=cache_dir,
                use_symlink=False,  # TODO: Make configurable
            )
            results.append(result)

    # Check if it's repotree format (has "miniatures" or "repos")
    elif "miniatures" in data or "repos" in data:
        # Load as repotree config
        config = RepotreeConfig.from_file(config_path)

        for entry in config.get_loaded_entries():
            if package_names and entry.pkg_name not in package_names:
                continue

            result = load_pkg(
                package_def=entry,
                clean=clean,
                cache_dir=cache_dir,
                use_symlink=False,  # TODO: Make configurable
            )
            results.append(result)

    # Legacy miniature format with "packages"
    elif "packages" in data:
        packages = data["packages"]

        if package_names is None:
            package_names = list(packages.keys())

        for name in package_names:
            if name not in packages:
                results.append(
                    {
                        "success": False,
                        "message": f"Package '{name}' not found in config",
                    }
                )
                continue

            pkg_config = packages[name]

            # Convert to PackageDefinition
            package_def = PackageDefinition(
                pkg_name=name,
                domain=pkg_config.get("db-repo", ""),
                path_name=pkg_config.get("root-dir", "."),
                branch=pkg_config.get("branch", "main"),
                local_dir=pkg_config.get("target-dir", name),
                version=pkg_config.get("version"),
                loaded=True,
            )

            result = load_pkg(package_def=package_def, clean=clean, cache_dir=cache_dir)
            results.append(result)

    else:
        raise ValueError(
            "Invalid config file format - expected 'dependencies', 'miniatures', or 'packages' field"
        )

    return results


def _find_latest_tag(repo: Repo) -> Optional[str]:
    """Find the latest tag in a repository.

    Args:
        repo: Git repository object

    Returns:
        Latest tag name or None
    """
    try:
        tags = list(repo.tags)

        if not tags:
            return None

        # Get all tags
        package_tags = [str(tag.name) for tag in tags]

        # Sort by version
        version_tags = []

        for tag_name in package_tags:
            try:
                # Extract version part
                if "/" in tag_name:
                    version_part = tag_name.split("/")[-1]
                else:
                    version_part = tag_name

                # Remove 'v' prefix if present
                version_part = version_part.lstrip("v")

                ver = packaging.version.parse(version_part)
                version_tags.append((tag_name, ver))
            except packaging.version.InvalidVersion:
                continue

        if not version_tags:
            return package_tags[-1]  # Return last tag if no valid versions

        # Sort by version and return latest
        version_tags.sort(key=lambda x: x[1])
        return version_tags[-1][0]

    except Exception:
        return None


def _find_matching_tag(repo: Repo, version_spec: str) -> Optional[str]:
    """Find a tag matching version specification.

    Args:
        repo: Git repository object
        version_spec: Version specification (e.g., ">=1.0.0")

    Returns:
        Matching tag name or None
    """
    try:
        tags = list(repo.tags)

        if not tags:
            return None

        # Create specifier set
        specifier_set = packaging.specifiers.SpecifierSet(version_spec)

        # Filter and match tags
        valid_tags = []

        for tag in tags:
            tag_name = str(tag.name)

            try:
                # Extract version part
                if "/" in tag_name:
                    version_part = tag_name.split("/")[-1]
                else:
                    version_part = tag_name

                # Remove 'v' prefix if present
                version_part = version_part.lstrip("v")

                ver = packaging.version.parse(version_part)

                # Check if version matches specifier
                if ver in specifier_set:
                    valid_tags.append((tag_name, ver))
            except packaging.version.InvalidVersion:
                continue

        if not valid_tags:
            return None

        # Sort by version and return latest matching
        valid_tags.sort(key=lambda x: x[1])
        return valid_tags[-1][0]

    except Exception:
        return None


def _is_commit_sha(value: str) -> bool:
    """Check if a value is a git commit SHA."""
    return bool(re.match(r"^[0-9a-f]{6,40}$", value, re.IGNORECASE))
