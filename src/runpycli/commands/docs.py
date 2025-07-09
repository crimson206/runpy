"""Documentation command for Runpy"""

import click
from typing import TYPE_CHECKING, Dict, Type, Any

if TYPE_CHECKING:
    from ..core import Runpy

from ..pydantic_utils import (
    get_pydantic_models_from_function,
    get_model_schema,
    is_pydantic_model,
    PYDANTIC_AVAILABLE,
)


def add_docs_command(runpy_instance: "Runpy") -> None:
    """Add the built-in docs command to a Runpy instance"""

    @click.command(name="docs", help="View command documentation and help")
    @click.argument("commands", nargs=-1, required=False)
    @click.option("--filter", "-f", help="Filter commands by pattern")
    def docs_command(commands, filter):
        """Show documentation for commands"""
        if commands:
            show_specific_docs(runpy_instance, commands)
        elif filter:
            show_filtered_docs(runpy_instance, filter)
        else:
            show_all_docs(runpy_instance)

    runpy_instance.app.add_command(docs_command)


def show_all_docs(runpy_instance: "Runpy") -> None:
    """Show documentation for all commands in tree structure"""
    click.echo(f"📖 {runpy_instance.name} Documentation")
    if runpy_instance.version:
        click.echo(f"Version: {runpy_instance.version}")
    click.echo()

    # Collect all commands and groups
    docs_tree = build_docs_tree(runpy_instance)
    print_docs_tree(docs_tree)

    # Don't show BaseModels in summary view - only show them when viewing specific commands


def show_specific_docs(runpy_instance: "Runpy", commands) -> None:
    """Show detailed documentation for specific commands"""
    for i, cmd_path in enumerate(commands):
        if i > 0:
            click.echo("─" * 60)
            click.echo()

        # Find and show command help
        cmd = find_command_by_path(runpy_instance, cmd_path)
        if cmd:
            # Convert path to readable format (e.g., "deploy/service" -> "deploy service")
            readable_path = cmd_path.replace("/", " ")
            click.echo(f"📋 {readable_path}")
            click.echo("=" * (len(readable_path) + 3))
            click.echo()

            # Try to get the original function info if this is a RunpyCommand
            if hasattr(cmd, "func_info"):
                display_enhanced_command_docs(cmd, runpy_instance)
            else:
                # Fall back to standard Click help
                ctx = click.Context(cmd)
                click.echo(cmd.get_help(ctx))
        else:
            click.echo(f"❌ Command not found: {cmd_path}")
            click.echo()


def show_filtered_docs(runpy_instance: "Runpy", pattern: str) -> None:
    """Show documentation for commands matching the pattern"""
    click.echo(f"📖 Commands matching '{pattern}'")
    click.echo()

    docs_tree = build_docs_tree(runpy_instance)
    filtered_tree = filter_docs_tree(docs_tree, pattern)

    if filtered_tree["commands"] or filtered_tree["groups"]:
        print_docs_tree(filtered_tree)
    else:
        click.echo(f"No commands found matching pattern: {pattern}")


def build_docs_tree(runpy_instance: "Runpy") -> dict:
    """Build a tree structure of all commands and their documentation"""
    tree = {"commands": {}, "groups": {}}

    # Process all commands in the app
    collect_docs_tree(runpy_instance.app, tree)

    return tree


def collect_docs_tree(group: click.Group, tree: dict, path: str = "") -> None:
    """Recursively collect commands and groups for docs tree"""
    for cmd_name, cmd in group.commands.items():
        # Skip built-in commands
        if cmd_name in ["schema", "docs"]:
            continue

        if isinstance(cmd, click.Group):
            # It's a group
            group_tree = {
                "commands": {},
                "groups": {},
                "help": cmd.help or f"{cmd_name} commands",
            }

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
            collect_docs_tree(cmd, tree, f"{path}/{cmd_name}" if path else cmd_name)
        else:
            # It's a command
            cmd_doc = {
                "help": cmd.help or "",
                "summary": (cmd.help or "").split("\n")[0] if cmd.help else "",
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


def print_docs_tree(tree: dict, prefix: str = "", is_last: bool = True) -> None:
    """Print the docs tree in a nice tree format"""
    # Print top-level commands first
    cmd_items = list(tree["commands"].items())
    group_items = list(tree["groups"].items())

    all_items = [(name, doc, "command") for name, doc in cmd_items] + [
        (name, info, "group") for name, info in group_items
    ]

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
            print_docs_tree(info, f"{prefix}{sub_prefix}", True)


def filter_docs_tree(tree: dict, pattern: str) -> dict:
    """Filter the docs tree by pattern"""
    filtered = {"commands": {}, "groups": {}}

    # Filter commands
    for name, doc in tree["commands"].items():
        if (
            pattern.lower() in name.lower()
            or pattern.lower() in doc.get("summary", "").lower()
        ):
            filtered["commands"][name] = doc

    # Filter groups recursively
    for name, info in tree["groups"].items():
        filtered_group = filter_docs_tree(info, pattern)

        # Include group if it has matching commands or subgroups, or if the group name matches
        if (
            filtered_group["commands"]
            or filtered_group["groups"]
            or pattern.lower() in name.lower()
        ):
            filtered["groups"][name] = {
                "commands": filtered_group["commands"],
                "groups": filtered_group["groups"],
                "help": info.get("help", ""),
            }

    return filtered


def find_command_by_path(runpy_instance: "Runpy", path: str) -> click.Command:
    """Find a command by its path (e.g., 'group/subcommand')"""
    parts = path.split("/")
    current = runpy_instance.app

    for part in parts:
        if hasattr(current, "commands") and part in current.commands:
            current = current.commands[part]
        else:
            return None

    return current if isinstance(current, click.Command) else None

    """Generate markdown documentation"""
    lines = [f"# {runpy_instance.name} Documentation"]

    if runpy_instance.version:
        lines.append(f"\nVersion: {runpy_instance.version}")

    lines.append("\n## Commands\n")

    docs_tree = build_docs_tree(runpy_instance)
    markdown_docs_tree(docs_tree, lines)


def display_enhanced_command_docs(cmd: click.Command, runpy_instance: "Runpy") -> None:
    """Display enhanced documentation for a command with proper Python types"""
    # Show usage
    ctx = click.Context(cmd)
    formatter = ctx.make_formatter()
    cmd.format_usage(ctx, formatter)
    click.echo(formatter.getvalue())

    # Show description
    if cmd.help:
        click.echo(f"  {cmd.help}")
        click.echo()

    # Show options with Python types
    if hasattr(cmd, "func_info"):
        func_info = cmd.func_info

        # Show parameters
        if func_info.get("parameters"):
            click.echo("Options:")
            for param in func_info["parameters"]:
                if param["name"] in ["self", "cls"]:
                    continue

                # Get the Python type annotation
                type_str = param.get("annotation", "Any")

                # Build the option line
                option_line = f"  --{param['name'].replace('_', '-')}"

                # Add type information using Python notation
                if type_str != "Any":
                    # Clean up type string for better display
                    clean_type = type_str.replace("<class '", "").replace("'>", "")
                    option_line += f" {clean_type}"

                # Add required/optional info
                if param.get("default") is None and param["name"] != "kwargs":
                    option_line += "  [required]"

                click.echo(option_line)

                # Add description if available
                if param.get("description"):
                    click.echo(f"    {param['description']}")

            click.echo("  --help                 Show this message and exit.")
            click.echo()

        # Show return type
        return_type = func_info.get("return_annotation")
        if (
            return_type
            and return_type != "None"
            and "inspect._empty" not in str(return_type)
        ):
            click.echo("Returns:")
            click.echo(f"  Type: {return_type}")
            click.echo()

    # Show BaseModel schemas if any
    if hasattr(cmd, "models") and cmd.models:
        click.echo("Models:")
        for model_name, model_info in cmd.models.items():
            click.echo(f"\n{model_name}:")
            if model_info.get("description"):
                click.echo(f"  {model_info['description'].strip()}")

            # Show fields
            for field_name, field_info in model_info.get("fields", {}).items():
                required = "required" if field_info.get("required") else "optional"
                field_type = field_info.get("type", "Any")
                description = field_info.get("description", "")

                line = f"  - {field_name} ({field_type}, {required})"
                if description:
                    line += f": {description}"

                # Add constraints if any
                constraints = field_info.get("constraints", {})
                if constraints:
                    constraint_strs = []
                    for key, value in constraints.items():
                        if key == "min_length":
                            constraint_strs.append(f"min length: {value}")
                        elif key == "max_length":
                            constraint_strs.append(f"max length: {value}")
                        elif key == "ge":
                            constraint_strs.append(f">= {value}")
                        elif key == "gt":
                            constraint_strs.append(f"> {value}")
                        elif key == "le":
                            constraint_strs.append(f"<= {value}")
                        elif key == "lt":
                            constraint_strs.append(f"< {value}")
                        elif key == "max_items":
                            constraint_strs.append(f"max items: {value}")
                        elif key == "min_items":
                            constraint_strs.append(f"min items: {value}")
                    if constraint_strs:
                        line += f" [{', '.join(constraint_strs)}]"

                click.echo(line)
        click.echo()


def collect_all_models(runpy_instance: "Runpy") -> Dict[str, Type]:
    """Collect all Pydantic models used in registered functions"""
    all_models = {}

    # Check all registered functions
    for cmd_name, func in runpy_instance.functions.items():
        models = get_pydantic_models_from_function(func)
        all_models.update(models)

    return all_models


def display_models(models: Dict[str, Type]) -> None:
    """Display Pydantic model schemas"""
    for model_name, model_type in models.items():
        schema = get_model_schema(model_type)
        click.echo(f"### {model_name}")
        if schema.get("description"):
            # Strip and clean the description
            desc = schema["description"].strip()
            click.echo(desc)
            click.echo()  # Add blank line after description

        # Display fields
        for field_name, field_info in schema.get("fields", {}).items():
            required = "required" if field_info.get("required") else "optional"
            field_type = field_info.get("type", "Any")
            description = field_info.get("description", "")

            line = f"**{field_name}** ({field_type}, {required})"
            if description:
                line += f": {description}"

            # Add constraints if any
            constraints = field_info.get("constraints", {})
            if constraints:
                constraint_strs = []
                for key, value in constraints.items():
                    if key == "min_length":
                        constraint_strs.append(f"min length: {value}")
                    elif key == "max_length":
                        constraint_strs.append(f"max length: {value}")
                    elif key == "ge":
                        constraint_strs.append(f">= {value}")
                    elif key == "gt":
                        constraint_strs.append(f"> {value}")
                    elif key == "le":
                        constraint_strs.append(f"<= {value}")
                    elif key == "lt":
                        constraint_strs.append(f"< {value}")
                    elif key == "max_items":
                        constraint_strs.append(f"max items: {value}")
                    elif key == "min_items":
                        constraint_strs.append(f"min items: {value}")
                if constraint_strs:
                    line += f" [{', '.join(constraint_strs)}]"

            click.echo(line)

        # Display validators if any
        validators = schema.get("validators", [])
        if validators:
            click.echo("\nValidators:")
            for validator in validators:
                click.echo(f"- {validator}")

        click.echo()
