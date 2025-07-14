"""BDD tests for miniature load functionality using Allure."""

import pytest
import allure
import shutil
from pathlib import Path
from git import Repo

from miniature.load import load_pkg, load_pkgs_from_file


@allure.feature("Package Loading")
@allure.story("Load package from local git repository")
class TestLoadPackage:
    """BDD tests for loading packages from git repositories."""

    @allure.title("Load specific version of package from git repository")
    @allure.description(
        """
        Given a local git repository with tagged versions
        When loading a package with specific version
        Then the package should be copied to target directory with correct version
    """
    )
    def test_load_package_with_specific_version(
        self, package_repo, gitdbs_config, temp_dir
    ):
        """Test loading a specific version of a package."""
        with allure.step("Given a package repository with multiple versions"):
            repo_url = f"file://{package_repo}"
            target_dir = temp_dir / "loaded-package"

        with allure.step("When loading version 1.0.0 of the package"):
            result = load_pkg(
                repo=repo_url,
                path="packages/test-package",
                version="1.0.0",
                target_dir=str(target_dir),
                gitdbs_config=gitdbs_config,
            )

        with allure.step("Then the package should be loaded successfully"):
            assert result["success"] is True
            assert target_dir.exists()
            assert (target_dir / "pkg.json").exists()
            assert (target_dir / "index.py").exists()

        with allure.step("And the loaded version should match the requested version"):
            pkg_json = (target_dir / "pkg.json").read_text()
            assert '"version": "1.0.0"' in pkg_json

    @allure.title("Load latest version of package")
    @allure.description(
        """
        Given a local git repository with multiple tagged versions
        When loading a package with version="latest"
        Then the latest tagged version should be loaded
    """
    )
    def test_load_latest_package_version(self, package_repo, gitdbs_config, temp_dir):
        """Test loading the latest version of a package."""
        with allure.step("Given a package repository with multiple versions"):
            repo_url = f"file://{package_repo}"
            target_dir = temp_dir / "latest-package"

        with allure.step("When loading the latest version"):
            result = load_pkg(
                repo=repo_url,
                path="packages/test-package",
                version="latest",
                target_dir=str(target_dir),
                gitdbs_config=gitdbs_config,
            )

        with allure.step("Then the latest version (1.0.0) should be loaded"):
            assert result["success"] is True
            assert result["version"] == "packages/test-package/1.0.0"
            pkg_json = (target_dir / "pkg.json").read_text()
            assert '"version": "1.0.0"' in pkg_json

    @allure.title("Load package from branch without version")
    @allure.description(
        """
        Given a local git repository 
        When loading a package without specifying version
        Then the package should be loaded from the specified branch
    """
    )
    def test_load_package_from_branch(self, package_repo, gitdbs_config, temp_dir):
        """Test loading a package from a branch."""
        with allure.step("Given a package repository"):
            repo_url = f"file://{package_repo}"
            target_dir = temp_dir / "branch-package"

        with allure.step("When loading without version from main branch"):
            result = load_pkg(
                repo=repo_url,
                path="packages/test-package",
                branch="main",
                target_dir=str(target_dir),
                gitdbs_config=gitdbs_config,
            )

        with allure.step("Then the package should be loaded from main branch"):
            assert result["success"] is True
            assert target_dir.exists()
            assert (target_dir / "pkg.json").exists()


@allure.feature("Package Loading")
@allure.story("Load multiple packages from configuration file")
class TestLoadMultiplePackages:
    """BDD tests for loading multiple packages from config file."""

    @allure.title("Load multiple packages from configuration file")
    @allure.description(
        """
        Given a configuration file with multiple package definitions
        When loading packages from the file
        Then all packages should be loaded to their specified directories
    """
    )
    def test_load_packages_from_config_file(
        self, package_repo, gitdbs_config, temp_dir
    ):
        """Test loading multiple packages from a configuration file."""
        with allure.step("Given a configuration file with package definitions"):
            config_file = temp_dir / "packages.json"
            config_data = {
                "packages": {
                    "test-pkg-v1": {
                        "db-repo": f"file://{package_repo}",
                        "root-dir": "packages/test-package",
                        "version": "1.0.0",
                        "target-dir": str(temp_dir / "pkg-v1"),
                    },
                    "test-pkg-latest": {
                        "db-repo": f"file://{package_repo}",
                        "root-dir": "packages/test-package",
                        "version": "latest",
                        "target-dir": str(temp_dir / "pkg-latest"),
                    },
                }
            }
            import json

            config_file.write_text(json.dumps(config_data))

        with allure.step("When loading all packages from the config file"):
            results = load_pkgs_from_file(str(config_file), gitdbs_config=gitdbs_config)

        with allure.step("Then all packages should be loaded successfully"):
            assert len(results) == 2
            assert all(r["success"] for r in results)

        with allure.step("And each package should be in its target directory"):
            assert (temp_dir / "pkg-v1" / "pkg.json").exists()
            assert (temp_dir / "pkg-latest" / "pkg.json").exists()

    @allure.title("Load specific packages from configuration file")
    @allure.description(
        """
        Given a configuration file with multiple package definitions
        When loading only specific packages by name
        Then only the specified packages should be loaded
    """
    )
    def test_load_specific_packages_from_config(
        self, package_repo, gitdbs_config, temp_dir
    ):
        """Test loading specific packages from a configuration file."""
        with allure.step("Given a configuration file with multiple packages"):
            config_file = temp_dir / "packages.json"
            config_data = {
                "packages": {
                    "package-a": {
                        "db-repo": f"file://{package_repo}",
                        "root-dir": "packages/test-package",
                        "version": "1.0.0",
                        "target-dir": str(temp_dir / "pkg-a"),
                    },
                    "package-b": {
                        "db-repo": f"file://{package_repo}",
                        "root-dir": "packages/test-package",
                        "version": "0.9.0",
                        "target-dir": str(temp_dir / "pkg-b"),
                    },
                }
            }
            import json

            config_file.write_text(json.dumps(config_data))

        with allure.step("When loading only package-a"):
            results = load_pkgs_from_file(
                str(config_file),
                package_names=["package-a"],
                gitdbs_config=gitdbs_config,
            )

        with allure.step("Then only package-a should be loaded"):
            assert len(results) == 1
            assert results[0]["success"] is True
            assert (temp_dir / "pkg-a" / "pkg.json").exists()
            assert not (temp_dir / "pkg-b" / "pkg.json").exists()


@allure.feature("Package Loading")
@allure.story("Handle loading errors gracefully")
class TestLoadingErrors:
    """BDD tests for error handling in package loading."""

    @allure.title("Handle non-existent package path")
    @allure.description(
        """
        Given a valid repository
        When trying to load from a non-existent path
        Then an appropriate error should be returned
    """
    )
    def test_load_nonexistent_package_path(self, package_repo, gitdbs_config, temp_dir):
        """Test loading from a non-existent path."""
        with allure.step("Given a valid repository"):
            repo_url = f"file://{package_repo}"
            target_dir = temp_dir / "error-package"

        with allure.step("When loading from non-existent path"):
            result = load_pkg(
                repo=repo_url,
                path="packages/non-existent",
                target_dir=str(target_dir),
                gitdbs_config=gitdbs_config,
            )

        with allure.step("Then the operation should fail with error message"):
            assert result["success"] is False
            assert (
                "error" in result["message"].lower()
                or "not found" in result["message"].lower()
            )
            assert not target_dir.exists()

    @allure.title("Handle invalid version specification")
    @allure.description(
        """
        Given a package with specific versions
        When trying to load with non-existent version
        Then an appropriate error should be returned
    """
    )
    def test_load_invalid_version(self, package_repo, gitdbs_config, temp_dir):
        """Test loading with an invalid version."""
        with allure.step("Given a package with versions 0.9.0 and 1.0.0"):
            repo_url = f"file://{package_repo}"
            target_dir = temp_dir / "invalid-version"

        with allure.step("When loading non-existent version 2.0.0"):
            result = load_pkg(
                repo=repo_url,
                path="packages/test-package",
                version="2.0.0",
                target_dir=str(target_dir),
                gitdbs_config=gitdbs_config,
            )

        with allure.step("Then the operation should fail"):
            assert result["success"] is False
            assert (
                "not found" in result["message"].lower()
                or "no matching" in result["message"].lower()
            )
