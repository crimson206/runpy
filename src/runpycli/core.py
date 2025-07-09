"""Core Runpy implementation - simplified version"""

import click
import json
from typing import Callable, Dict, Any, Optional
from functools import wraps

from .analyzer import analyze_function
from .click_helpers import RunpyGroup, RunpyCommand, get_click_type
from .commands import add_schema_command, add_docs_command
from .group import RunpyCommandGroup
from .pydantic_utils import get_pydantic_models_from_function, get_model_schema, is_pydantic_model


class Runpy:
    """Main class for converting Python functions to CLI commands"""

    def __init__(
        self,
        name: Optional[str] = None,
        version: Optional[str] = None,
        transform_underscore_to_dash: bool = True,
        config_file: Optional[str] = None,
    ):
        """
        Initialize Runpy CLI generator

        Args:
            name: Base command name or path (e.g., "myapp" or "myapp/subcommand")
            version: Application version
            transform_underscore_to_dash: Whether to convert underscores to dashes in command names
            config_file: Path to JSON configuration file with defaults and shortcuts
        """
        self.name = name or "cli"
        self.version = version
        self.transform_underscore_to_dash = transform_underscore_to_dash
        self.commands = {}
        self.shortcuts = {}
        self.function_info = {}  # Store original function info for schema generation
        self.functions = {}  # Store original function objects
        self.config_defaults = {}  # Store default values from config

        # Load configuration if provided
        if config_file:
            self._load_config(config_file)

        # Parse command path if provided
        self.command_path = []
        if "/" in self.name:
            parts = self.name.split("/")
            self.name = parts[0]
            self.command_path = parts[1:]

        # Create main click group with custom error handling
        self.app = RunpyGroup(
            name=self.name,
            help=f"{self.name} CLI",
            transform_underscore_to_dash=self.transform_underscore_to_dash,
        )

        # Create nested groups if command path is provided
        self.current_group = self.app
        for path_part in self.command_path:
            new_group = click.Group(name=path_part, help=f"{path_part} commands")
            self.current_group.add_command(new_group)
            self.current_group = new_group

        # Add version option if provided
        if self.version:
            self.app = click.version_option(version=self.version)(self.app)

        # Add built-in commands
        add_schema_command(self)
        add_docs_command(self)

    def _load_config(self, config_file: str) -> None:
        """Load configuration from JSON file"""
        import os

        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(config_file, "r") as f:
            config = json.load(f)

        # Load defaults
        if "defaults" in config:
            self.config_defaults = config["defaults"]

        # Load shortcuts
        if "shortcuts" in config:
            # Store global shortcuts
            self.shortcuts = config["shortcuts"]

    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        shortcuts: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Register a function as a CLI command

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
                if self.transform_underscore_to_dash
                else func.__name__
            )

        # Analyze function
        func_info = analyze_function(func)

        # Store function info for schema generation
        self.function_info[cmd_name] = func_info

        # Store original function
        self.functions[cmd_name] = func

        # Store shortcuts
        if shortcuts:
            self.shortcuts[cmd_name] = shortcuts

        # Get Pydantic models used in this function
        models = get_pydantic_models_from_function(func)
        model_schemas = {}
        for model_name, model_type in models.items():
            model_schemas[model_name] = get_model_schema(model_type)

        # Create click command
        # Identify VAR_POSITIONAL parameter
        var_positional_param = None
        for param in func_info["parameters"]:
            if param["kind"] == "VAR_POSITIONAL":
                var_positional_param = param["name"]
                break

        # Build help text (return type will be handled by RunpyCommand)
        help_text = func_info.get("summary", func.__doc__) or ""

        # Use RunpyCommand if we have models, otherwise regular command
        if model_schemas:
            command_decorator = lambda f: RunpyCommand(
                name=cmd_name,
                callback=f,
                help=help_text,
                models=model_schemas,
                func_info=func_info,
            )
        else:
            command_decorator = lambda f: RunpyCommand(
                name=cmd_name, callback=f, help=help_text, func_info=func_info
            )

        @wraps(func)
        def click_command(**kwargs):
            # Prepare function arguments
            func_args = {}
            var_args = []

            # Separate regular kwargs from VAR_POSITIONAL
            for key, value in kwargs.items():
                if key == var_positional_param:
                    # This is the *args parameter
                    var_args = value
                else:
                    func_args[key] = value
            
            # Process parameters to handle BaseModel types
            import inspect
            sig = inspect.signature(func)
            
            for param_name, param_obj in sig.parameters.items():
                if param_name in func_args and param_obj.annotation != param_obj.empty:
                    # Check if this parameter is a Pydantic BaseModel
                    if is_pydantic_model(param_obj.annotation):
                        # Convert JSON string to BaseModel instance
                        json_str = func_args[param_name]
                        try:
                            if isinstance(json_str, str):
                                # Parse JSON string
                                json_data = json.loads(json_str)
                                # Create BaseModel instance
                                func_args[param_name] = param_obj.annotation(**json_data)
                            elif isinstance(json_str, dict):
                                # If already a dict, create BaseModel directly
                                func_args[param_name] = param_obj.annotation(**json_str)
                        except json.JSONDecodeError as e:
                            raise click.BadParameter(
                                f"Invalid JSON for parameter '{param_name}': {str(e)}"
                            )
                        except Exception as e:
                            raise click.BadParameter(
                                f"Error creating {param_obj.annotation.__name__} for parameter '{param_name}': {str(e)}"
                            )

            # Call the original function
            if var_positional_param:
                # Build ordered args list based on function signature
                ordered_args = []
                remaining_kwargs = {}

                # Get parameter order from func_info
                for param in func_info["parameters"]:
                    if param["kind"] == "VAR_POSITIONAL":
                        break  # Stop at *args
                    if param["name"] in func_args:
                        ordered_args.append(func_args[param["name"]])
                    elif param["default"] is None and param["kind"] != "VAR_POSITIONAL":
                        # Required parameter missing
                        raise TypeError(f"Missing required argument: {param['name']}")

                # Call with ordered args followed by varargs
                result = func(*ordered_args, *var_args)
            else:
                result = func(**func_args)

            # Format output based on return type
            if result is not None:
                if isinstance(result, dict):
                    click.echo(json.dumps(result, indent=2))
                elif isinstance(result, (list, tuple)):
                    for item in result:
                        click.echo(item)
                else:
                    click.echo(result)

            return result

        # Create the command with decorator
        click_command_instance = command_decorator(click_command)

        # Add parameters to click command
        for param in reversed(func_info["parameters"]):
            click_command_instance = self._add_parameter_to_command(
                click_command_instance, param, self.shortcuts.get(cmd_name, {})
            )

        # Add command to appropriate group
        self._add_command_to_hierarchy(click_command_instance)

    def _add_parameter_to_command(
        self, command: click.Command, param_info: dict, shortcuts: dict
    ) -> click.Command:
        """Add a parameter to a click command"""
        param_name = param_info["name"]
        param_type = param_info["annotation"]
        default = param_info["default"]
        description = param_info["description"] or ""

        # Check if there's a config default for this parameter
        # Config defaults override function defaults
        if param_name in self.config_defaults:
            default = self.config_defaults[param_name]

        # Determine if parameter is required
        is_required = default is None and param_info["kind"] != "VAR_POSITIONAL"
        
        # Check if this is a BaseModel parameter
        import inspect
        func = self.functions.get(command.name)
        is_basemodel_param = False
        if func:
            sig = inspect.signature(func)
            if param_name in sig.parameters:
                param_obj = sig.parameters[param_name]
                if param_obj.annotation != param_obj.empty:
                    is_basemodel_param = is_pydantic_model(param_obj.annotation)

        # Get click type from annotation
        click_type = get_click_type(param_type)
        
        # Prepare metavar (display type) for the parameter
        metavar = None
        if is_basemodel_param and param_obj.annotation != param_obj.empty:
            # Show the actual BaseModel type in help
            model_name = param_obj.annotation.__name__
            metavar = model_name
            description = description.strip()
        else:
            # Use Python type annotation as metavar
            if param_type == "int" or param_type == "<class 'int'>":
                metavar = "int"
            elif param_type == "float" or param_type == "<class 'float'>":
                metavar = "float"
            elif param_type == "str" or param_type == "<class 'str'>":
                metavar = "str"
            elif param_type == "bool" or param_type == "<class 'bool'>":
                metavar = "bool"
            elif "List[" in param_type or "list[" in param_type:
                metavar = param_type.replace("typing.", "")
            else:
                # Clean up the type annotation for display
                metavar = param_type.replace("typing.", "").replace("<class '", "").replace("'>", "")

        # Build option names
        if (
            self.transform_underscore_to_dash
            if hasattr(self, "transform_underscore_to_dash")
            else True
        ):
            option_names = [f"--{param_name.replace('_', '-')}"]
        else:
            option_names = [f"--{param_name}"]

        # Check for shortcuts (function-specific first, then global)
        if param_name in shortcuts:
            option_names.insert(0, f"-{shortcuts[param_name]}")
        elif param_name in self.shortcuts:
            option_names.insert(0, f"-{self.shortcuts[param_name]}")

        # Handle different parameter kinds
        if param_info["kind"] == "VAR_POSITIONAL":
            # Handle *args as multiple arguments
            # Store the mapping for later use
            decorator = click.argument(
                param_name,  # Keep original name
                nargs=-1,
                type=click_type,
                required=False,
            )
        else:
            # Regular parameters as options
            # Handle boolean flags specially
            if param_type in ["bool", "<class 'bool'>"]:
                decorator = click.option(
                    *option_names,
                    is_flag=True,
                    default=default,
                    help=description,
                    show_default=True if default is not None else False,
                )
            else:
                decorator = click.option(
                    *option_names,
                    default=default,
                    required=is_required,
                    type=click_type,
                    help=description,
                    show_default=True if default is not None else False,
                    metavar=metavar,
                )

        return decorator(command)

    def _add_command_to_hierarchy(self, command: click.Command) -> None:
        """Add command to the appropriate place in hierarchy"""
        # If we have a command path, add to the current group
        if hasattr(self, "current_group") and self.current_group != self.app:
            self.current_group.add_command(command)
        else:
            # Otherwise add to main app
            self.app.add_command(command)

    def register_module(self, module, prefix: str = "") -> None:
        """
        Register all public functions from a module or class

        Args:
            module: Module or class containing functions to register
            prefix: Optional prefix to add to all command names
        """
        import inspect

        # Get all members of the module/class
        members = inspect.getmembers(module)

        for name, obj in members:
            # Skip private/protected members
            if name.startswith("_"):
                continue

            # Check if it's a callable function or static method
            if callable(obj) and (
                inspect.isfunction(obj)
                or inspect.ismethod(obj)
                or hasattr(module, name)
            ):
                # For class methods, get the actual function
                if hasattr(module, name):
                    attr = getattr(module, name)
                    if isinstance(attr, staticmethod):
                        # Get function from staticmethod descriptor
                        obj = attr.__func__

                # Create command name with prefix
                if prefix:
                    cmd_name = f"{prefix}_{name}"
                else:
                    cmd_name = name

                # Register the function
                self.register(obj, name=cmd_name)

    def group(self, name: str) -> RunpyCommandGroup:
        """Create a command group"""
        # Create a Click group for this subcommand
        group_name = (
            name.replace("_", "-") if self.transform_underscore_to_dash else name
        )
        group_command = click.Group(name=group_name, help=f"{name} commands")

        # Add the group to the hierarchy
        self._add_command_to_hierarchy(group_command)

        # Return a RunpyCommandGroup instance
        return RunpyCommandGroup(group_command, self)
