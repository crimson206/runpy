import allure
import pytest
from click.testing import CliRunner


@allure.feature("Runpy Basic Function Conversion")
class TestRunpyBasicConversion:
    """BDD tests for basic function to CLI conversion"""

    @allure.story("Convert simple function to CLI command")
    @allure.title(
        "Given a simple function, When registered, Then it becomes a CLI command"
    )
    def test_simple_function_conversion(self):
        with allure.step("Given a simple add function with type hints"):

            def add(a: int, b: int) -> int:
                """Add two numbers together"""
                return a + b

        with allure.step("When I register the function with Runpy"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(add)
            runner = CliRunner()

        with allure.step("Then I can call it as a CLI command"):
            result = runner.invoke(cli.app, ["add", "--a", "5", "--b", "3"])

            assert result.exit_code == 0
            assert "8" in result.output

    @allure.story("Function with optional parameters")
    @allure.title(
        "Given a function with defaults, When called without all args, Then uses defaults"
    )
    def test_function_with_defaults(self):
        with allure.step("Given a function with optional parameters"):

            def greet(name: str, greeting: str = "Hello") -> str:
                """Greet someone with a custom message"""
                return f"{greeting}, {name}!"

        with allure.step("When I register and call with partial arguments"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(greet)
            runner = CliRunner()

            result = runner.invoke(cli.app, ["greet", "--name", "Alice"])

        with allure.step("Then it uses the default value"):
            assert result.exit_code == 0
            assert "Hello, Alice!" in result.output

    @allure.story("Function with variable arguments")
    @allure.title(
        "Given a function with *args, When called with multiple values, Then processes all"
    )
    def test_function_with_varargs(self):
        with allure.step("Given a function with *args"):

            def sum_all(initial: int, *numbers: int) -> int:
                """Sum all provided numbers"""
                return initial + sum(numbers)

        with allure.step("When I register and call with multiple arguments"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(sum_all)
            runner = CliRunner()

            result = runner.invoke(
                cli.app, ["sum-all", "--initial", "10", "5", "3", "2"]
            )

        with allure.step("Then all arguments are processed"):
            assert result.exit_code == 0
            assert "20" in result.output

    @allure.story("Custom shortcuts for parameters")
    @allure.title(
        "Given shortcuts config, When calling with shortcuts, Then maps correctly"
    )
    def test_parameter_shortcuts(self):
        with allure.step("Given a function and shortcut configuration"):

            def deploy(name: str, version: str, force: bool = False) -> str:
                """Deploy an application"""
                return f"Deploying {name} v{version} (force={force})"

        with allure.step("When I register with shortcuts"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(deploy, shortcuts={"name": "n", "version": "v", "force": "f"})
            runner = CliRunner()

        with allure.step("Then I can use shortcuts"):
            result = runner.invoke(
                cli.app, ["deploy", "-n", "myapp", "-v", "1.0.0", "-f"]
            )

            assert result.exit_code == 0
            assert "Deploying myapp v1.0.0 (force=True)" in result.output

    @allure.story("Type validation")
    @allure.title(
        "Given typed parameters, When called with wrong types, Then shows error"
    )
    def test_type_validation(self):
        with allure.step("Given a function with strict types"):

            def calculate(x: int, y: float) -> float:
                """Perform calculation"""
                return x * y

        with allure.step("When I call with invalid types"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(calculate)
            runner = CliRunner()

            result = runner.invoke(
                cli.app, ["calculate", "--x", "not_a_number", "--y", "2.5"]
            )

        with allure.step("Then it shows a type error"):
            assert result.exit_code != 0
            assert "Invalid value" in result.output or "type" in result.output.lower()

    @allure.story("Command name transformation")
    @allure.title(
        "Given underscore function names, When dash transformation is enabled/disabled, Then commands match setting"
    )
    def test_command_name_transformation(self):
        with allure.step("Given a function with underscores in name"):

            def get_user_info(user_id: int) -> str:
                """Get information about a user"""
                return f"User {user_id} info"

        with allure.step("When dash transformation is enabled (default)"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(get_user_info)
            runner = CliRunner()

            # Should work with dashes
            result = runner.invoke(cli.app, ["get-user-info", "--user-id", "123"])
            assert result.exit_code == 0
            assert "User 123 info" in result.output

            # Should NOT work with underscores
            result = runner.invoke(cli.app, ["get_user_info", "--user-id", "123"])
            assert result.exit_code != 0
            assert "No such command" in result.output
            # Check for helpful error message
            assert (
                "get-user-info" in result.output
                or "dash" in result.output.lower()
                or "underscore" in result.output.lower()
            )

        with allure.step("When dash transformation is disabled"):
            cli2 = Runpy(transform_underscore_to_dash=False)
            cli2.register(get_user_info)
            runner2 = CliRunner()

            # Should work with underscores
            result = runner2.invoke(cli2.app, ["get_user_info", "--user_id", "123"])
            assert result.exit_code == 0
            assert "User 123 info" in result.output

            # Should NOT work with dashes
            result = runner2.invoke(cli2.app, ["get-user-info", "--user_id", "123"])
            assert result.exit_code != 0
            assert "No such command" in result.output
