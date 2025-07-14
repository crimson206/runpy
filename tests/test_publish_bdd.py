"""BDD tests for miniature publish functionality using Allure."""

import pytest
import allure
import json
from pathlib import Path
from git import Repo

from miniature.publish import publish_pkg


@allure.feature("Package Publishing")
@allure.story("Publish package to git repository")
class TestPublishPackage:
    """BDD tests for publishing packages to git repositories."""

    @allure.title("Publish package with automatic tagging")
    @allure.description(
        """
        Given a package directory with pkg.json
        And a local git repository configured in gitdbs
        When publishing the package with tag=True
        Then the package should be committed and tagged in the repository
    """
    )
    def test_publish_package_with_tag(self, temp_dir, gitdbs_config):
        """Test publishing a package with automatic version tagging."""
        with allure.step("Given a package directory with pkg.json"):
            # Create package directory
            pkg_dir = temp_dir / "my-package"
            pkg_dir.mkdir()

            # Create pkg.json
            pkg_data = {
                "name": "my-package",
                "version": "1.2.3",
                "description": "Test package for publishing",
                "db-repo": "https://github.com/test/repo",
                "root-dir": "packages/my-package",
                "branch": "main",
            }
            (pkg_dir / "pkg.json").write_text(json.dumps(pkg_data, indent=2))

            # Create package content
            (pkg_dir / "index.py").write_text(
                'def main():\n    print("Hello from my-package")'
            )

        with allure.step("And a local git repository"):
            # Set up local repository matching gitdbs config
            local_repo_path = Path(temp_dir) / "local-repos" / "test-repo"
            local_repo_path.mkdir(parents=True)
            repo = Repo.init(str(local_repo_path))

            # Create initial structure
            packages_dir = local_repo_path / "packages" / "my-package"
            packages_dir.mkdir(parents=True)
            (packages_dir / ".gitkeep").touch()
            repo.index.add([str(packages_dir / ".gitkeep")])
            repo.index.commit("Initial commit")

        with allure.step("When publishing the package with tagging"):
            result = publish_pkg(
                pkg_dir=str(pkg_dir),
                push=False,  # Don't push in tests
                tag=True,
                gitdbs_config=gitdbs_config,
            )

        with allure.step("Then the package should be published successfully"):
            assert result["success"] is True
            assert "tag_result" in result
            assert result["tag_result"]["tag_name"] == "packages/my-package/1.2.3"

        with allure.step("And the files should be committed to the repository"):
            # Check files exist in repo
            assert (packages_dir / "pkg.json").exists()
            assert (packages_dir / "index.py").exists()

            # Check git status
            assert len(list(repo.iter_commits())) > 1  # More than initial commit

        with allure.step("And the version tag should exist"):
            tags = [tag.name for tag in repo.tags]
            assert "packages/my-package/1.2.3" in tags

    @allure.title("Publish package without tagging")
    @allure.description(
        """
        Given a package directory with pkg.json
        When publishing the package with tag=False
        Then the package should be committed without creating a tag
    """
    )
    def test_publish_package_without_tag(self, temp_dir, gitdbs_config):
        """Test publishing without creating a version tag."""
        with allure.step("Given a package directory"):
            pkg_dir = temp_dir / "no-tag-package"
            pkg_dir.mkdir()

            pkg_data = {
                "name": "no-tag-package",
                "version": "0.1.0",
                "db-repo": "https://github.com/test/repo",
                "root-dir": "packages/no-tag-package",
            }
            (pkg_dir / "pkg.json").write_text(json.dumps(pkg_data, indent=2))
            (pkg_dir / "README.md").write_text("# No Tag Package")

        with allure.step("And a local git repository"):
            local_repo_path = Path(temp_dir) / "local-repos" / "test-repo"
            local_repo_path.mkdir(parents=True)
            repo = Repo.init(str(local_repo_path))

            packages_dir = local_repo_path / "packages" / "no-tag-package"
            packages_dir.mkdir(parents=True)
            (packages_dir / ".gitkeep").touch()
            repo.index.add([str(packages_dir / ".gitkeep")])
            repo.index.commit("Initial commit")

        with allure.step("When publishing without tagging"):
            result = publish_pkg(
                pkg_dir=str(pkg_dir), push=False, tag=False, gitdbs_config=gitdbs_config
            )

        with allure.step("Then the package should be committed"):
            assert result["success"] is True
            assert (packages_dir / "pkg.json").exists()
            assert (packages_dir / "README.md").exists()

        with allure.step("But no tag should be created"):
            assert "tag_result" not in result or result["tag_result"] is None
            tags = [tag.name for tag in repo.tags]
            assert "packages/no-tag-package/0.1.0" not in tags

    @allure.title("Force overwrite existing tag")
    @allure.description(
        """
        Given a package that has already been published with a tag
        When publishing the same version with force_tag=True
        Then the existing tag should be overwritten
    """
    )
    def test_publish_force_tag_overwrite(self, temp_dir, gitdbs_config):
        """Test force overwriting an existing tag."""
        with allure.step("Given a package directory"):
            pkg_dir = temp_dir / "force-tag-package"
            pkg_dir.mkdir()

            pkg_data = {
                "name": "force-tag-package",
                "version": "2.0.0",
                "db-repo": "https://github.com/test/repo",
                "root-dir": "packages/force-tag-package",
            }
            (pkg_dir / "pkg.json").write_text(json.dumps(pkg_data, indent=2))
            (pkg_dir / "version1.txt").write_text("Version 1")

        with allure.step("And a repository with existing tag"):
            local_repo_path = Path(temp_dir) / "local-repos" / "test-repo"
            local_repo_path.mkdir(parents=True)
            repo = Repo.init(str(local_repo_path))

            packages_dir = local_repo_path / "packages" / "force-tag-package"
            packages_dir.mkdir(parents=True)
            (packages_dir / ".gitkeep").touch()
            repo.index.add([str(packages_dir / ".gitkeep")])
            repo.index.commit("Initial commit")

            # Create existing tag
            repo.create_tag("packages/force-tag-package/2.0.0", message="Initial tag")

        with allure.step("When publishing with updated content and force_tag=True"):
            # Update package content
            (pkg_dir / "version2.txt").write_text("Version 2")

            result = publish_pkg(
                pkg_dir=str(pkg_dir),
                push=False,
                tag=True,
                force_tag=True,
                gitdbs_config=gitdbs_config,
            )

        with allure.step("Then the tag should be updated"):
            assert result["success"] is True
            assert result["tag_result"]["action"] == "updated"

        with allure.step("And new content should be included"):
            assert (packages_dir / "version1.txt").exists()
            assert (packages_dir / "version2.txt").exists()


@allure.feature("Package Publishing")
@allure.story("Handle publishing errors")
class TestPublishingErrors:
    """BDD tests for error handling in package publishing."""

    @allure.title("Handle missing pkg.json file")
    @allure.description(
        """
        Given a package directory without pkg.json
        When trying to publish the package
        Then an appropriate error should be returned
    """
    )
    def test_publish_without_pkg_json(self, temp_dir, gitdbs_config):
        """Test publishing without pkg.json file."""
        with allure.step("Given a directory without pkg.json"):
            pkg_dir = temp_dir / "no-pkg-json"
            pkg_dir.mkdir()
            (pkg_dir / "some-file.txt").write_text("Some content")

        with allure.step("When trying to publish"):
            result = publish_pkg(pkg_dir=str(pkg_dir), gitdbs_config=gitdbs_config)

        with allure.step("Then the operation should fail"):
            assert result["success"] is False
            assert "pkg.json" in result["message"].lower()

    @allure.title("Handle repository not found in gitdbs")
    @allure.description(
        """
        Given a package with db-repo not in gitdbs config
        When trying to publish the package
        Then an appropriate error should be returned
    """
    )
    def test_publish_repo_not_in_gitdbs(self, temp_dir):
        """Test publishing when repository is not in gitdbs."""
        with allure.step("Given a package with unknown db-repo"):
            pkg_dir = temp_dir / "unknown-repo-package"
            pkg_dir.mkdir()

            pkg_data = {
                "name": "unknown-repo-package",
                "version": "1.0.0",
                "db-repo": "https://github.com/unknown/repo",
                "root-dir": "packages/unknown",
            }
            (pkg_dir / "pkg.json").write_text(json.dumps(pkg_data, indent=2))

        with allure.step("And gitdbs config without that repo"):
            gitdbs_file = temp_dir / ".miniature" / "gitdbs.json"
            gitdbs_file.parent.mkdir()
            gitdbs_file.write_text(
                json.dumps(
                    [
                        {
                            "name": "different-repo",
                            "db-repo": "https://github.com/different/repo",
                            "local_path": str(temp_dir / "different-repo"),
                        }
                    ]
                )
            )

        with allure.step("When trying to publish"):
            result = publish_pkg(pkg_dir=str(pkg_dir), gitdbs_config=str(gitdbs_file))

        with allure.step("Then the operation should fail"):
            assert result["success"] is False
            assert (
                "not found" in result["message"].lower()
                or "repository" in result["message"].lower()
            )


@allure.feature("Package Publishing")
@allure.story("Custom commit messages")
class TestCustomCommitMessages:
    """BDD tests for publishing with custom commit messages."""

    @allure.title("Publish with custom commit message")
    @allure.description(
        """
        Given a package to publish
        When publishing with a custom commit message
        Then the commit should use the provided message
    """
    )
    def test_publish_with_custom_message(self, temp_dir, gitdbs_config):
        """Test publishing with custom commit message."""
        with allure.step("Given a package directory"):
            pkg_dir = temp_dir / "custom-message-package"
            pkg_dir.mkdir()

            pkg_data = {
                "name": "custom-message-package",
                "version": "1.0.0",
                "db-repo": "https://github.com/test/repo",
                "root-dir": "packages/custom-message",
            }
            (pkg_dir / "pkg.json").write_text(json.dumps(pkg_data, indent=2))

        with allure.step("And a local repository"):
            local_repo_path = Path(temp_dir) / "local-repos" / "test-repo"
            local_repo_path.mkdir(parents=True)
            repo = Repo.init(str(local_repo_path))

            packages_dir = local_repo_path / "packages" / "custom-message"
            packages_dir.mkdir(parents=True)
            (packages_dir / ".gitkeep").touch()
            repo.index.add([str(packages_dir / ".gitkeep")])
            repo.index.commit("Initial commit")

        with allure.step("When publishing with custom message"):
            custom_message = "feat: Add awesome new feature"
            result = publish_pkg(
                pkg_dir=str(pkg_dir),
                commit_message=custom_message,
                push=False,
                gitdbs_config=gitdbs_config,
            )

        with allure.step("Then the commit should use the custom message"):
            assert result["success"] is True
            assert result["commit_message"] == custom_message

            # Check actual commit message
            latest_commit = list(repo.iter_commits())[0]
            assert latest_commit.message.strip() == custom_message
