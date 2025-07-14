"""Cache management for git repositories in repotree system."""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import json
from git import Repo


class RepositoryCache:
    """Manages local cache of git repositories."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize repository cache.

        Args:
            cache_dir: Cache directory path. Defaults to ~/.miniature/cache
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".miniature" / "cache"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_index_file = self.cache_dir / "index.json"
        self._load_index()

    def _load_index(self):
        """Load cache index from file."""
        if self._cache_index_file.exists():
            with open(self._cache_index_file, "r") as f:
                self._index = json.load(f)
        else:
            self._index = {}

    def _save_index(self):
        """Save cache index to file."""
        with open(self._cache_index_file, "w") as f:
            json.dump(self._index, f, indent=2)

    def get_cache_key(self, repo_url: str, branch: Optional[str] = None) -> str:
        """Generate cache key from repository URL and optional branch.
        
        Args:
            repo_url: Repository URL
            branch: Optional branch name to include in cache key
            
        Returns:
            Cache key string
        """
        # Remove protocol and replace special characters
        key = repo_url.replace("https://", "").replace("http://", "")
        key = key.replace("file://", "file_")
        key = key.replace("/", "_").replace(":", "_")
        
        # Add branch suffix if provided
        if branch and branch not in ['main', 'master']:
            key = f"{key}@{branch}"
            
        return key

    def get_repo_path(self, repo_url: str, branch: Optional[str] = None) -> Path:
        """Get local cache path for a repository.
        
        Args:
            repo_url: Repository URL
            branch: Optional branch name for branch-specific cache
            
        Returns:
            Path to cached repository
        """
        cache_key = self.get_cache_key(repo_url, branch)
        return self.cache_dir / cache_key

    def has_repo(self, repo_url: str, branch: Optional[str] = None) -> bool:
        """Check if repository is in cache.
        
        Args:
            repo_url: Repository URL
            branch: Optional branch name for branch-specific cache
            
        Returns:
            True if repository exists in cache
        """
        repo_path = self.get_repo_path(repo_url, branch)
        return repo_path.exists() and (repo_path / ".git").exists()

    def clone_or_update(self, repo_url: str, branch: Optional[str] = None, use_branch_cache: bool = True) -> Path:
        """Clone repository to cache or update if exists.

        Args:
            repo_url: Repository URL
            branch: Branch to checkout (optional)
            use_branch_cache: Whether to use branch-specific caching

        Returns:
            Path to local repository
        """
        # Use branch-specific cache for non-default branches
        cache_branch = branch if use_branch_cache and branch not in ['main', 'master'] else None
        repo_path = self.get_repo_path(repo_url, cache_branch)

        if self.has_repo(repo_url, cache_branch):
            # Update existing repository
            repo = Repo(repo_path)

            # Fetch latest changes
            try:
                repo.remotes.origin.fetch()
            except Exception as e:
                print(f"Warning: Failed to fetch updates for {repo_url}: {e}")

            # Checkout branch if specified
            if branch and branch in repo.heads:
                repo.heads[branch].checkout()
        else:
            # Clone new repository
            print(f"Cloning {repo_url} to cache...")
            
            # Use single-branch clone for non-default branches
            if branch and branch not in ['main', 'master']:
                try:
                    repo = Repo.clone_from(
                        repo_url, 
                        repo_path,
                        branch=branch,
                        single_branch=True,
                        depth=1  # Shallow clone for better performance
                    )
                except Exception as e:
                    # If branch doesn't exist, try normal clone and create branch
                    if "not found" in str(e).lower():
                        print(f"Branch '{branch}' not found. Cloning default branch and creating new branch...")
                        repo = Repo.clone_from(repo_url, repo_path)
                        # Create new branch
                        repo.create_head(branch)
                        repo.heads[branch].checkout()
                    else:
                        raise
            else:
                repo = Repo.clone_from(repo_url, repo_path)

        # Update index with branch info
        index_key = f"{repo_url}@{branch}" if cache_branch else repo_url
        self._index[index_key] = {
            "cache_key": self.get_cache_key(repo_url, cache_branch),
            "path": str(repo_path),
            "branch": branch,
            "last_updated": repo.head.commit.committed_datetime.isoformat(),
        }
        self._save_index()
        
        # If cache is on Windows filesystem (WSL), disable filemode tracking
        if str(repo_path).startswith('/mnt/'):
            try:
                repo.config_writer().set_value("core", "filemode", False).release()
            except Exception:
                pass  # Silently ignore if setting fails

        return repo_path

    def get_repo(self, repo_url: str, ensure_latest: bool = True) -> Optional[Path]:
        """Get repository from cache.

        Args:
            repo_url: Repository URL
            ensure_latest: Whether to fetch latest changes

        Returns:
            Path to local repository or None if not in cache
        """
        if not self.has_repo(repo_url):
            return None

        repo_path = self.get_repo_path(repo_url)

        if ensure_latest:
            try:
                repo = Repo(repo_path)
                repo.remotes.origin.fetch()
            except Exception as e:
                print(f"Warning: Failed to fetch updates: {e}")

        return repo_path

    def remove_repo(self, repo_url: str):
        """Remove repository from cache."""
        repo_path = self.get_repo_path(repo_url)

        if repo_path.exists():
            shutil.rmtree(repo_path)

        if repo_url in self._index:
            del self._index[repo_url]
            self._save_index()

    def clear_cache(self):
        """Clear entire cache."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index = {}
        self._save_index()

    def list_cached_repos(self) -> Dict[str, Any]:
        """List all cached repositories."""
        return self._index.copy()

    def create_symlink(self, repo_url: str, target_path: Path, package_path: str = ".", branch: Optional[str] = None):
        """Create symlink from cache to target location.

        Args:
            repo_url: Repository URL
            target_path: Where to create the symlink
            package_path: Path within repository to link
            branch: Optional branch for branch-specific cache
        """
        cache_branch = branch if branch not in ['main', 'master'] else None
        repo_path = self.get_repo_path(repo_url, cache_branch)

        if not self.has_repo(repo_url, cache_branch):
            raise ValueError(f"Repository {repo_url} (branch: {branch}) not in cache")

        source = repo_path / package_path

        if not source.exists():
            raise ValueError(f"Package path {package_path} not found in repository")

        # Create parent directory if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing target if it exists
        if target_path.exists() or target_path.is_symlink():
            if target_path.is_symlink():
                target_path.unlink()
            elif target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()

        # Create symlink
        target_path.symlink_to(source)

        print(f"Created symlink: {target_path} -> {source}")


# Global cache instance
_global_cache = None


def get_cache(cache_dir: Optional[Path] = None) -> RepositoryCache:
    """Get global repository cache instance.

    Args:
        cache_dir: Optional cache directory path

    Returns:
        RepositoryCache instance
    """
    global _global_cache

    if _global_cache is None or (cache_dir and _global_cache.cache_dir != cache_dir):
        _global_cache = RepositoryCache(cache_dir)

    return _global_cache
