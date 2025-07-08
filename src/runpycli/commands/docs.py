"""Documentation command for Runpy"""

import click
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Runpy


def add_docs_command(runpy_instance: "Runpy") -> None:
    """Add the built-in docs command to a Runpy instance"""
    @click.command(name="docs", help="View command documentation and help")
    @click.argument("commands", nargs=-1, required=False)
    @click.option("--filter", "-f", help="Filter commands by pattern")
    @click.option("--export", "-e", type=click.Choice(["markdown", "html", "man"]), help="Export documentation format")
    def docs_command(commands, filter, export):
        """Show documentation for commands"""
        if export:
            export_docs(runpy_instance, export)
        elif commands:
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
            
            # Get the command's help
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




def export_docs(runpy_instance: "Runpy", format: str) -> None:
    """Export documentation in specified format"""
    if format == "markdown":
        content = generate_markdown_docs(runpy_instance)
        click.echo(content)
    elif format == "html":
        content = generate_html_docs(runpy_instance)
        click.echo(content)
    elif format == "man":
        content = generate_man_docs(runpy_instance)
        click.echo(content)


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
            collect_docs_tree(cmd, tree, f"{path}/{cmd_name}" if path else cmd_name)
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


def print_docs_tree(tree: dict, prefix: str = "", is_last: bool = True) -> None:
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
            print_docs_tree(info, f"{prefix}{sub_prefix}", True)


def filter_docs_tree(tree: dict, pattern: str) -> dict:
    """Filter the docs tree by pattern"""
    filtered = {"commands": {}, "groups": {}}
    
    # Filter commands
    for name, doc in tree["commands"].items():
        if pattern.lower() in name.lower() or pattern.lower() in doc.get("summary", "").lower():
            filtered["commands"][name] = doc
    
    # Filter groups recursively
    for name, info in tree["groups"].items():
        filtered_group = filter_docs_tree(info, pattern)
        
        # Include group if it has matching commands or subgroups, or if the group name matches
        if (filtered_group["commands"] or filtered_group["groups"] or 
            pattern.lower() in name.lower()):
            filtered["groups"][name] = {
                "commands": filtered_group["commands"],
                "groups": filtered_group["groups"],
                "help": info.get("help", "")
            }
    
    return filtered


def find_command_by_path(runpy_instance: "Runpy", path: str) -> click.Command:
    """Find a command by its path (e.g., 'group/subcommand')"""
    parts = path.split("/")
    current = runpy_instance.app
    
    for part in parts:
        if hasattr(current, 'commands') and part in current.commands:
            current = current.commands[part]
        else:
            return None
    
    return current if isinstance(current, click.Command) else None


def generate_markdown_docs(runpy_instance: "Runpy") -> str:
    """Generate markdown documentation"""
    lines = [f"# {runpy_instance.name} Documentation"]
    
    if runpy_instance.version:
        lines.append(f"\nVersion: {runpy_instance.version}")
    
    lines.append("\n## Commands\n")
    
    docs_tree = build_docs_tree(runpy_instance)
    markdown_docs_tree(docs_tree, lines)
    
    return "\n".join(lines)


def generate_html_docs(runpy_instance: "Runpy") -> str:
    """Generate HTML documentation"""
    lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        f"<title>{runpy_instance.name} Documentation</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 40px; }",
        "h1, h2, h3 { color: #333; }",
        ".command { margin: 20px 0; }",
        ".summary { color: #666; font-style: italic; }",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{runpy_instance.name} Documentation</h1>"
    ]
    
    if runpy_instance.version:
        lines.append(f"<p>Version: {runpy_instance.version}</p>")
    
    lines.append("<h2>Commands</h2>")
    
    # Add commands content here
    docs_tree = build_docs_tree(runpy_instance)
    html_docs_tree(docs_tree, lines)
    
    lines.extend(["</body>", "</html>"])
    
    return "\n".join(lines)


def generate_man_docs(runpy_instance: "Runpy") -> str:
    """Generate man page documentation"""
    lines = [
        f".TH {runpy_instance.name.upper()} 1",
        f".SH NAME",
        f"{runpy_instance.name} - Convert Python functions to CLI commands automatically",
        f".SH SYNOPSIS",
        f".B {runpy_instance.name}",
        f"[\\fIcommand\\fR] [\\fIoptions\\fR]",
        f".SH DESCRIPTION",
        f"{runpy_instance.name} automatically converts Python functions into command-line interface commands.",
        f".SH COMMANDS"
    ]
    
    # Add commands in man page format
    docs_tree = build_docs_tree(runpy_instance)
    man_docs_tree(docs_tree, lines)
    
    return "\n".join(lines)


def markdown_docs_tree(tree: dict, lines: list, level: int = 3) -> None:
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
        markdown_docs_tree(info, lines, level + 1)


def html_docs_tree(tree: dict, lines: list, level: int = 3) -> None:
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
        html_docs_tree(info, lines, level + 1)


def man_docs_tree(tree: dict, lines: list) -> None:
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
        man_docs_tree(info, lines)