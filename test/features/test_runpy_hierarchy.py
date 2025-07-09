import allure
import pytest
from click.testing import CliRunner


@allure.feature("Runpy Hierarchical Commands")
class TestRunpyHierarchy:
    """BDD tests for hierarchical command structures"""

    @allure.story("Single-level subcommands")
    @allure.title(
        "Given command groups, When accessing subcommands, Then executes correctly"
    )
    def test_single_level_hierarchy(self):
        with allure.step("Given functions organized in groups"):

            def user_create(name: str, email: str) -> str:
                """Create a new user"""
                return f"Created user: {name} ({email})"

            def user_delete(user_id: int) -> str:
                """Delete a user"""
                return f"Deleted user with ID: {user_id}"

        with allure.step("When I create a hierarchical CLI"):
            from runpycli import Runpy

            cli = Runpy("myapp")
            user_group = cli.group("user")
            user_group.register(user_create, name="create")
            user_group.register(user_delete, name="delete")

            runner = CliRunner()

        with allure.step("Then I can call subcommands"):
            # Test create subcommand
            result = runner.invoke(
                cli.app,
                ["user", "create", "--name", "John", "--email", "john@example.com"],
            )
            assert result.exit_code == 0
            assert "Created user: John (john@example.com)" in result.output

            # Test delete subcommand
            result = runner.invoke(cli.app, ["user", "delete", "--user-id", "123"])
            assert result.exit_code == 0
            assert "Deleted user with ID: 123" in result.output

    @allure.story("Multi-level subcommands")
    @allure.title(
        "Given nested command groups, When accessing deep commands, Then navigates correctly"
    )
    def test_multi_level_hierarchy(self):
        with allure.step("Given deeply nested functions"):

            def db_user_list() -> str:
                """List all database users"""
                return "Listing database users..."

            def db_user_grant(username: str, permission: str) -> str:
                """Grant permission to database user"""
                return f"Granted {permission} to {username}"

            def db_backup_create(name: str) -> str:
                """Create database backup"""
                return f"Created backup: {name}"

        with allure.step("When I create multi-level hierarchy"):
            from runpycli import Runpy

            cli = Runpy("myapp")
            db_group = cli.group("database")
            db_user_group = db_group.group("user")
            db_backup_group = db_group.group("backup")

            db_user_group.register(db_user_list, name="list")
            db_user_group.register(db_user_grant, name="grant")
            db_backup_group.register(db_backup_create, name="create")

            runner = CliRunner()

        with allure.step("Then I can navigate deep command paths"):
            # Test database user list
            result = runner.invoke(cli.app, ["database", "user", "list"])
            assert result.exit_code == 0
            assert "Listing database users" in result.output

            # Test database user grant
            result = runner.invoke(
                cli.app,
                [
                    "database",
                    "user",
                    "grant",
                    "--username",
                    "admin",
                    "--permission",
                    "SELECT",
                ],
            )
            assert result.exit_code == 0
            assert "Granted SELECT to admin" in result.output

            # Test database backup create
            result = runner.invoke(
                cli.app, ["database", "backup", "create", "--name", "daily-backup"]
            )
            assert result.exit_code == 0
            assert "Created backup: daily-backup" in result.output

    @allure.story("Command path configuration")
    @allure.title(
        "Given path configuration, When initializing CLI, Then creates proper structure"
    )
    def test_command_path_initialization(self):
        with allure.step("Given a command path specification"):

            def status() -> str:
                """Check service status"""
                return "Service is running"

        with allure.step("When I initialize with path"):
            from runpycli import Runpy

            # Create nested structure: mycli/service/health/status
            cli = Runpy("mycli/service/health")
            cli.register(status)

            runner = CliRunner()

        with allure.step("Then the command is accessible at the path"):
            result = runner.invoke(cli.app, ["service", "health", "status"])
            assert result.exit_code == 0
            assert "Service is running" in result.output

    @allure.story("Mixed hierarchy levels")
    @allure.title(
        "Given mixed depth commands, When calling at different levels, Then all work"
    )
    def test_mixed_hierarchy_levels(self):
        with allure.step("Given functions at different hierarchy levels"):

            def root_version() -> str:
                """Show version"""
                return "Version 1.0.0"

            def config_show() -> str:
                """Show configuration"""
                return "Current configuration..."

            def config_env_list() -> str:
                """List environments"""
                return "dev, staging, prod"

        with allure.step("When I register at different levels"):
            from runpycli import Runpy

            cli = Runpy("mycli")
            cli.register(root_version, name="version")

            config_group = cli.group("config")
            config_group.register(config_show, name="show")

            env_group = config_group.group("env")
            env_group.register(config_env_list, name="list")

            runner = CliRunner()

        with allure.step("Then all levels are accessible"):
            # Root level command
            result = runner.invoke(cli.app, ["version"])
            assert result.exit_code == 0
            assert "Version 1.0.0" in result.output

            # First level subcommand
            result = runner.invoke(cli.app, ["config", "show"])
            assert result.exit_code == 0
            assert "Current configuration" in result.output

            # Second level subcommand
            result = runner.invoke(cli.app, ["config", "env", "list"])
            assert result.exit_code == 0
            assert "dev, staging, prod" in result.output
