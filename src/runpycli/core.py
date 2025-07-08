"""Core Runpy implementation"""

import click
import inspect
import json
from typing import (
    Callable,
    Dict,
    Any,
    Optional,
    Type,
    get_type_hints,
    get_args,
    get_origin,
)
from functools import wraps

try:
    from func_analyzer import analyze_function as _analyze_function
except ImportError:
    # Fallback implementation if func_analyzer is not available
    def _analyze_function(func: Callable) -> dict:
        """Simple function analysis fallback"""
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or ""

        # Extract summary (first line)
        lines = docstring.strip().split("\n")
        summary = lines[0] if lines else ""

        parameters = []
        for name, param in sig.parameters.items():
            if name in ("self", "cls"):
                continue

            # Get type annotation
            annotation = param.annotation
            if annotation is param.empty:
                annotation_str = "Any"
            else:
                annotation_str = str(annotation).replace("typing.", "")

            parameters.append(
                {
                    "name": name,
                    "annotation": annotation_str,
                    "default": (
                        param.default if param.default is not param.empty else None
                    ),
                    "kind": str(param.kind),
                    "description": None,  # Simple fallback doesn't parse docstring params
                }
            )

        return {
            "name": func.__name__,
            "summary": summary,
            "docstring": docstring,
            "parameters": parameters,
            "is_async": inspect.iscoroutinefunction(func),
            "is_generator": inspect.isgeneratorfunction(func),
        }


analyze_function = _analyze_function


class RunpyGroup(click.Group):
    """Custom Click Group with enhanced error messages"""
    
    def __init__(self, *args, transform_underscore_to_dash: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform_underscore_to_dash = transform_underscore_to_dash
    
    def resolve_command(self, ctx, args):
        """Override to provide better error messages for command not found"""
        cmd_name = args[0]
        cmd = self.commands.get(cmd_name)
        
        if cmd is None:
            # Try to find similar commands
            if self.transform_underscore_to_dash and '_' in cmd_name:
                # Suggest dash version
                dash_version = cmd_name.replace('_', '-')
                if dash_version in self.commands:
                    ctx.fail(f"No such command '{cmd_name}'. Did you mean '{dash_version}'?")
            elif self.transform_underscore_to_dash and '-' in cmd_name:
                # Check if underscore version was registered
                underscore_version = cmd_name.replace('-', '_')
                if any(orig_name.replace('_', '-') == cmd_name for orig_name in self.commands):
                    ctx.fail(f"No such command '{cmd_name}'. This CLI uses dashes instead of underscores.")
            
            # Default error
            ctx.fail(f"No such command '{cmd_name}'.")
        
        return cmd_name, cmd, args[1:]


class Runpy:
    """Main class for converting Python functions to CLI commands"""

    def __init__(self, name: Optional[str] = None, version: Optional[str] = None, 
                 transform_underscore_to_dash: bool = True):
        """
        Initialize Runpy CLI generator

        Args:
            name: Base command name or path (e.g., "myapp" or "myapp/subcommand")
            version: Application version
            transform_underscore_to_dash: Whether to convert underscores to dashes in command names
        """
        self.name = name or "cli"
        self.version = version
        self.transform_underscore_to_dash = transform_underscore_to_dash
        self.commands = {}
        self.shortcuts = {}
        self.function_info = {}  # Store original function info for schema generation

        # Parse command path if provided
        self.command_path = []
        if "/" in self.name:
            parts = self.name.split("/")
            self.name = parts[0]
            self.command_path = parts[1:]

        # Create main click group with custom error handling
        self.app = RunpyGroup(name=self.name, help=f"{self.name} CLI", 
                              transform_underscore_to_dash=self.transform_underscore_to_dash)

        # Create nested groups if command path is provided
        self.current_group = self.app
        for path_part in self.command_path:
            new_group = click.Group(name=path_part, help=f"{path_part} commands")
            self.current_group.add_command(new_group)
            self.current_group = new_group

        # Add version option if provided
        if self.version:
            self.app = click.version_option(version=self.version)(self.app)
        
        # Add built-in schema command
        self._add_schema_command()
        
        # Add built-in docs command
        self._add_docs_command()

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
            cmd_name = func.__name__.replace("_", "-") if self.transform_underscore_to_dash else func.__name__

        # Analyze function
        func_info = analyze_function(func)
        
        # Store function info for schema generation
        self.function_info[cmd_name] = func_info

        # Store shortcuts
        if shortcuts:
            self.shortcuts[cmd_name] = shortcuts

        # Create click command
        # Identify VAR_POSITIONAL parameter
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
                    # This is the *args parameter
                    var_args = value
                else:
                    func_args[key] = value

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

        # Add parameters to click command
        for param in reversed(func_info["parameters"]):
            click_command = self._add_parameter_to_command(
                click_command, param, self.shortcuts.get(cmd_name, {})
            )

        # Add command to appropriate group
        self._add_command_to_hierarchy(click_command)

    def _add_parameter_to_command(
        self, command: click.Command, param_info: dict, shortcuts: dict
    ) -> click.Command:
        """Add a parameter to a click command"""
        param_name = param_info["name"]
        param_type = param_info["annotation"]
        default = param_info["default"]
        description = param_info["description"] or ""

        # Determine if parameter is required
        is_required = default is None and param_info["kind"] != "VAR_POSITIONAL"

        # Get click type from annotation
        click_type = self._get_click_type(param_type)

        # Build option names
        if self.transform_underscore_to_dash if hasattr(self, 'transform_underscore_to_dash') else True:
            option_names = [f"--{param_name.replace('_', '-')}"]
        else:
            option_names = [f"--{param_name}"]
        if param_name in shortcuts:
            option_names.insert(0, f"-{shortcuts[param_name]}")

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
                )

        return decorator(command)

    def _get_click_type(self, type_annotation: str) -> Any:
        """Convert Python type annotation to Click type"""
        # Handle basic types
        type_map = {
            "int": click.INT,
            "float": click.FLOAT,
            "str": click.STRING,
            "bool": click.BOOL,
        }

        # Clean annotation string
        clean_type = type_annotation.strip("'\"")

        # Handle <class 'type'> format
        if clean_type.startswith("<class '") and clean_type.endswith("'>"):
            clean_type = clean_type[8:-2]  # Extract type name

        # Check if it's a simple type
        if clean_type in type_map:
            return type_map[clean_type]

        # Handle List types
        if clean_type.startswith("List[") or clean_type.startswith("list["):
            # For now, return string and handle conversion in the function
            return click.STRING

        # Default to string
        return click.STRING

    def _add_command_to_hierarchy(self, command: click.Command) -> None:
        """Add command to the appropriate place in hierarchy"""
        # If we have a command path, add to the current group
        if hasattr(self, "current_group") and self.current_group != self.app:
            self.current_group.add_command(command)
        else:
            # Otherwise add to main app
            self.app.add_command(command)

    def group(self, name: str) -> "RunpyCommandGroup":
        """Create a command group"""
        # Create a Click group for this subcommand
        group_name = name.replace("_", "-") if self.transform_underscore_to_dash else name
        group_command = click.Group(
            name=group_name, help=f"{name} commands"
        )

        # Add the group to the hierarchy
        self._add_command_to_hierarchy(group_command)

        # Return a RunpyCommandGroup instance
        return RunpyCommandGroup(group_command, self)
    
    def _add_schema_command(self) -> None:
        """Add the built-in schema command"""
        @click.command(name="schema", help="Generate API-style documentation for all commands")
        @click.option("--format", type=click.Choice(["json", "yaml", "markdown"]), default="json", help="Output format")
        def schema_command(format: str):
            """Generate and display schema for all registered commands"""
            schema = self._generate_schema()
            
            if format == "json":
                click.echo(json.dumps(schema, indent=2))
            elif format == "yaml":
                # Simple YAML-like output (without external dependency)
                click.echo(self._schema_to_yaml(schema))
            elif format == "markdown":
                click.echo(self._schema_to_markdown(schema))
        
        self.app.add_command(schema_command)
    
    def _add_docs_command(self) -> None:
        """Add the built-in docs command"""
        @click.command(name="docs", help="View command documentation and help")
        @click.argument("commands", nargs=-1, required=False)
        @click.option("--filter", "-f", help="Filter commands by pattern")
        @click.option("--interactive", "-i", is_flag=True, help="Interactive documentation browser")
        @click.option("--export", "-e", type=click.Choice(["markdown", "html", "man"]), help="Export documentation format")
        def docs_command(commands, filter, interactive, export):
            """Show documentation for commands"""
            if interactive:
                self._show_interactive_docs()
            elif export:
                self._export_docs(export)
            elif commands:
                self._show_specific_docs(commands)
            elif filter:
                self._show_filtered_docs(filter)
            else:
                self._show_all_docs()
        
        self.app.add_command(docs_command)
    
    def _generate_schema(self) -> dict:
        """Generate schema for all registered commands"""
        schema = {
            "name": self.name,
            "version": self.version,
            "commands": {},
            "groups": {}
        }
        
        # Process all commands in the app
        self._collect_commands(self.app, schema)
        
        return schema
    
    def _collect_commands(self, group: click.Group, schema: dict, path: str = "") -> None:
        """Recursively collect all commands and groups"""
        for cmd_name, cmd in group.commands.items():
            # Skip built-in commands
            if cmd_name == "schema":
                continue
            if isinstance(cmd, click.Group):
                # It's a group
                group_schema = {
                    "description": cmd.help or f"{cmd_name} commands",
                    "commands": {},
                    "groups": {}
                }
                if path:
                    # Nested group
                    parts = path.split("/")
                    current = schema["groups"]
                    for part in parts:
                        if part not in current:
                            current[part] = {"commands": {}, "groups": {}}
                        current = current[part]["groups"]
                    current[cmd_name] = group_schema
                else:
                    # Top-level group
                    schema["groups"][cmd_name] = group_schema
                
                # Recursively process subcommands
                self._collect_commands(cmd, schema, f"{path}/{cmd_name}" if path else cmd_name)
            else:
                # It's a command
                cmd_schema = self._get_command_schema(cmd, cmd_name, path)
                if path:
                    # Command in a group
                    parts = path.split("/")
                    current = schema["groups"]
                    for part in parts:
                        current = current[part]
                    current["commands"][cmd_name] = cmd_schema
                else:
                    # Top-level command
                    schema["commands"][cmd_name] = cmd_schema
    
    def _get_command_schema(self, cmd: click.Command, cmd_name: str, path: str = "") -> dict:
        """Get schema for a single command"""
        cmd_schema = {
            "description": cmd.help or "",
            "parameters": {}
        }
        
        # Try to get original function info
        # For grouped commands, check with full path
        if path:
            func_info = self.function_info.get(f"{path}/{cmd_name}")
        else:
            func_info = self.function_info.get(cmd_name)
        
        # Get parameter information
        for param in cmd.params:
            param_schema = {}
            
            if isinstance(param, click.Option):
                param_name = param.name
                
                # Try to get original type from function info
                if func_info:
                    for p in func_info["parameters"]:
                        if p["name"] == param_name:
                            param_schema["type"] = self._get_schema_type_from_annotation(p["annotation"])
                            break
                    else:
                        param_schema["type"] = self._get_param_type(param.type)
                else:
                    param_schema["type"] = self._get_param_type(param.type)
                
                # Check if it's Optional type from function info
                if func_info:
                    for p in func_info["parameters"]:
                        if p["name"] == param_name and "Optional[" in p["annotation"]:
                            param_schema["required"] = False
                            break
                    else:
                        param_schema["required"] = param.required
                else:
                    param_schema["required"] = param.required
                # Handle special default values
                if param.default is not None:
                    # Handle Enum types
                    if hasattr(param.default, 'value'):
                        param_schema["default"] = param.default.value
                    else:
                        param_schema["default"] = param.default
                else:
                    param_schema["default"] = None
                param_schema["help"] = param.help or ""
                
                # Check for shortcuts - consider path for grouped commands
                shortcut_key = f"{path}/{cmd_name}" if path else cmd_name
                if shortcut_key in self.shortcuts and param_name in self.shortcuts[shortcut_key]:
                    param_schema["shortcut"] = self.shortcuts[shortcut_key][param_name]
                
                # Check if it's a flag
                if param.is_flag:
                    param_schema["type"] = "boolean"
                    param_schema["is_flag"] = True
                
                cmd_schema["parameters"][param_name] = param_schema
            elif isinstance(param, click.Argument):
                param_schema["type"] = self._get_param_type(param.type)
                param_schema["required"] = param.required
                param_schema["multiple"] = param.nargs == -1
                cmd_schema["parameters"][param.name] = param_schema
        
        return cmd_schema
    
    def _get_param_type(self, click_type) -> str:
        """Convert Click type to schema type string"""
        if click_type == click.INT:
            return "integer"
        elif click_type == click.FLOAT:
            return "float"
        elif click_type == click.STRING:
            return "string"
        elif click_type == click.BOOL:
            return "boolean"
        elif isinstance(click_type, click.Choice):
            return "enum"
        else:
            # For now, complex types are stored as strings in Click
            # We need to look at the original type annotation
            return "string"
    
    def _get_schema_type_from_annotation(self, annotation: str) -> str:
        """Get schema type from Python type annotation string"""
        # Clean up the annotation string
        annotation = annotation.replace("typing.", "").replace("<class '", "").replace("'>", "")
        
        # Basic types
        if annotation in ["int", "integer"]:
            return "integer"
        elif annotation in ["float"]:
            return "float"
        elif annotation in ["str", "string"]:
            return "string"
        elif annotation in ["bool", "boolean"]:
            return "boolean"
        
        # Complex types
        elif annotation.startswith("List[") or annotation.startswith("list["):
            return "array"
        elif annotation.startswith("Dict[") or annotation.startswith("dict["):
            return "object"
        elif annotation.startswith("Optional["):
            # Extract the inner type
            inner = annotation[9:-1]  # Remove "Optional[" and "]"
            return self._get_schema_type_from_annotation(inner)
        elif annotation.startswith("Union["):
            return "union"
        elif annotation.startswith("Literal["):
            return "literal"
        elif "BaseModel" in annotation or annotation[0].isupper():
            # Likely a Pydantic model or custom class
            return "object"
        else:
            return "string"
    
    def _schema_to_yaml(self, schema: dict, indent: int = 0) -> str:
        """Convert schema to YAML-like format"""
        lines = []
        indent_str = "  " * indent
        
        for key, value in schema.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                lines.append(self._schema_to_yaml(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}:")
                for item in value:
                    lines.append(f"{indent_str}- {item}")
            elif value is None:
                lines.append(f"{indent_str}{key}: null")
            elif isinstance(value, bool):
                lines.append(f"{indent_str}{key}: {str(value).lower()}")
            else:
                lines.append(f"{indent_str}{key}: {value}")
        
        return "\n".join(lines)
    
    def _schema_to_markdown(self, schema: dict) -> str:
        """Convert schema to Markdown format"""
        lines = [f"# {schema['name']} CLI Documentation"]
        
        if schema.get('version'):
            lines.append(f"\nVersion: {schema['version']}")
        
        # Top-level commands
        if schema.get('commands'):
            lines.append("\n# Commands\n")
            for cmd_name, cmd_info in schema['commands'].items():
                lines.append(f"## {cmd_name}")
                lines.append(f"\n{cmd_info['description']}\n")
                
                if cmd_info.get('parameters'):
                    lines.append("### Parameters\n")
                    for param_name, param_info in cmd_info['parameters'].items():
                        param_line = f"- `--{param_name}`"
                        if param_info.get('shortcut'):
                            param_line += f" / `-{param_info['shortcut']}`"
                        param_line += f" ({param_info['type']})"
                        if not param_info.get('required', True):
                            param_line += " [optional]"
                        if param_info.get('default') is not None:
                            param_line += f" - default: {param_info['default']}"
                        lines.append(param_line)
                        if param_info.get('help'):
                            lines.append(f"  - {param_info['help']}")
        
        # Groups
        if schema.get('groups'):
            lines.append("\n# Command Groups\n")
            self._markdown_groups(schema['groups'], lines)
        
        return "\n".join(lines)
    
    def _markdown_groups(self, groups: dict, lines: list, level: int = 2) -> None:
        """Recursively add groups to markdown"""
        for group_name, group_info in groups.items():
            lines.append(f"\n{'#' * level} {group_name}")
            lines.append(f"\n{group_info.get('description', '')}\n")
            
            # Commands in this group
            if group_info.get('commands'):
                for cmd_name, cmd_info in group_info['commands'].items():
                    lines.append(f"\n{'#' * (level + 1)} {cmd_name}")
                    lines.append(f"\n{cmd_info['description']}\n")
                    
                    if cmd_info.get('parameters'):
                        lines.append("Parameters:\n")
                        for param_name, param_info in cmd_info['parameters'].items():
                            param_line = f"- `--{param_name}`"
                            if param_info.get('shortcut'):
                                param_line += f" / `-{param_info['shortcut']}`"
                            param_line += f" ({param_info['type']})"
                            if not param_info.get('required', True):
                                param_line += " [optional]"
                            lines.append(param_line)
            
            # Nested groups
            if group_info.get('groups'):
                self._markdown_groups(group_info['groups'], lines, level + 1)
    
    def _show_all_docs(self) -> None:
        """Show documentation for all commands in tree structure"""
        click.echo(f"📖 {self.name} Documentation")
        if self.version:
            click.echo(f"Version: {self.version}")
        click.echo()
        
        # Collect all commands and groups
        docs_tree = self._build_docs_tree()
        self._print_docs_tree(docs_tree)
    
    def _show_specific_docs(self, commands) -> None:
        """Show detailed documentation for specific commands"""
        for i, cmd_path in enumerate(commands):
            if i > 0:
                click.echo("─" * 60)
                click.echo()
            
            # Find and show command help
            cmd = self._find_command_by_path(cmd_path)
            if cmd:
                # Convert path to readable format (e.g., "deploy/service" -> "deploy service")
                readable_path = cmd_path.replace("/", " ")
                click.echo(f"📋 {readable_path}")
                click.echo("=" * (len(readable_path) + 3))
                click.echo()
                
                # Get the command's help
                ctx = click.Context(cmd)
                click.echo(cmd.get_help(ctx))
            else:
                click.echo(f"❌ Command not found: {cmd_path}")
                click.echo()
    
    def _show_filtered_docs(self, pattern: str) -> None:
        """Show documentation for commands matching the pattern"""
        click.echo(f"📖 Commands matching '{pattern}'")
        click.echo()
        
        docs_tree = self._build_docs_tree()
        filtered_tree = self._filter_docs_tree(docs_tree, pattern)
        
        if filtered_tree["commands"] or filtered_tree["groups"]:
            self._print_docs_tree(filtered_tree)
        else:
            click.echo(f"No commands found matching pattern: {pattern}")
    
    def _show_interactive_docs(self) -> None:
        """Show interactive documentation browser"""
        click.echo("🔍 Interactive Documentation Browser")
        click.echo("(Use arrow keys to navigate, Enter to select, 'q' to quit)")
        click.echo()
        
        # For now, just show all docs
        # In a full implementation, this would use a library like blessed or rich
        # for proper interactive navigation
        self._show_all_docs()
    
    def _export_docs(self, format: str) -> None:
        """Export documentation in specified format"""
        if format == "markdown":
            content = self._generate_markdown_docs()
            click.echo(content)
        elif format == "html":
            content = self._generate_html_docs()
            click.echo(content)
        elif format == "man":
            content = self._generate_man_docs()
            click.echo(content)
    
    def _build_docs_tree(self) -> dict:
        """Build a tree structure of all commands and their documentation"""
        tree = {"commands": {}, "groups": {}}
        
        # Process all commands in the app
        self._collect_docs_tree(self.app, tree)
        
        return tree
    
    def _collect_docs_tree(self, group: click.Group, tree: dict, path: str = "") -> None:
        """Recursively collect commands and groups for docs tree"""
        for cmd_name, cmd in group.commands.items():
            # Skip built-in commands
            if cmd_name in ["schema", "docs"]:
                continue
                
            if isinstance(cmd, click.Group):
                # It's a group
                group_tree = {"commands": {}, "groups": {}, "help": cmd.help or f"{cmd_name} commands"}
                
                if path:
                    # Nested group
                    parts = path.split("/")
                    current = tree["groups"]
                    for part in parts:
                        if part not in current:
                            current[part] = {"commands": {}, "groups": {}, "help": ""}
                        current = current[part]["groups"]
                    current[cmd_name] = group_tree
                else:
                    # Top-level group
                    tree["groups"][cmd_name] = group_tree
                
                # Recursively process subcommands
                self._collect_docs_tree(cmd, tree, f"{path}/{cmd_name}" if path else cmd_name)
            else:
                # It's a command
                cmd_doc = {
                    "help": cmd.help or "",
                    "summary": (cmd.help or "").split('\n')[0] if cmd.help else ""
                }
                
                if path:
                    # Command in a group
                    parts = path.split("/")
                    current = tree["groups"]
                    for part in parts:
                        current = current[part]
                    current["commands"][cmd_name] = cmd_doc
                else:
                    # Top-level command
                    tree["commands"][cmd_name] = cmd_doc
    
    def _print_docs_tree(self, tree: dict, prefix: str = "", is_last: bool = True) -> None:
        """Print the docs tree in a nice tree format"""
        # Print top-level commands first
        cmd_items = list(tree["commands"].items())
        group_items = list(tree["groups"].items())
        
        all_items = [(name, doc, "command") for name, doc in cmd_items] + \
                   [(name, info, "group") for name, info in group_items]
        
        for i, (name, info, item_type) in enumerate(all_items):
            is_last_item = i == len(all_items) - 1
            
            if item_type == "command":
                # Print command
                branch = "└── " if is_last_item else "├── "
                click.echo(f"{prefix}{branch}{name}")
                
                # Print command summary
                if info.get("summary"):
                    sub_prefix = "    " if is_last_item else "│   "
                    click.echo(f"{prefix}{sub_prefix}└── {info['summary']}")
            else:
                # Print group
                branch = "└── " if is_last_item else "├── "
                click.echo(f"{prefix}{branch}{name}")
                
                # Print group commands recursively
                sub_prefix = "    " if is_last_item else "│   "
                self._print_docs_tree(info, f"{prefix}{sub_prefix}", True)
    
    def _filter_docs_tree(self, tree: dict, pattern: str) -> dict:
        """Filter the docs tree by pattern"""
        filtered = {"commands": {}, "groups": {}}
        
        # Filter commands
        for name, doc in tree["commands"].items():
            if pattern.lower() in name.lower() or pattern.lower() in doc.get("summary", "").lower():
                filtered["commands"][name] = doc
        
        # Filter groups recursively
        for name, info in tree["groups"].items():
            filtered_group = self._filter_docs_tree(info, pattern)
            
            # Include group if it has matching commands or subgroups, or if the group name matches
            if (filtered_group["commands"] or filtered_group["groups"] or 
                pattern.lower() in name.lower()):
                filtered["groups"][name] = {
                    "commands": filtered_group["commands"],
                    "groups": filtered_group["groups"],
                    "help": info.get("help", "")
                }
        
        return filtered
    
    def _find_command_by_path(self, path: str) -> click.Command:
        """Find a command by its path (e.g., 'group/subcommand')"""
        parts = path.split("/")
        current = self.app
        
        for part in parts:
            if hasattr(current, 'commands') and part in current.commands:
                current = current.commands[part]
            else:
                return None
        
        return current if isinstance(current, click.Command) else None
    
    def _generate_markdown_docs(self) -> str:
        """Generate markdown documentation"""
        lines = [f"# {self.name} Documentation"]
        
        if self.version:
            lines.append(f"\nVersion: {self.version}")
        
        lines.append("\n## Commands\n")
        
        docs_tree = self._build_docs_tree()
        self._markdown_docs_tree(docs_tree, lines)
        
        return "\n".join(lines)
    
    def _generate_html_docs(self) -> str:
        """Generate HTML documentation"""
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{self.name} Documentation</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1, h2, h3 { color: #333; }",
            ".command { margin: 20px 0; }",
            ".summary { color: #666; font-style: italic; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{self.name} Documentation</h1>"
        ]
        
        if self.version:
            lines.append(f"<p>Version: {self.version}</p>")
        
        lines.append("<h2>Commands</h2>")
        
        # Add commands content here
        docs_tree = self._build_docs_tree()
        self._html_docs_tree(docs_tree, lines)
        
        lines.extend(["</body>", "</html>"])
        
        return "\n".join(lines)
    
    def _generate_man_docs(self) -> str:
        """Generate man page documentation"""
        lines = [
            f".TH {self.name.upper()} 1",
            f".SH NAME",
            f"{self.name} - Convert Python functions to CLI commands automatically",
            f".SH SYNOPSIS",
            f".B {self.name}",
            f"[\\fIcommand\\fR] [\\fIoptions\\fR]",
            f".SH DESCRIPTION",
            f"{self.name} automatically converts Python functions into command-line interface commands.",
            f".SH COMMANDS"
        ]
        
        # Add commands in man page format
        docs_tree = self._build_docs_tree()
        self._man_docs_tree(docs_tree, lines)
        
        return "\n".join(lines)
    
    def _markdown_docs_tree(self, tree: dict, lines: list, level: int = 3) -> None:
        """Add docs tree to markdown lines"""
        # Add commands
        for name, doc in tree["commands"].items():
            lines.append(f"{'#' * level} {name}")
            if doc.get("summary"):
                lines.append(f"\n{doc['summary']}\n")
        
        # Add groups
        for name, info in tree["groups"].items():
            lines.append(f"{'#' * level} {name}")
            if info.get("help"):
                lines.append(f"\n{info['help']}\n")
            self._markdown_docs_tree(info, lines, level + 1)
    
    def _html_docs_tree(self, tree: dict, lines: list, level: int = 3) -> None:
        """Add docs tree to HTML lines"""
        # Add commands
        for name, doc in tree["commands"].items():
            lines.append(f"<div class='command'>")
            lines.append(f"<h{level}>{name}</h{level}>")
            if doc.get("summary"):
                lines.append(f"<p class='summary'>{doc['summary']}</p>")
            lines.append(f"</div>")
        
        # Add groups
        for name, info in tree["groups"].items():
            lines.append(f"<h{level}>{name}</h{level}>")
            if info.get("help"):
                lines.append(f"<p>{info['help']}</p>")
            self._html_docs_tree(info, lines, level + 1)
    
    def _man_docs_tree(self, tree: dict, lines: list) -> None:
        """Add docs tree to man page lines"""
        # Add commands
        for name, doc in tree["commands"].items():
            lines.append(f".TP")
            lines.append(f".B {name}")
            if doc.get("summary"):
                lines.append(doc['summary'])
        
        # Add groups
        for name, info in tree["groups"].items():
            lines.append(f".SS {name}")
            if info.get("help"):
                lines.append(info['help'])
            self._man_docs_tree(info, lines)


class RunpyCommandGroup:
    """Represents a command group that can contain subcommands"""

    def __init__(self, group: click.Group, parent_runpy: Runpy):
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
            cmd_name = func.__name__.replace("_", "-") if self.parent_runpy.transform_underscore_to_dash else func.__name__

        # Analyze function
        func_info = analyze_function(func)
        
        # Store function info in parent for schema generation
        full_cmd_name = f"{self.click_group.name}/{cmd_name}"
        self.parent_runpy.function_info[full_cmd_name] = func_info

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
                self.parent_runpy.shortcuts.get(f"{self.click_group.name}/{cmd_name}", {}),
            )

        # Add command to this group
        self.click_group.add_command(click_command)

    def group(self, name: str) -> "RunpyCommandGroup":
        """Create a subgroup within this group"""
        # Create a Click group for this subcommand
        subgroup_name = name.replace("_", "-") if self.parent_runpy.transform_underscore_to_dash else name
        subgroup_command = click.Group(
            name=subgroup_name, help=f"{name} commands"
        )

        # Add the subgroup to this group
        self.click_group.add_command(subgroup_command)

        # Return a new RunpyCommandGroup instance
        return RunpyCommandGroup(subgroup_command, self.parent_runpy)
