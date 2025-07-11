"""Test to demonstrate Optional parameter bug in runpycli"""

import sys
import os
from typing import Optional

# Add the src directory to the path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from runpycli import Runpy
from click.testing import CliRunner


def test_optional_parameters_bug():
    """Demonstrate that Optional[T] = None is incorrectly treated as required"""
    
    # Test 1: Optional[str] = None
    def func_str(arg1: Optional[str] = None) -> str:
        return f"arg1={arg1}"
    
    # Test 2: Optional[int] = None
    def func_int(arg2: Optional[int] = None) -> str:
        return f"arg2={arg2}"
    
    # Test 3: Optional[bool] = False (not None)
    def func_bool(arg3: Optional[bool] = False) -> str:
        return f"arg3={arg3}"
    
    # Test 4: str = None (not Optional, but has None default)
    def func_plain_none(arg4: str = None) -> str:
        return f"arg4={arg4}"
    
    cli = Runpy("testcli")
    cli.register(func_str, name="test-str")
    cli.register(func_int, name="test-int")
    cli.register(func_bool, name="test-bool")
    cli.register(func_plain_none, name="test-plain")
    
    runner = CliRunner()
    
    print("\n=== Testing Optional Parameters ===\n")
    
    # Test each function without arguments
    tests = [
        ("test-str", "Optional[str] = None"),
        ("test-int", "Optional[int] = None"),
        ("test-bool", "Optional[bool] = False"),
        ("test-plain", "str = None"),
    ]
    
    for cmd_name, description in tests:
        result = runner.invoke(cli.app, [cmd_name])
        status = "✓ PASS" if result.exit_code == 0 else "✗ FAIL"
        print(f"{status} {description:30} exit_code={result.exit_code}")
        if result.exit_code != 0:
            print(f"     Error: {result.output.strip()}")
        else:
            print(f"     Output: {result.output.strip()}")
        print()
    
    # Show the help for one of the failing commands
    print("\n=== Help output for test-int ===")
    help_result = runner.invoke(cli.app, ["test-int", "--help"])
    print(help_result.output)
    
    # Analysis
    print("\n=== Analysis ===")
    print("The issue is in core.py line 265:")
    print("    is_required = default is None and param_info['kind'] != 'VAR_POSITIONAL'")
    print("\nThis makes any parameter with default=None required, even if it's Optional[T].")
    print("The code should check if the type annotation includes Optional/Union with None.")


if __name__ == "__main__":
    test_optional_parameters_bug()