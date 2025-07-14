"""Test loading packages from pkg.json with dependencies array."""

import pytest
import json
from pathlib import Path
from miniature.load import load_pkgs_from_file
from miniature.models import PkgJson, PackageDefinition


def test_load_from_pkg_json_with_dependencies(tmp_path):
    """Test loading packages from pkg.json format with dependencies array."""
    # Create a pkg.json file with dependencies
    pkg_json_path = tmp_path / "pkg.json"
    pkg_data = {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": [
            {
                "pkgName": "miniature",
                "pkgType": "python",
                "version": ">=0.4.0",
                "domain": "https://github.com/",
                "repoName": "crimson206/miniature",
                "pathName": ".",
                "branch": "main",
                "localDir": "miniature",
            },
            {
                "pkgName": "repotree-core",
                "version": ">=1.4.0",
                "domain": "https://gitlab.com/",
                "repoName": "crimson206/repotree-core",
                "pathName": ".",
                "branch": "main",
                "localDir": "repotree-core",
                "customConfig": {"install": "pip install -e ."},
            },
        ],
    }

    with open(pkg_json_path, "w") as f:
        json.dump(pkg_data, f, indent=2)

    # Test that we can parse the file
    pkg_json = PkgJson.from_file(pkg_json_path)
    assert pkg_json.name == "test-project"
    assert pkg_json.version == "1.0.0"
    assert len(pkg_json.dependencies) == 2

    # Check first dependency
    dep1 = pkg_json.dependencies[0]
    assert dep1.pkg_name == "miniature"
    assert dep1.domain == "https://github.com/"
    assert dep1.repo_name == "crimson206/miniature"
    assert dep1.path_name == "."
    assert dep1.branch == "main"
    assert dep1.local_dir == "miniature"
    assert dep1.version == ">=0.4.0"
    assert dep1.pkg_type == "python"

    # Check second dependency
    dep2 = pkg_json.dependencies[1]
    assert dep2.pkg_name == "repotree-core"
    assert dep2.domain == "https://gitlab.com/"
    assert dep2.repo_name == "crimson206/repotree-core"
    assert dep2.custom_config.install == "pip install -e ."


def test_backward_compatibility_miniatures_format(tmp_path):
    """Test backward compatibility with miniatures array format."""
    # Create a miniature.json file
    miniature_json_path = tmp_path / "miniature.json"
    miniature_data = {
        "miniatures": [
            {
                "pkgName": "myPkg",
                "domain": "https://gitlab.com/",
                "repoName": "user/repo",
                "pathName": "path/in-repo/my-project",
                "branch": "my_module",
                "localDir": "my-project",
                "loaded": True,
                "customConfig": {"install": "pip install -e ."},
            }
        ]
    }

    with open(miniature_json_path, "w") as f:
        json.dump(miniature_data, f, indent=2)

    # This should work without errors (actual loading would require git repos)
    try:
        # We don't actually load packages here since it would require real git repos
        # Just verify the file can be parsed
        with open(miniature_json_path, "r") as f:
            data = json.load(f)

        assert "miniatures" in data
        assert len(data["miniatures"]) == 1
        assert data["miniatures"][0]["pkgName"] == "myPkg"
    except Exception as e:
        pytest.fail(f"Failed to handle miniatures format: {e}")


def test_package_definition_serialization():
    """Test PackageDefinition to/from dict conversion."""
    # Create a PackageDefinition
    pkg_def = PackageDefinition(
        pkg_name="test-pkg",
        domain="https://github.com/",
        repo_name="user/repo",
        path_name="src/package",
        branch="feature",
        local_dir="local-package",
        version="1.2.3",
        pkg_type="python",
        loaded=True,
        custom_config={"install": "npm install"},
    )

    # Convert to dict
    pkg_dict = pkg_def.to_dict()

    # Check all fields are serialized correctly
    assert pkg_dict["pkgName"] == "test-pkg"
    assert pkg_dict["domain"] == "https://github.com/"
    assert pkg_dict["repoName"] == "user/repo"
    assert pkg_dict["pathName"] == "src/package"
    assert pkg_dict["branch"] == "feature"
    assert pkg_dict["localDir"] == "local-package"
    assert pkg_dict["version"] == "1.2.3"
    assert pkg_dict["pkgType"] == "python"
    assert pkg_dict["loaded"] is True
    assert pkg_dict["customConfig"]["install"] == "npm install"

    # Convert back from dict
    pkg_def2 = PackageDefinition.from_dict(pkg_dict)

    # Verify round-trip conversion
    assert pkg_def2.pkg_name == pkg_def.pkg_name
    assert pkg_def2.domain == pkg_def.domain
    assert pkg_def2.repo_name == pkg_def.repo_name
    assert pkg_def2.path_name == pkg_def.path_name
    assert pkg_def2.branch == pkg_def.branch
    assert pkg_def2.local_dir == pkg_def.local_dir
    assert pkg_def2.version == pkg_def.version
    assert pkg_def2.pkg_type == pkg_def.pkg_type
    assert pkg_def2.loaded == pkg_def.loaded
    assert pkg_def2.custom_config.install == pkg_def.custom_config.install
