"""Click framework helper utilities"""

import click
from typing import Any


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


def get_click_type(type_annotation: str) -> Any:
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


def get_param_type_string(click_type) -> str:
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


def get_schema_type_from_annotation(annotation: str) -> str:
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
        return get_schema_type_from_annotation(inner)
    elif annotation.startswith("Union["):
        return "union"
    elif annotation.startswith("Literal["):
        return "literal"
    elif "BaseModel" in annotation or annotation[0].isupper():
        # Likely a Pydantic model or custom class
        return "object"
    else:
        return "string"