import allure
import pytest
from click.testing import CliRunner
import json


@allure.feature("Runpy Schema Generation")
class TestRunpySchema:
    """BDD tests for automatic schema generation"""

    @allure.story("Basic schema command")
    @allure.title("Given registered functions, When calling schema, Then returns API-style docs")
    def test_basic_schema_generation(self):
        with allure.step("Given multiple registered functions"):
            def calculate(x: int, y: int, operation: str = "add") -> int:
                """Perform mathematical operations
                
                Args:
                    x: First number
                    y: Second number
                    operation: Operation to perform (add, subtract, multiply, divide)
                """
                pass
            
            def format_text(text: str, uppercase: bool = False) -> str:
                """Format text with various options"""
                pass

        with allure.step("When I request the schema"):
            from runpycli import Runpy
            
            cli = Runpy("calculator")
            cli.register(calculate)
            cli.register(format_text)
            
            runner = CliRunner()
            result = runner.invoke(cli.app, ['schema'])

        with allure.step("Then it returns structured API documentation"):
            assert result.exit_code == 0
            
            # Parse schema output as JSON
            schema = json.loads(result.output)
            
            # Check basic structure
            assert "commands" in schema
            assert "calculate" in schema["commands"]
            assert "format-text" in schema["commands"]
            
            # Check calculate command details
            calc_schema = schema["commands"]["calculate"]
            assert calc_schema["description"] == "Perform mathematical operations"
            assert "parameters" in calc_schema
            
            # Check parameters
            params = calc_schema["parameters"]
            assert params["x"]["type"] == "integer"
            assert params["x"]["required"] is True
            assert params["y"]["type"] == "integer"
            assert params["y"]["required"] is True
            assert params["operation"]["type"] == "string"
            assert params["operation"]["default"] == "add"
            assert params["operation"]["required"] is False

    @allure.story("Schema with shortcuts")
    @allure.title("Given functions with shortcuts, When generating schema, Then includes shortcut info")
    def test_schema_with_shortcuts(self):
        with allure.step("Given function with shortcuts"):
            def deploy(name: str, version: str, environment: str = "dev") -> str:
                """Deploy application to environment"""
                pass

        with allure.step("When I register with shortcuts and get schema"):
            from runpycli import Runpy
            
            cli = Runpy()
            cli.register(deploy, shortcuts={
                "name": "n",
                "version": "v",
                "environment": "e"
            })
            
            runner = CliRunner()
            result = runner.invoke(cli.app, ['schema'])

        with allure.step("Then schema includes shortcut information"):
            assert result.exit_code == 0
            schema = json.loads(result.output)
            
            deploy_params = schema["commands"]["deploy"]["parameters"]
            assert deploy_params["name"]["shortcut"] == "n"
            assert deploy_params["version"]["shortcut"] == "v"
            assert deploy_params["environment"]["shortcut"] == "e"

    @allure.story("Hierarchical schema")
    @allure.title("Given nested command structure, When requesting schema, Then shows full hierarchy")
    def test_hierarchical_schema(self):
        with allure.step("Given hierarchical command structure"):
            def user_create(name: str, role: str = "user") -> str:
                """Create a new user"""
                pass
            
            def user_list(active: bool = True) -> str:
                """List all users"""
                pass
            
            def db_backup(full: bool = False) -> str:
                """Create database backup"""
                pass

        with allure.step("When I create hierarchy and get schema"):
            from runpycli import Runpy
            
            cli = Runpy("admin")
            
            user_group = cli.group("user")
            user_group.register(user_create, name="create")
            user_group.register(user_list, name="list")
            
            db_group = cli.group("database")
            db_group.register(db_backup, name="backup")
            
            runner = CliRunner()
            result = runner.invoke(cli.app, ['schema'])

        with allure.step("Then schema reflects the hierarchy"):
            assert result.exit_code == 0
            schema = json.loads(result.output)
            
            assert "groups" in schema
            assert "user" in schema["groups"]
            assert "database" in schema["groups"]
            
            # Check user group commands
            user_commands = schema["groups"]["user"]["commands"]
            assert "create" in user_commands
            assert "list" in user_commands
            
            # Check database group commands
            db_commands = schema["groups"]["database"]["commands"]
            assert "backup" in db_commands

    @allure.story("Schema format options")
    @allure.title("Given schema request with format, When generating, Then returns requested format")
    def test_schema_format_options(self):
        with allure.step("Given a simple function"):
            def hello(name: str = "World") -> str:
                """Say hello to someone"""
                pass

        with allure.step("When I request schema in different formats"):
            from runpycli import Runpy
            
            cli = Runpy()
            cli.register(hello)
            runner = CliRunner()
            
            # Test JSON format (default)
            json_result = runner.invoke(cli.app, ['schema', '--format', 'json'])
            
            # Test YAML format
            yaml_result = runner.invoke(cli.app, ['schema', '--format', 'yaml'])
            
            # Test Markdown format
            md_result = runner.invoke(cli.app, ['schema', '--format', 'markdown'])

        with allure.step("Then each format is properly generated"):
            # JSON format
            assert json_result.exit_code == 0
            json_schema = json.loads(json_result.output)
            assert "commands" in json_schema
            
            # YAML format
            assert yaml_result.exit_code == 0
            assert "commands:" in yaml_result.output
            assert "hello:" in yaml_result.output
            
            # Markdown format
            assert md_result.exit_code == 0
            assert "# Commands" in md_result.output
            assert "## hello" in md_result.output
            assert "Say hello to someone" in md_result.output

    @allure.story("Schema with complex types")
    @allure.title("Given functions with complex types, When generating schema, Then handles properly")
    def test_schema_complex_types(self):
        with allure.step("Given functions with various type hints"):
            from typing import List, Dict, Optional, Union, Literal
            from pydantic import BaseModel, Field
            
            class ProcessConfig(BaseModel):
                """Processing configuration"""
                timeout: int = Field(30, ge=1, le=300, description="Timeout in seconds")
                retry_count: int = Field(3, ge=0, le=10, description="Number of retries")
                mode: Literal["fast", "normal", "thorough"] = Field("normal", description="Processing mode")
            
            class ProcessResult(BaseModel):
                """Processing result"""
                success: bool = Field(..., description="Whether processing succeeded")
                items_processed: int = Field(..., description="Number of items processed")
                errors: List[str] = Field(default_factory=list, description="List of errors")
                metadata: Dict[str, str] = Field(default_factory=dict, description="Additional metadata")
            
            def process_data(
                items: List[str],
                config: ProcessConfig,
                tags: Optional[List[str]] = None,
                priority: Literal["low", "normal", "high"] = "normal"
            ) -> ProcessResult:
                """Process data with complex parameters"""
                pass

        with allure.step("When I generate schema"):
            from runpycli import Runpy
            
            cli = Runpy()
            cli.register(process_data)
            
            runner = CliRunner()
            result = runner.invoke(cli.app, ['schema'])

        with allure.step("Then complex types are properly documented"):
            assert result.exit_code == 0
            schema = json.loads(result.output)
            
            params = schema["commands"]["process-data"]["parameters"]
            
            # List type
            assert params["items"]["type"] == "array" or params["items"]["type"] == "list"
            
            # BaseModel type
            assert params["config"]["type"] == "basemodel" or params["config"]["type"] == "object"
            
            # Optional List type
            assert params["tags"]["required"] is False
            
            # Literal type
            assert params["priority"]["type"] in ["literal", "choice", "enum", "string"]
            assert params["priority"]["default"] == "normal"
            
            # The schema should also include information about BaseModel schemas
            # (This might be in a separate "components" or "models" section)