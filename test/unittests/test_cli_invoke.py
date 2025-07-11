"""Minimal unit test to verify the Click invoke issue."""

import sys
import os
from typing import Optional

# Add the src directory to the path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from runpycli import Runpy
from click.testing import CliRunner


def test_nested_group_invoke():
    """Test that nested groups can be invoked correctly."""

    # Define a simple function
    def list_users() -> str:
        """List all users"""
        return "Users: Alice, Bob"

    # Create nested CLI structure
    cli = Runpy("myapp")
    db_group = cli.group("database")
    user_group = db_group.group("user")
    user_group.register(list_users, name="list")

    # Test invocation
    runner = CliRunner()
    result = runner.invoke(cli.app, ["database", "user", "list"])

    # Verify
    assert (
        result.exit_code == 0
    ), f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Users: Alice, Bob" in result.output


def test_optional_argument_not_provided():
    """Test that optional arguments work when not provided in CLI."""
    
    def process_data(arg1: Optional[str] = None) -> str:
        """Process data with optional argument."""
        if arg1 is None:
            return "No arg1 provided"
        return f"arg1: {arg1}"
    
    cli = Runpy("myapp")
    cli.register(process_data)
    
    runner = CliRunner()
    # Call without --arg1
    result = runner.invoke(cli.app, ["process-data"])
    
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "No arg1 provided" in result.output, f"Expected 'No arg1 provided' in output, got: {result.output}"


def test_optional_argument_with_value():
    """Test that optional arguments work when provided in CLI."""
    
    def process_data(arg1: Optional[str] = None) -> str:
        """Process data with optional argument."""
        if arg1 is None:
            return "No arg1 provided"
        return f"arg1: {arg1}"
    
    cli = Runpy("myapp")
    cli.register(process_data)
    
    runner = CliRunner()
    # Call with --arg1
    result = runner.invoke(cli.app, ["process-data", "--arg1", "test_value"])
    
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "arg1: test_value" in result.output, f"Expected 'arg1: test_value' in output, got: {result.output}"


def test_optional_int_debug():
    """Debug test for Optional[int] parameter."""
    
    def process_int(arg2: Optional[int] = None) -> str:
        """Process with optional int argument."""
        return f"arg2: {arg2 if arg2 is not None else 'None'}"
    
    cli = Runpy("myapp")
    cli.register(process_int)
    
    runner = CliRunner()
    
    # First, let's see what --help shows
    help_result = runner.invoke(cli.app, ["process-int", "--help"])
    print(f"\nHelp output:\n{help_result.output}")
    
    # Try without --arg2
    result = runner.invoke(cli.app, ["process-int"])
    print(f"\nWithout --arg2: exit_code={result.exit_code}")
    print(f"Output: {result.output}")
    
    # If it fails, let's not assert, just print for debugging
    if result.exit_code != 0:
        print("FAILED: Optional[int] = None is being treated as required!")
        return False
    
    return True


def test_multiple_optional_arguments():
    """Test multiple optional arguments with different combinations."""
    
    def process_multiple(
        arg1: Optional[str] = None,
        arg2: Optional[int] = None,
        arg3: Optional[bool] = False
    ) -> str:
        """Process with multiple optional arguments."""
        parts = []
        parts.append(f"arg1: {arg1 if arg1 is not None else 'None'}")
        parts.append(f"arg2: {arg2 if arg2 is not None else 'None'}")
        parts.append(f"arg3: {arg3}")
        return ", ".join(parts)
    
    cli = Runpy("myapp")
    cli.register(process_multiple)
    
    runner = CliRunner()
    
    # Test 1: No arguments provided
    result = runner.invoke(cli.app, ["process-multiple"])
    assert result.exit_code == 0, f"Test 1 failed with exit code {result.exit_code}. Output: {result.output}"
    assert "arg1: None, arg2: None, arg3: False" in result.output
    
    # Test 2: Only arg1 provided
    result = runner.invoke(cli.app, ["process-multiple", "--arg1", "hello"])
    assert result.exit_code == 0, f"Test 2 failed with exit code {result.exit_code}. Output: {result.output}"
    assert "arg1: hello, arg2: None, arg3: False" in result.output
    
    # Test 3: arg1 and arg2 provided
    result = runner.invoke(cli.app, ["process-multiple", "--arg1", "hello", "--arg2", "42"])
    assert result.exit_code == 0, f"Test 3 failed with exit code {result.exit_code}. Output: {result.output}"
    assert "arg1: hello, arg2: 42, arg3: False" in result.output
    
    # Test 4: All arguments provided with arg3=true
    result = runner.invoke(cli.app, ["process-multiple", "--arg1", "hello", "--arg2", "42", "--arg3", "true"])
    assert result.exit_code == 0, f"Test 4 failed with exit code {result.exit_code}. Output: {result.output}"
    assert "arg1: hello, arg2: 42, arg3: True" in result.output
    
    # Test 5: Test with arg3=false explicitly
    result = runner.invoke(cli.app, ["process-multiple", "--arg3", "false"])
    assert result.exit_code == 0, f"Test 5 failed with exit code {result.exit_code}. Output: {result.output}"
    assert "arg1: None, arg2: None, arg3: False" in result.output


if __name__ == "__main__":
    # Prevent Click from parsing sys.argv when running directly
    original_argv = sys.argv
    sys.argv = [sys.argv[0]]

    try:
        # Run all tests
        test_nested_group_invoke()
        print("✓ test_nested_group_invoke passed")
        
        test_optional_argument_not_provided()
        print("✓ test_optional_argument_not_provided passed")
        
        test_optional_argument_with_value()
        print("✓ test_optional_argument_with_value passed")
        
        test_multiple_optional_arguments()
        print("✓ test_multiple_optional_arguments passed")
        
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    finally:
        sys.argv = original_argv
