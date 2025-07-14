"""Data models for miniature package management aligned with repotree requirements."""

from typing import Optional, Dict, Any, List
from pathlib import Path
import json


class CustomConfig:
    """Custom configuration for package operations."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @property
    def install(self) -> Optional[str]:
        """Get install command."""
        return self.config.get("install")

    @property
    def build(self) -> Optional[str]:
        """Get build command."""
        return self.config.get("build")

    def get(self, key: str, default=None):
        """Get custom config value."""
        return self.config.get(key, default)


class AsPkg:
    """Version specification for non-editable packages."""

    def __init__(self, version: str):
        self.version = version


class PackageDefinition:
    """Base package definition aligned with repotree structure."""

    def __init__(
        self,
        pkg_name: Optional[str] = None,
        domain: str = None,
        repo_name: Optional[str] = None,
        repo: Optional[str] = None,  # Alternative to repo_name
        branch: Optional[str] = None,
        tag: Optional[str] = None,  # Alternative to branch
        local_dir: str = None,
        loaded: bool = False,
        as_pkg: Optional[Dict[str, str]] = None,
        custom_config: Optional[Dict[str, Any]] = None,
        pkg_type: Optional[str] = None,
        version: Optional[str] = None,
        **kwargs,
    ):
        self.pkg_name = pkg_name
        self.domain = domain
        self.repo_name = repo_name or repo
        self.branch = branch
        self.tag = tag
        self.local_dir = local_dir
        self.loaded = loaded
        self.as_pkg = AsPkg(as_pkg["version"]) if as_pkg else None
        self.custom_config = CustomConfig(custom_config)
        self.pkg_type = pkg_type
        self.version = version
        self.extra = kwargs

    def get_branch_or_tag(self) -> str:
        """Get branch or tag, with branch taking precedence."""
        return self.branch or self.tag or "main"

    def get_repo_url(self) -> str:
        """Construct full repository URL from domain and repo name."""
        if not self.domain:
            return ""
        domain = self.domain.rstrip("/")
        if self.repo_name:
            return f"{domain}/{self.repo_name}"
        return domain

    def get_cache_key(self) -> str:
        """Get unique cache key for this package repository."""
        return (
            self.get_repo_url()
            .replace("https://", "")
            .replace("http://", "")
            .replace("/", "_")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "pkgName": self.pkg_name,
            "domain": self.domain,
            "localDir": self.local_dir,
            "loaded": self.loaded,
        }

        if self.repo_name:
            result["repoName"] = self.repo_name
        if self.branch:
            result["branch"] = self.branch
        elif self.tag:
            result["tag"] = self.tag

        if self.as_pkg:
            result["as_pkg"] = {"version": self.as_pkg.version}
        if self.custom_config.config:
            result["customConfig"] = self.custom_config.config
        if self.pkg_type:
            result["pkgType"] = self.pkg_type
        if self.version:
            result["version"] = self.version

        result.update(self.extra)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PackageDefinition":
        """Create from dictionary."""
        # Handle both camelCase and snake_case
        return cls(
            pkg_name=data.get("pkgName") or data.get("pkg_name"),
            domain=data.get("domain"),
            repo_name=data.get("repoName") or data.get("repo_name"),
            repo=data.get("repo"),
            branch=data.get("branch"),
            tag=data.get("tag"),
            local_dir=data.get("localDir") or data.get("local_dir"),
            loaded=data.get("loaded", False),
            as_pkg=data.get("as_pkg"),
            custom_config=data.get("customConfig") or data.get("custom_config"),
            pkg_type=data.get("pkgType") or data.get("pkg_type"),
            version=data.get("version"),
            **{
                k: v
                for k, v in data.items()
                if k
                not in [
                    "pkgName",
                    "pkg_name",
                    "domain",
                    "repoName",
                    "repo_name",
                    "repo",
                    "branch",
                    "tag",
                    "localDir",
                    "local_dir",
                    "loaded",
                    "as_pkg",
                    "customConfig",
                    "custom_config",
                    "pkgType",
                    "pkg_type",
                    "version",
                ]
            },
        )


class PkgJson:
    """Package metadata from pkg.json file."""

    def __init__(
        self,
        name: str,
        version: Optional[str] = None,
        description: Optional[str] = None,
        db_repo: Optional[str] = None,
        root_dir: Optional[str] = None,
        branch: Optional[str] = None,
        dependencies: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.db_repo = db_repo
        self.root_dir = root_dir
        self.branch = branch or "main"
        self.dependencies = [
            PackageDefinition.from_dict(d) for d in (dependencies or [])
        ]
        self.extra = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {"name": self.name}

        if self.version:
            result["version"] = self.version
        if self.description:
            result["description"] = self.description
        if self.db_repo:
            result["db-repo"] = self.db_repo
        if self.root_dir:
            result["root-dir"] = self.root_dir
        if self.branch != "main":
            result["branch"] = self.branch
        if self.dependencies:
            result["dependencies"] = [d.to_dict() for d in self.dependencies]

        result.update(self.extra)
        return result

    @classmethod
    def from_file(cls, file_path: Path) -> "PkgJson":
        """Load from pkg.json file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            name=data.get("name", ""),
            version=data.get("version"),
            description=data.get("description"),
            db_repo=data.get("db-repo"),
            root_dir=data.get("root-dir"),
            branch=data.get("branch"),
            dependencies=data.get("dependencies"),
            **{
                k: v
                for k, v in data.items()
                if k
                not in [
                    "name",
                    "version",
                    "description",
                    "db-repo",
                    "root-dir",
                    "branch",
                    "dependencies",
                ]
            },
        )

    def save(self, file_path: Path):
        """Save to pkg.json file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


class RepotreeConfig:
    """Repotree configuration from repotree.json."""

    def __init__(
        self,
        miniatures: Optional[List[Dict[str, Any]]] = None,
        repos: Optional[List[Dict[str, Any]]] = None,
    ):
        # Support both miniatures and legacy repos field
        entries = miniatures or repos or []
        self.entries = [PackageDefinition.from_dict(e) for e in entries]

    def get_loaded_entries(self) -> List[PackageDefinition]:
        """Get only loaded entries."""
        return [e for e in self.entries if e.loaded]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {"miniatures": [e.to_dict() for e in self.entries]}

    @classmethod
    def from_file(cls, file_path: Path) -> "RepotreeConfig":
        """Load from repotree.json file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(miniatures=data.get("miniatures"), repos=data.get("repos"))

    def save(self, file_path: Path):
        """Save to repotree.json file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
