"""Debug test to understand the invoke chain."""

import sys
import os

# Prevent any Click app from auto-executing
original_argv = sys.argv[:]
sys.argv = [sys.argv[0]]

try:
    # Add the src directory to the path
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
    )

    from runpycli import Runpy
    from click.testing import CliRunner
    import click

    def test_debug_invoke():
        """Debug the invoke process."""

        # Create a simple function
        def list_users() -> str:
            return "User list"

        # Build the CLI
        cli = Runpy("myapp")
        db_group = cli.group("database")
        user_group = db_group.group("user")
        user_group.register(list_users, name="list")

        # Debug: Patch Click's Group.invoke to see what's happening
        original_invoke = click.Group.invoke
        call_count = 0

        def debug_invoke(self, ctx):
            nonlocal call_count
            call_count += 1
            print(f"\n[{call_count}] Group.invoke on '{self.name}'")
            print(f"  ctx.args: {ctx.args}")
            print(f"  ctx.protected_args: {ctx.protected_args}")
            print(f"  ctx.params: {ctx.params}")

            # Check if args look wrong
            if ctx.args and isinstance(ctx.args[0], str) and len(ctx.args[0]) == 1:
                print(f"  WARNING: First arg is single char: '{ctx.args[0]}'")
                print(f"  This suggests string is being split into chars!")

            try:
                return original_invoke(self, ctx)
            except Exception as e:
                print(f"  ERROR: {e}")
                raise

        click.Group.invoke = debug_invoke

        try:
            # Run the test
            runner = CliRunner()
            result = runner.invoke(cli.app, ["database", "user", "list"])

            print(f"\nFinal result:")
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")

            if result.exception:
                print(f"Exception: {result.exception}")

        finally:
            # Restore
            click.Group.invoke = original_invoke

    # Run test
    test_debug_invoke()

finally:
    # Restore argv
    sys.argv = original_argv
