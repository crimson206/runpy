"""Minimal unit test to verify the Click invoke issue."""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

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
    result = runner.invoke(cli.app, ['database', 'user', 'list'])
    
    # Verify
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Users: Alice, Bob" in result.output


if __name__ == '__main__':
    # Prevent Click from parsing sys.argv when running directly
    original_argv = sys.argv
    sys.argv = [sys.argv[0]]
    
    try:
        test_nested_group_invoke()
        print("Test passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    finally:
        sys.argv = original_argv