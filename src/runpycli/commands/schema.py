"""Schema generation command for Runpy"""

import click
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Runpy

from ..click_helpers import get_param_type_string, get_schema_type_from_annotation


def add_schema_command(runpy_instance: "Runpy") -> None:
    """Add the built-in schema command to a Runpy instance"""

    @click.command(
        name="schema", help="Generate API-style documentation for all commands"
    )
    @click.option(
        "--format",
        type=click.Choice(["json", "yaml", "markdown"]),
        default="json",
        help="Output format",
    )
    def schema_command(format: str):
        """Generate and display schema for all registered commands"""
        schema = generate_schema(runpy_instance)

        if format == "json":
            click.echo(json.dumps(schema, indent=2))
        elif format == "yaml":
            # Simple YAML-like output (without external dependency)
            click.echo(schema_to_yaml(schema))
        elif format == "markdown":
            click.echo(schema_to_markdown(schema))

    runpy_instance.app.add_command(schema_command)


def generate_schema(runpy_instance: "Runpy") -> dict:
    """Generate schema for all registered commands"""
    schema = {
        "name": runpy_instance.name,
        "version": runpy_instance.version,
        "commands": {},
        "groups": {},
    }

    # Process all commands in the app
    collect_commands(runpy_instance.app, schema, runpy_instance)

    return schema


def collect_commands(
    group: click.Group, schema: dict, runpy_instance: "Runpy", path: str = ""
) -> None:
    """Recursively collect all commands and groups"""
    for cmd_name, cmd in group.commands.items():
        # Skip built-in commands
        if cmd_name in ["schema", "docs"]:
            continue
        if isinstance(cmd, click.Group):
            # It's a group
            group_schema = {
                "description": cmd.help or f"{cmd_name} commands",
                "commands": {},
                "groups": {},
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
            collect_commands(
                cmd, schema, runpy_instance, f"{path}/{cmd_name}" if path else cmd_name
            )
        else:
            # It's a command
            cmd_schema = get_command_schema(cmd, cmd_name, path, runpy_instance)
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


def get_command_schema(
    cmd: click.Command, cmd_name: str, path: str, runpy_instance: "Runpy"
) -> dict:
    """Get schema for a single command"""
    cmd_schema = {"description": cmd.help or "", "parameters": {}}

    # Try to get original function info
    # For grouped commands, check with full path
    if path:
        func_info = runpy_instance.function_info.get(f"{path}/{cmd_name}")
    else:
        func_info = runpy_instance.function_info.get(cmd_name)

    # Get parameter information
    for param in cmd.params:
        param_schema = {}

        if isinstance(param, click.Option):
            param_name = param.name

            # Try to get original type from function info
            if func_info:
                for p in func_info["parameters"]:
                    if p["name"] == param_name:
                        param_schema["type"] = get_schema_type_from_annotation(
                            p["annotation"]
                        )
                        break
                else:
                    param_schema["type"] = get_param_type_string(param.type)
            else:
                param_schema["type"] = get_param_type_string(param.type)

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
                if hasattr(param.default, "value"):
                    param_schema["default"] = param.default.value
                else:
                    param_schema["default"] = param.default
            else:
                param_schema["default"] = None
            param_schema["help"] = param.help or ""

            # Check for shortcuts - consider path for grouped commands
            shortcut_key = f"{path}/{cmd_name}" if path else cmd_name
            if (
                shortcut_key in runpy_instance.shortcuts
                and param_name in runpy_instance.shortcuts[shortcut_key]
            ):
                param_schema["shortcut"] = runpy_instance.shortcuts[shortcut_key][
                    param_name
                ]

            # Check if it's a flag
            if param.is_flag:
                param_schema["type"] = "boolean"
                param_schema["is_flag"] = True

            cmd_schema["parameters"][param_name] = param_schema
        elif isinstance(param, click.Argument):
            param_schema["type"] = get_param_type_string(param.type)
            param_schema["required"] = param.required
            param_schema["multiple"] = param.nargs == -1
            cmd_schema["parameters"][param.name] = param_schema

    return cmd_schema


def schema_to_yaml(schema: dict, indent: int = 0) -> str:
    """Convert schema to YAML-like format"""
    lines = []
    indent_str = "  " * indent

    for key, value in schema.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(schema_to_yaml(value, indent + 1))
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


def schema_to_markdown(schema: dict) -> str:
    """Convert schema to Markdown format"""
    lines = [f"# {schema['name']} CLI Documentation"]

    if schema.get("version"):
        lines.append(f"\nVersion: {schema['version']}")

    # Top-level commands
    if schema.get("commands"):
        lines.append("\n# Commands\n")
        for cmd_name, cmd_info in schema["commands"].items():
            lines.append(f"## {cmd_name}")
            lines.append(f"\n{cmd_info['description']}\n")

            if cmd_info.get("parameters"):
                lines.append("### Parameters\n")
                for param_name, param_info in cmd_info["parameters"].items():
                    param_line = f"- `--{param_name}`"
                    if param_info.get("shortcut"):
                        param_line += f" / `-{param_info['shortcut']}`"
                    param_line += f" ({param_info['type']})"
                    if not param_info.get("required", True):
                        param_line += " [optional]"
                    if param_info.get("default") is not None:
                        param_line += f" - default: {param_info['default']}"
                    lines.append(param_line)
                    if param_info.get("help"):
                        lines.append(f"  - {param_info['help']}")

    # Groups
    if schema.get("groups"):
        lines.append("\n# Command Groups\n")
        markdown_groups(schema["groups"], lines)

    return "\n".join(lines)


def markdown_groups(groups: dict, lines: list, level: int = 2) -> None:
    """Recursively add groups to markdown"""
    for group_name, group_info in groups.items():
        lines.append(f"\n{'#' * level} {group_name}")
        lines.append(f"\n{group_info.get('description', '')}\n")

        # Commands in this group
        if group_info.get("commands"):
            for cmd_name, cmd_info in group_info["commands"].items():
                lines.append(f"\n{'#' * (level + 1)} {cmd_name}")
                lines.append(f"\n{cmd_info['description']}\n")

                if cmd_info.get("parameters"):
                    lines.append("Parameters:\n")
                    for param_name, param_info in cmd_info["parameters"].items():
                        param_line = f"- `--{param_name}`"
                        if param_info.get("shortcut"):
                            param_line += f" / `-{param_info['shortcut']}`"
                        param_line += f" ({param_info['type']})"
                        if not param_info.get("required", True):
                            param_line += " [optional]"
                        lines.append(param_line)

        # Nested groups
        if group_info.get("groups"):
            markdown_groups(group_info["groups"], lines, level + 1)
