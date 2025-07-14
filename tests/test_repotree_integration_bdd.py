"""BDD integration tests for repotree functionality using Allure."""

import pytest
import allure
import json
import shutil
from pathlib import Path
from git import Repo


@allure.feature("Repotree Integration")
@allure.story("Load packages from pkg.json configuration")
class TestRepotreeIntegration:
    """Integration tests for repotree package management system."""

    @allure.title("Load multiple packages from pkg.json configuration")
    @allure.description(
        """
        Given a pkg.json with multiple package dependencies
        And bare git repositories containing those packages
        When loading packages using pkg.json configuration
        Then all packages should be loaded to their specified directories
        And version constraints should be respected
    """
    )
    @pytest.mark.integration
    def test_load_packages_from_pkg_json_config(self, temp_dir):
        """Test loading packages from pkg.json configuration."""

        with allure.step("Given bare repositories with packages"):
            # Create first bare repo with a Python package
            bare_repo1 = temp_dir / "repos" / "python-pkg.git"
            bare_repo1.mkdir(parents=True)
            bare1 = Repo.init(str(bare_repo1), bare=True)

            # Create working clone to add content
            work_repo1 = temp_dir / "work" / "python-pkg"
            work_repo1.mkdir(parents=True)
            work1 = bare1.clone(str(work_repo1))

            # Add Python package
            py_pkg = work_repo1 / "src" / "math_utils"
            py_pkg.mkdir(parents=True)
            (py_pkg / "__init__.py").write_text("__version__ = '1.0.0'")
            (py_pkg / "calc.py").write_text("def add(a, b):\n    return a + b")
            (work_repo1 / "src" / "pkg.json").write_text(
                json.dumps(
                    {"name": "math-utils", "version": "1.0.0", "pkgType": "python"}
                )
            )

            work1.index.add(
                ["src/math_utils/__init__.py", "src/math_utils/calc.py", "src/pkg.json"]
            )
            work1.index.commit("Add math utils package v1.0.0")
            work1.create_tag("src/math_utils/1.0.0", message="Version 1.0.0")

            # Add version 1.1.0
            (py_pkg / "calc.py").write_text(
                "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b"
            )
            (work_repo1 / "src" / "pkg.json").write_text(
                json.dumps(
                    {"name": "math-utils", "version": "1.1.0", "pkgType": "python"}
                )
            )
            work1.index.add(["src/math_utils/calc.py", "src/pkg.json"])
            work1.index.commit("Add multiply function v1.1.0")
            work1.create_tag("src/math_utils/1.1.0", message="Version 1.1.0")

            # Push to bare repo
            work1.remote().push()
            work1.remote().push(tags=True)

            # Create second bare repo with a config package
            bare_repo2 = temp_dir / "repos" / "config-pkg.git"
            bare_repo2.mkdir(parents=True)
            bare2 = Repo.init(str(bare_repo2), bare=True)

            work_repo2 = temp_dir / "work" / "config-pkg"
            work_repo2.mkdir(parents=True)
            work2 = bare2.clone(str(work_repo2))

            # Add config package
            config_pkg = work_repo2 / "configs" / "app-config"
            config_pkg.mkdir(parents=True)
            (config_pkg / "config.json").write_text(
                json.dumps({"app_name": "TestApp", "version": "2.0.0"})
            )
            (config_pkg / "pkg.json").write_text(
                json.dumps({"name": "app-config", "version": "2.0.0"})
            )

            work2.index.add(
                ["configs/app-config/config.json", "configs/app-config/pkg.json"]
            )
            work2.index.commit("Add app config v2.0.0")
            work2.create_tag("configs/app-config/2.0.0", message="Version 2.0.0")
            work2.remote().push()
            work2.remote().push(tags=True)

        with allure.step("And a pkg.json configuration"):
            pkg_config = {
                "name": "test-project",
                "version": "1.0.0",
                "dependencies": [
                    {
                        "pkgName": "math-utils",
                        "pkgType": "python",
                        "version": ">=1.0.0",
                        "domain": f"file://{bare_repo1}/",
                        "repoName": "",
                        "pathName": "src/math_utils",
                        "branch": "main",
                        "localDir": "lib/math",
                    },
                    {
                        "pkgName": "app-config",
                        "version": "latest",
                        "domain": f"file://{bare_repo2}/",
                        "pathName": "configs/app-config",
                        "branch": "main",
                        "localDir": "config",
                    },
                ],
            }

            config_file = temp_dir / "project" / "pkg.json"
            config_file.parent.mkdir()
            config_file.write_text(json.dumps(pkg_config, indent=2))

        with allure.step("And a gitdbs configuration"):
            gitdbs_config = [
                {
                    "name": "python-pkg",
                    "db-repo": f"file://{bare_repo1}/",
                    "local_path": str(temp_dir / "cache" / "python-pkg"),
                },
                {
                    "name": "config-pkg",
                    "db-repo": f"file://{bare_repo2}/",
                    "local_path": str(temp_dir / "cache" / "config-pkg"),
                },
            ]

            gitdbs_file = temp_dir / "project" / ".miniature" / "gitdbs.json"
            gitdbs_file.parent.mkdir(parents=True)
            gitdbs_file.write_text(json.dumps(gitdbs_config, indent=2))

        with allure.step("When loading packages using miniature"):
            # This simulates what repotree-core would do
            import os

            os.chdir(str(config_file.parent))

            from miniature.load import load_pkg
            from miniature.models import PkgJson

            # Load the pkg.json file
            pkg_json = PkgJson.from_file(config_file)

            results = []
            for dep in pkg_json.dependencies:
                result = load_pkg(
                    repo=dep.get_repo_url(),
                    path=dep.path_name,
                    version=dep.version or (dep.as_pkg.version if dep.as_pkg else None),
                    target_dir=dep.local_dir,
                    branch=dep.get_branch_or_tag(),
                    gitdbs_config=str(gitdbs_file),
                )
                results.append(result)

        with allure.step("Then all packages should be loaded successfully"):
            assert len(results) == 2
            assert all(r["success"] for r in results)

        with allure.step("And math-utils should be loaded with version >= 1.0.0"):
            assert (config_file.parent / "lib" / "math" / "calc.py").exists()
            # Should load 1.1.0 as it's the latest matching >=1.0.0
            assert (
                "multiply"
                in (config_file.parent / "lib" / "math" / "calc.py").read_text()
            )

        with allure.step("And app-config should be loaded with latest version"):
            assert (config_file.parent / "config" / "config.json").exists()
            config_content = json.loads(
                (config_file.parent / "config" / "config.json").read_text()
            )
            assert config_content["version"] == "2.0.0"

    @allure.title("Publish and load cycle with branch-based versioning")
    @allure.description(
        """
        Given packages in different branches (main, dev)
        When publishing packages with branch-specific tags
        Then tags should include branch name for non-default branches
        And loading should respect branch-based versioning
    """
    )
    @pytest.mark.integration
    def test_branch_based_versioning(self, temp_dir):
        """Test branch-based versioning as described in pkgStructure.md."""

        with allure.step("Given a bare repository"):
            bare_repo = temp_dir / "repos" / "multi-branch.git"
            bare_repo.mkdir(parents=True)
            bare = Repo.init(str(bare_repo), bare=True)

            work_repo = temp_dir / "work" / "multi-branch"
            work_repo.mkdir(parents=True)
            work = bare.clone(str(work_repo))

        with allure.step("And a package in main branch"):
            pkg_dir = work_repo / "packages" / "feature"
            pkg_dir.mkdir(parents=True)

            (pkg_dir / "pkg.json").write_text(
                json.dumps({"name": "feature", "version": "1.0.0", "branch": "main"})
            )
            (pkg_dir / "feature.py").write_text("# Main branch feature v1.0.0")

            work.index.add(["packages/feature/pkg.json", "packages/feature/feature.py"])
            work.index.commit("Add feature v1.0.0 on main")

            # Tag without branch prefix for default branch
            work.create_tag("packages/feature/1.0.0", message="Release v1.0.0")

        with allure.step("And the same package in dev branch with different version"):
            # Create dev branch
            work.create_head("dev")
            work.heads.dev.checkout()

            (pkg_dir / "pkg.json").write_text(
                json.dumps({"name": "feature", "version": "2.0.0", "branch": "dev"})
            )
            (pkg_dir / "feature.py").write_text(
                "# Dev branch feature v2.0.0\n# New experimental features"
            )

            work.index.add(["packages/feature/pkg.json", "packages/feature/feature.py"])
            work.index.commit("Add feature v2.0.0 on dev")

            # Tag with branch prefix for non-default branch
            work.create_tag("packages/feature/dev/2.0.0", message="Dev release v2.0.0")

        with allure.step("When pushing both branches"):
            work.remote().push("main")
            work.remote().push("dev")
            work.remote().push(tags=True)

        with allure.step("And loading from main branch"):
            from miniature.load import load_pkg

            gitdbs_config = [
                {
                    "db-repo": f"file://{bare_repo}/",
                    "local_path": str(temp_dir / "cache" / "multi-branch"),
                }
            ]
            gitdbs_file = temp_dir / ".miniature" / "gitdbs.json"
            gitdbs_file.parent.mkdir(exist_ok=True)
            gitdbs_file.write_text(json.dumps(gitdbs_config))

            main_result = load_pkg(
                repo=f"file://{bare_repo}/",
                path="packages/feature",
                version="latest",
                branch="main",
                target_dir=str(temp_dir / "main-feature"),
                gitdbs_config=str(gitdbs_file),
            )

        with allure.step("Then main branch version should be loaded"):
            assert main_result["success"] is True
            assert "1.0.0" in main_result["version"]
            content = (temp_dir / "main-feature" / "feature.py").read_text()
            assert "Main branch" in content

        with allure.step("When loading from dev branch"):
            dev_result = load_pkg(
                repo=f"file://{bare_repo}/",
                path="packages/feature",
                version="latest",
                branch="dev",
                target_dir=str(temp_dir / "dev-feature"),
                gitdbs_config=str(gitdbs_file),
            )

        with allure.step("Then dev branch version should be loaded"):
            assert dev_result["success"] is True
            assert "dev/2.0.0" in dev_result["version"]
            content = (temp_dir / "dev-feature" / "feature.py").read_text()
            assert "Dev branch" in content
            assert "experimental" in content


@allure.feature("Repotree Integration")
@allure.story("Dependency management")
class TestDependencyManagement:
    """Tests for managing package dependencies in repotree."""

    @allure.title("Load package with dependencies")
    @allure.description(
        """
        Given a package with dependencies defined in pkg.json
        When loading the package
        Then its dependencies should also be installable
    """
    )
    @pytest.mark.integration
    def test_load_package_with_dependencies(self, temp_dir):
        """Test loading a package that has dependencies."""

        with allure.step("Given repositories with dependent packages"):
            # Create base library repo
            base_repo = temp_dir / "repos" / "base-lib.git"
            base_repo.mkdir(parents=True)
            Repo.init(str(base_repo), bare=True)

            # Create app repo that depends on base library
            app_repo = temp_dir / "repos" / "app.git"
            app_repo.mkdir(parents=True)
            Repo.init(str(app_repo), bare=True)

            # Set up base library
            base_work = temp_dir / "work" / "base-lib"
            base_work.mkdir(parents=True)
            base_git = Repo.clone_from(str(base_repo), str(base_work))

            base_pkg = base_work / "libs" / "base"
            base_pkg.mkdir(parents=True)
            (base_pkg / "pkg.json").write_text(
                json.dumps(
                    {"name": "base-lib", "version": "1.0.0", "pkgType": "python"}
                )
            )
            (base_pkg / "base.py").write_text("def get_version():\n    return '1.0.0'")

            base_git.index.add(["libs/base/pkg.json", "libs/base/base.py"])
            base_git.index.commit("Add base library")
            base_git.create_tag("libs/base/1.0.0")
            base_git.remote().push()
            base_git.remote().push(tags=True)

            # Set up app with dependency
            app_work = temp_dir / "work" / "app"
            app_work.mkdir(parents=True)
            app_git = Repo.clone_from(str(app_repo), str(app_work))

            app_pkg = app_work / "apps" / "main-app"
            app_pkg.mkdir(parents=True)
            (app_pkg / "pkg.json").write_text(
                json.dumps(
                    {
                        "name": "main-app",
                        "version": "1.0.0",
                        "dependencies": [
                            {
                                "pkgName": "base-lib",
                                "pkgType": "python",
                                "version": ">=1.0.0",
                                "domain": f"file://{base_repo}/",
                                "repoName": "",
                                "pathName": "libs/base",
                                "branch": "main",
                                "localDir": "vendor/base-lib",
                            }
                        ],
                    }
                )
            )
            (app_pkg / "app.py").write_text(
                "from vendor.base_lib import base\nprint(base.get_version())"
            )

            app_git.index.add(["apps/main-app/pkg.json", "apps/main-app/app.py"])
            app_git.index.commit("Add main app with dependency")
            app_git.create_tag("apps/main-app/1.0.0")
            app_git.remote().push()
            app_git.remote().push(tags=True)

        with allure.step("When loading the app package"):
            from miniature.load import load_pkg

            gitdbs_config = [
                {
                    "db-repo": f"file://{app_repo}/",
                    "local_path": str(temp_dir / "cache" / "app"),
                },
                {
                    "db-repo": f"file://{base_repo}/",
                    "local_path": str(temp_dir / "cache" / "base-lib"),
                },
            ]
            gitdbs_file = temp_dir / ".miniature" / "gitdbs.json"
            gitdbs_file.parent.mkdir(exist_ok=True)
            gitdbs_file.write_text(json.dumps(gitdbs_config))

            result = load_pkg(
                repo=f"file://{app_repo}/",
                path="apps/main-app",
                version="1.0.0",
                target_dir=str(temp_dir / "project" / "main-app"),
                gitdbs_config=str(gitdbs_file),
            )

        with allure.step("Then the app should be loaded"):
            assert result["success"] is True
            assert (temp_dir / "project" / "main-app" / "app.py").exists()

        with allure.step("And dependency information should be available"):
            pkg_json = json.loads(
                (temp_dir / "project" / "main-app" / "pkg.json").read_text()
            )
            assert "dependencies" in pkg_json
            assert len(pkg_json["dependencies"]) == 1
            assert pkg_json["dependencies"][0]["pkgName"] == "base-lib"
