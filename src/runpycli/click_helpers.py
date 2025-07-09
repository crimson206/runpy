"""Click framework helper utilities"""

import click
from typing import Any, Optional


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
            if self.transform_underscore_to_dash and "_" in cmd_name:
                # Suggest dash version
                dash_version = cmd_name.replace("_", "-")
                if dash_version in self.commands:
                    ctx.fail(
                        f"No such command '{cmd_name}'. Did you mean '{dash_version}'?"
                    )
            elif self.transform_underscore_to_dash and "-" in cmd_name:
                # Check if underscore version was registered
                underscore_version = cmd_name.replace("-", "_")
                if any(
                    orig_name.replace("_", "-") == cmd_name
                    for orig_name in self.commands
                ):
                    ctx.fail(
                        f"No such command '{cmd_name}'. This CLI uses dashes instead of underscores."
                    )

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
    annotation = (
        annotation.replace("typing.", "").replace("<class '", "").replace("'>", "")
    )

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


class RunpyCommand(click.Command):
    """Custom Click Command with enhanced help for BaseModel parameters"""

    def __init__(
        self,
        *args,
        models: Optional[dict] = None,
        func_info: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.models = models or {}
        self.func_info = func_info or {}

    def format_help(self, ctx, formatter):
        """Override to add BaseModel documentation and return type info"""
        # First, get the standard help
        super().format_help(ctx, formatter)

        # Add return type information if available
        if self.func_info:
            return_annotation = self.func_info.get("return_annotation")
            # Skip if no return type, or it's None/inspect._empty
            if (
                return_annotation
                and return_annotation != "None"
                and "inspect._empty" not in str(return_annotation)
            ):

                formatter.write("\n")
                with formatter.section("Returns"):
                    # Check if we have a description from docstring
                    docstring = self.func_info.get("docstring", "")
                    if docstring and "Returns:" in docstring:
                        # Extract returns description from docstring
                        lines = docstring.split("\n")
                        in_returns = False
                        for line in lines:
                            if line.strip().startswith("Returns:"):
                                in_returns = True
                                continue
                            if in_returns and line.strip() and not line.startswith(" "):
                                break
                            if in_returns and line.strip():
                                formatter.write_text(line.strip())
                    else:
                        formatter.write_text(f"Type: {return_annotation}")

        # If we have models, add them to the help
        if self.models:
            formatter.write("\n")
            with formatter.section("Models"):
                for model_name, model_info in self.models.items():
                    formatter.write_text(f"{model_name}:")
                    if model_info.get("description"):
                        formatter.write_text(model_info["description"])

                    # Write fields
                    for field_name, field_info in model_info.get("fields", {}).items():
                        required = (
                            "required" if field_info.get("required") else "optional"
                        )
                        field_type = field_info.get("type", "Any")
                        description = field_info.get("description", "")

                        line = f"- {field_name} ({field_type}, {required})"
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

                        formatter.write_text(line)

                    formatter.write_text("")
