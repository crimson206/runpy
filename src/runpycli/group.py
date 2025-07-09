"""Command group functionality for Runpy"""

import click
import json
from typing import Callable, Dict, Optional, TYPE_CHECKING
from functools import wraps

if TYPE_CHECKING:
    from .core import Runpy

from .analyzer import analyze_function


class RunpyCommandGroup:
    """Represents a command group that can contain subcommands"""

    def __init__(self, group: click.Group, parent_runpy: "Runpy"):
        """
        Initialize RunpyGroup

        Args:
            group: The Click group instance
            parent_runpy: The parent Runpy instance (for accessing shortcuts etc)
        """
        self.click_group = group
        self.parent_runpy = parent_runpy

    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        shortcuts: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Register a function as a command in this group

        Args:
            func: Function to register
            name: Command name (defaults to function name)
            shortcuts: Dictionary mapping parameter names to short options
        """
        if name:
            cmd_name = name
        else:
            cmd_name = (
                func.__name__.replace("_", "-")
                if self.parent_runpy.transform_underscore_to_dash
                else func.__name__
            )

        # Analyze function
        func_info = analyze_function(func)

        # Store function info in parent for schema generation
        full_cmd_name = f"{self.click_group.name}/{cmd_name}"
        self.parent_runpy.function_info[full_cmd_name] = func_info

        # Store original function
        self.parent_runpy.functions[full_cmd_name] = func

        # Store shortcuts in parent
        if shortcuts:
            self.parent_runpy.shortcuts[full_cmd_name] = shortcuts

        # Create click command (similar to Runpy.register)
        var_positional_param = None
        for param in func_info["parameters"]:
            if param["kind"] == "VAR_POSITIONAL":
                var_positional_param = param["name"]
                break

        @click.command(name=cmd_name, help=func_info.get("summary", func.__doc__))
        @wraps(func)
        def click_command(**kwargs):
            # Prepare function arguments
            func_args = {}
            var_args = []

            # Separate regular kwargs from VAR_POSITIONAL
            for key, value in kwargs.items():
                if key == var_positional_param:
                    var_args = value
                else:
                    func_args[key] = value

            # Call the original function
            if var_positional_param:
                ordered_args = []

                for param in func_info["parameters"]:
                    if param["kind"] == "VAR_POSITIONAL":
                        break
                    if param["name"] in func_args:
                        ordered_args.append(func_args[param["name"]])
                    elif param["default"] is None and param["kind"] != "VAR_POSITIONAL":
                        raise TypeError(f"Missing required argument: {param['name']}")

                result = func(*ordered_args, *var_args)
            else:
                result = func(**func_args)

            # Format output
            if result is not None:
                if isinstance(result, dict):
                    click.echo(json.dumps(result, indent=2))
                elif isinstance(result, (list, tuple)):
                    for item in result:
                        click.echo(item)
                else:
                    click.echo(result)

            return result

        # Add parameters to click command
        for param in reversed(func_info["parameters"]):
            click_command = self.parent_runpy._add_parameter_to_command(
                click_command,
                param,
                self.parent_runpy.shortcuts.get(
                    f"{self.click_group.name}/{cmd_name}", {}
                ),
            )

        # Add command to this group
        self.click_group.add_command(click_command)

    def group(self, name: str) -> "RunpyCommandGroup":
        """Create a subgroup within this group"""
        # Create a Click group for this subcommand
        subgroup_name = (
            name.replace("_", "-")
            if self.parent_runpy.transform_underscore_to_dash
            else name
        )
        subgroup_command = click.Group(name=subgroup_name, help=f"{name} commands")

        # Add the subgroup to this group
        self.click_group.add_command(subgroup_command)

        # Return a new RunpyCommandGroup instance
        return RunpyCommandGroup(subgroup_command, self.parent_runpy)
