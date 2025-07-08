import allure
import pytest
from click.testing import CliRunner


@allure.feature("Runpy Documentation Commands")
class TestRunpyDocsCommand:
    """BDD tests for documentation viewing commands"""

    @allure.story("View all command summaries")
    @allure.title("Given nested commands, When calling docs, Then shows all summaries in hierarchy")
    def test_docs_show_all_summaries(self):
        with allure.step("Given a complex nested command structure"):
            def user_create(name: str, email: str) -> str:
                """Create a new user account
                
                This function creates a new user with the provided
                name and email address. It validates the email format
                and checks for duplicates.
                """
                pass
            
            def user_delete(user_id: int) -> str:
                """Delete an existing user
                
                Permanently removes a user from the system.
                This action cannot be undone.
                """
                pass
            
            def user_list(active: bool = True) -> str:
                """List all users in the system
                
                Returns a formatted list of users with their
                basic information and status.
                """
                pass
            
            def db_backup(name: str = None) -> str:
                """Create a database backup
                
                Creates a full backup of the database including
                all tables, indexes, and stored procedures.
                """
                pass
            
            def db_restore(backup_file: str) -> str:
                """Restore database from backup
                
                Restores the database to a previous state using
                a backup file. All current data will be replaced.
                """
                pass
            
            def config_get(key: str) -> str:
                """Retrieve a configuration value
                
                Gets the current value of a configuration key
                from the application settings.
                """
                pass

        with allure.step("When I call the docs command"):
            from runpycli import Runpy
            
            cli = Runpy("myapp")
            
            # Create user group
            user_group = cli.group("user")
            user_group.register(user_create, name="create")
            user_group.register(user_delete, name="delete")
            user_group.register(user_list, name="list")
            
            # Create database group
            db_group = cli.group("database")
            db_group.register(db_backup, name="backup")
            db_group.register(db_restore, name="restore")
            
            # Register root level command
            cli.register(config_get, name="config-get")
            
            runner = CliRunner()
            result = runner.invoke(cli.app, ['docs'])

        with allure.step("Then it displays all summaries in tree structure"):
            assert result.exit_code == 0
            
            # Check tree structure
            assert "myapp" in result.output
            assert "├── config-get" in result.output
            assert "│   └── Retrieve a configuration value" in result.output
            assert "├── user" in result.output
            assert "│   ├── create" in result.output
            assert "│   │   └── Create a new user account" in result.output
            assert "│   ├── delete" in result.output
            assert "│   │   └── Delete an existing user" in result.output
            assert "│   └── list" in result.output
            assert "│       └── List all users in the system" in result.output
            assert "└── database" in result.output
            assert "    ├── backup" in result.output
            assert "    │   └── Create a database backup" in result.output
            assert "    └── restore" in result.output
            assert "        └── Restore database from backup" in result.output

    @allure.story("View specific command descriptions")
    @allure.title("Given multiple command paths, When calling docs with args, Then shows their help")
    def test_docs_with_specific_commands(self):
        with allure.step("Given commands with detailed documentation"):
            def deploy(service: str, version: str = "latest", env: str = "staging") -> str:
                """Deploy a service to environment
                
                This command deploys the specified service version to the target
                environment. It performs health checks and rollback on failure.
                
                The deployment process includes:
                - Building the service image
                - Running pre-deployment tests
                - Updating the service configuration
                - Performing rolling update
                - Running post-deployment validation
                """
                pass
            
            def rollback(service: str, steps: int = 1) -> str:
                """Rollback a service to previous version
                
                Reverts the service to a previous deployment state.
                Can rollback multiple steps if specified.
                
                Safety features:
                - Automatic backup before rollback
                - Health check validation
                - Rollback prevention if issues detected
                """
                pass
            
            def status(service: str = None, detailed: bool = False) -> str:
                """Check service deployment status
                
                Shows current deployment status and health metrics
                for one or all services.
                """
                pass

        with allure.step("When I request help for specific commands"):
            from runpycli import Runpy
            
            cli = Runpy("ops")
            deploy_group = cli.group("deploy")
            deploy_group.register(deploy, name="service")
            deploy_group.register(rollback, name="rollback")
            deploy_group.register(status, name="status")
            
            runner = CliRunner()
            
            # Request help for multiple specific commands
            result = runner.invoke(cli.app, [
                'docs',
                'deploy/service',
                'deploy/rollback'
            ])

        with allure.step("Then it shows detailed help for each requested command"):
            assert result.exit_code == 0
            
            # First command help
            assert "deploy service" in result.output
            assert "Deploy a service to environment" in result.output
            assert "--service" in result.output
            assert "--version" in result.output
            assert "--env" in result.output
            
            # Separator between commands
            assert "─" * 40 in result.output or "=" * 40 in result.output
            
            # Second command help
            assert "deploy rollback" in result.output
            assert "Rollback a service to previous version" in result.output
            assert "--steps" in result.output

    @allure.story("Filter documentation by pattern")
    @allure.title("Given pattern argument, When calling docs, Then shows matching commands")
    def test_docs_with_filter_pattern(self):
        with allure.step("Given various commands"):
            def user_create() -> str:
                """Create a new user"""
                pass
            
            def user_update() -> str:
                """Update user information"""
                pass
            
            def create_backup() -> str:
                """Create system backup"""
                pass
            
            def create_snapshot() -> str:
                """Create database snapshot"""
                pass
            
            def delete_user() -> str:
                """Delete a user"""
                pass

        with allure.step("When I filter docs by pattern"):
            from runpycli import Runpy
            
            cli = Runpy()
            cli.register(user_create)
            cli.register(user_update)
            cli.register(create_backup)
            cli.register(create_snapshot)
            cli.register(delete_user)
            
            runner = CliRunner()
            
            # Filter by "create" pattern
            result = runner.invoke(cli.app, ['docs', '--filter', 'create'])

        with allure.step("Then it shows only matching commands"):
            assert result.exit_code == 0
            
            # Should include commands with "create" in name
            assert "user-create" in result.output
            assert "Create a new user" in result.output
            assert "create-backup" in result.output
            assert "Create system backup" in result.output
            assert "create-snapshot" in result.output
            assert "Create database snapshot" in result.output
            
            # Should not include non-matching commands
            assert "user-update" not in result.output
            assert "delete-user" not in result.output


    # Test removed: export formats (--export option) no longer supported
    # The docs command now only outputs to stdout in a single format