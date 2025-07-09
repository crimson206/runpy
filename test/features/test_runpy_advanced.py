import allure
import pytest
from click.testing import CliRunner


@allure.feature("Runpy Advanced Features")
class TestRunpyAdvanced:
    """BDD tests for advanced Runpy functionality"""

    @allure.story("FastAPI-style parsing")
    @allure.title(
        "Given FastAPI-like docstrings, When parsing, Then extracts parameter descriptions"
    )
    def test_fastapi_style_parsing(self):
        with allure.step("Given function with FastAPI-style documentation"):

            def create_item(name: str, price: float, is_offer: bool = False) -> dict:
                """
                Create a new item in the catalog

                Args:
                    name: The name of the item
                    price: Price in USD
                    is_offer: Whether this item is on special offer
                """
                return {"name": name, "price": price, "is_offer": is_offer}

        with allure.step("When I register and check help"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(create_item)
            runner = CliRunner()

            result = runner.invoke(cli.app, ["create-item", "--help"])

        with allure.step("Then parameter descriptions are shown"):
            assert result.exit_code == 0
            assert "The name of the item" in result.output
            assert "Price in USD" in result.output
            assert "Whether this item is on special offer" in result.output

    @allure.story("Return value handling")
    @allure.title(
        "Given functions with return values, When executed, Then displays formatted output"
    )
    def test_return_value_handling(self):
        with allure.step("Given functions returning different types"):

            def get_dict() -> dict:
                """Return a dictionary"""
                return {"status": "ok", "count": 42}

            def get_list() -> list:
                """Return a list"""
                return ["apple", "banana", "cherry"]

            def get_string() -> str:
                """Return a string"""
                return "Hello, World!"

            def get_number() -> int:
                """Return a number"""
                return 42

        with allure.step("When I execute each function"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(get_dict)
            cli.register(get_list)
            cli.register(get_string)
            cli.register(get_number)

            runner = CliRunner()

        with allure.step("Then output is properly formatted"):
            # Dictionary output (JSON format)
            result = runner.invoke(cli.app, ["get-dict"])
            assert result.exit_code == 0
            assert '"status": "ok"' in result.output
            assert '"count": 42' in result.output

            # List output (test with underscore preserved)
            cli2 = Runpy(transform_underscore_to_dash=False)
            cli2.register(get_list)
            result = runner.invoke(cli2.app, ["get_list"])
            assert result.exit_code == 0
            assert "apple" in result.output
            assert "banana" in result.output

            # String output
            result = runner.invoke(cli.app, ["get-string"])
            assert result.exit_code == 0
            assert "Hello, World!" in result.output

            # Number output
            result = runner.invoke(cli.app, ["get-number"])
            assert result.exit_code == 0
            assert "42" in result.output

    @allure.story("Error handling")
    @allure.title(
        "Given function that raises exceptions, When error occurs, Then shows friendly message"
    )
    def test_error_handling(self):
        with allure.step("Given function that can raise exceptions"):

            def divide(a: float, b: float) -> float:
                """Divide two numbers"""
                if b == 0:
                    raise ValueError("Cannot divide by zero")
                return a / b

        with allure.step("When I trigger an error"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(divide)
            runner = CliRunner()

            result = runner.invoke(cli.app, ["divide", "--a", "10", "--b", "0"])

        with allure.step("Then error is handled gracefully"):
            assert result.exit_code != 0
            # Check either in output or exception
            assert "Cannot divide by zero" in result.output or (
                result.exception and "Cannot divide by zero" in str(result.exception)
            )

    @allure.story("Module and package registration")
    @allure.title(
        "Given a module with functions, When registering module, Then all functions available"
    )
    def test_module_registration(self):
        with allure.step("Given a module with multiple functions"):
            # Simulate a module
            class MathModule:
                @staticmethod
                def add(a: int, b: int) -> int:
                    """Add two numbers"""
                    return a + b

                @staticmethod
                def multiply(a: int, b: int) -> int:
                    """Multiply two numbers"""
                    return a * b

                @staticmethod
                def _private_func():
                    """This should not be registered"""
                    pass

        with allure.step("When I register the entire module"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register_module(MathModule, prefix="math")
            runner = CliRunner()

        with allure.step("Then public functions are available"):
            # Test add function
            result = runner.invoke(cli.app, ["math_add", "--a", "5", "--b", "3"])
            assert result.exit_code == 0
            assert "8" in result.output

            # Test multiply function
            result = runner.invoke(cli.app, ["math_multiply", "--a", "4", "--b", "7"])
            assert result.exit_code == 0
            assert "28" in result.output

            # Private function should not be available
            result = runner.invoke(cli.app, ["math__private_func"])
            assert result.exit_code != 0

    @allure.story("Configuration file support")
    @allure.title(
        "Given config file with defaults, When running commands, Then uses config values"
    )
    def test_configuration_file_support(self):
        with allure.step("Given a configuration file"):
            import tempfile
            import json

            config = {
                "defaults": {"environment": "production", "timeout": 30},
                "shortcuts": {"environment": "e", "timeout": "t"},
            }

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(config, f)
                config_file = f.name

        with allure.step("When I create CLI with config"):

            def deploy(
                service: str, environment: str = "dev", timeout: int = 10
            ) -> str:
                """Deploy a service"""
                return f"Deploying {service} to {environment} (timeout: {timeout}s)"

            from runpycli import Runpy

            cli = Runpy(config_file=config_file)
            cli.register(deploy)
            runner = CliRunner()

        with allure.step("Then config defaults are used"):
            # Without specifying environment, should use config default
            result = runner.invoke(cli.app, ["deploy", "--service", "api"])
            assert result.exit_code == 0
            assert "Deploying api to production" in result.output
            assert "timeout: 30s" in result.output

            # Shortcuts from config should work
            result = runner.invoke(
                cli.app, ["deploy", "--service", "web", "-e", "staging"]
            )
            assert result.exit_code == 0
            assert "Deploying web to staging" in result.output

        # Cleanup
        import os

        os.unlink(config_file)
