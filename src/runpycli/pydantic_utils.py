"""Utilities for handling Pydantic BaseModel in Runpy"""

import inspect
from typing import Any, Dict, List, Optional, Type, get_type_hints, get_origin, get_args
from functools import lru_cache

try:
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo

    PYDANTIC_AVAILABLE = True
except ImportError:
    BaseModel = None
    FieldInfo = None
    PYDANTIC_AVAILABLE = False


def is_pydantic_model(type_hint: Any) -> bool:
    """Check if a type hint is a Pydantic BaseModel"""
    if not PYDANTIC_AVAILABLE:
        return False

    # Handle string annotations
    if isinstance(type_hint, str):
        return False

    # Direct check
    try:
        return inspect.isclass(type_hint) and issubclass(type_hint, BaseModel)
    except (TypeError, AttributeError):
        return False


def get_pydantic_models_from_function(func: callable) -> Dict[str, Type[BaseModel]]:
    """Extract all Pydantic models used in a function's signature"""
    if not PYDANTIC_AVAILABLE:
        return {}

    models = {}

    try:
        # Get type hints
        hints = get_type_hints(func)

        # Check parameters
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param.annotation != param.empty:
                type_hint = hints.get(param_name, param.annotation)
                _collect_models_from_type(type_hint, models)

        # Check return type
        if sig.return_annotation != sig.empty:
            return_hint = hints.get("return", sig.return_annotation)
            _collect_models_from_type(return_hint, models)

    except Exception:
        # If we can't get type hints, return empty
        pass

    return models


def _collect_models_from_type(
    type_hint: Any, models: Dict[str, Type[BaseModel]]
) -> None:
    """Recursively collect Pydantic models from a type hint"""
    if is_pydantic_model(type_hint):
        models[type_hint.__name__] = type_hint
        # Check fields for nested models
        for field_name, field_info in type_hint.model_fields.items():
            _collect_models_from_type(field_info.annotation, models)

    # Check generic types (List, Optional, etc.)
    origin = get_origin(type_hint)
    if origin:
        args = get_args(type_hint)
        for arg in args:
            _collect_models_from_type(arg, models)


@lru_cache(maxsize=128)
def get_model_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """Get schema information for a Pydantic model"""
    if not PYDANTIC_AVAILABLE or not is_pydantic_model(model):
        return {}

    schema = {"name": model.__name__, "description": model.__doc__ or "", "fields": {}}

    # Process fields
    for field_name, field_info in model.model_fields.items():
        field_schema = {
            "type": _get_field_type_string(field_info.annotation),
            "required": field_info.is_required(),
            "description": field_info.description or "",
            "default": field_info.default if field_info.default is not None else None,
        }

        # Add constraints if any
        constraints = _get_field_constraints(field_info)
        if constraints:
            field_schema["constraints"] = constraints

        # Check if it's a nested model
        if is_pydantic_model(field_info.annotation):
            field_schema["model"] = field_info.annotation.__name__

        schema["fields"][field_name] = field_schema

    # Get validators if any
    validators = _get_model_validators(model)
    if validators:
        schema["validators"] = validators

    return schema


def _get_field_type_string(type_hint: Any) -> str:
    """Convert a type hint to a readable string"""
    if type_hint is type(None):
        return "None"

    # Handle basic types
    if type_hint in (str, int, float, bool):
        return type_hint.__name__

    # Handle Optional
    origin = get_origin(type_hint)
    if origin is Union:
        args = get_args(type_hint)
        # Check if it's Optional (Union with None)
        if type(None) in args:
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return f"Optional[{_get_field_type_string(non_none_args[0])}]"
        return f"Union[{', '.join(_get_field_type_string(arg) for arg in args)}]"

    # Handle List, Dict, etc.
    if origin:
        args = get_args(type_hint)
        if args:
            arg_strs = [_get_field_type_string(arg) for arg in args]
            return f"{origin.__name__}[{', '.join(arg_strs)}]"
        return origin.__name__

    # Handle Pydantic models
    if is_pydantic_model(type_hint):
        return type_hint.__name__

    # Handle Literal
    if (
        hasattr(type_hint, "__class__")
        and type_hint.__class__.__name__ == "_LiteralGenericAlias"
    ):
        args = get_args(type_hint)
        return f"Literal[{', '.join(repr(arg) for arg in args)}]"

    # Default: try to get a readable name
    if hasattr(type_hint, "__name__"):
        return type_hint.__name__

    return str(type_hint)


def _get_field_constraints(field_info: FieldInfo) -> Dict[str, Any]:
    """Extract constraints from a Pydantic field"""
    constraints = {}

    # In Pydantic v2, constraints are stored in metadata
    if hasattr(field_info, "metadata"):
        for metadata in field_info.metadata:
            # Check for various constraint types
            if hasattr(metadata, "min_length"):
                constraints["min_length"] = metadata.min_length
            elif hasattr(metadata, "max_length"):
                constraints["max_length"] = metadata.max_length
            elif hasattr(metadata, "ge"):
                constraints["ge"] = metadata.ge
            elif hasattr(metadata, "gt"):
                constraints["gt"] = metadata.gt
            elif hasattr(metadata, "le"):
                constraints["le"] = metadata.le
            elif hasattr(metadata, "lt"):
                constraints["lt"] = metadata.lt
            elif hasattr(metadata, "max_items"):
                constraints["max_items"] = metadata.max_items
            elif hasattr(metadata, "min_items"):
                constraints["min_items"] = metadata.min_items

    # For backwards compatibility, also check direct attributes
    for attr in [
        "min_length",
        "max_length",
        "ge",
        "gt",
        "le",
        "lt",
        "max_items",
        "min_items",
    ]:
        if hasattr(field_info, attr):
            value = getattr(field_info, attr, None)
            if value is not None:
                constraints[attr] = value

    return constraints


def _get_model_validators(model: Type[BaseModel]) -> List[str]:
    """Get validator descriptions from a model"""
    validators = []

    # Check for validator methods
    for name, method in inspect.getmembers(model):
        if hasattr(method, "__validator_config__"):
            # Get the docstring as description
            if method.__doc__:
                validators.append(method.__doc__.strip())

    return validators


def generate_example_dict(model: Type[BaseModel]) -> Dict[str, Any]:
    """Generate an example dictionary from a Pydantic model"""
    if not PYDANTIC_AVAILABLE or not is_pydantic_model(model):
        return {}

    example = {}

    for field_name, field_info in model.model_fields.items():
        # Use example if provided
        if hasattr(field_info, "example") and field_info.example is not None:
            example[field_name] = field_info.example
        # Use default if provided
        elif field_info.default is not None:
            example[field_name] = field_info.default
        # Use default_factory if provided
        elif field_info.default_factory is not None:
            example[field_name] = field_info.default_factory()
        # Generate based on type
        else:
            example[field_name] = _generate_example_for_type(field_info.annotation)

    return example


def _generate_example_for_type(type_hint: Any) -> Any:
    """Generate an example value for a given type"""
    # Basic types
    if type_hint is str:
        return "string"
    elif type_hint is int:
        return 0
    elif type_hint is float:
        return 0.0
    elif type_hint is bool:
        return False

    # Handle Optional
    origin = get_origin(type_hint)
    if origin is Union:
        args = get_args(type_hint)
        # For Optional, use the non-None type
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            return _generate_example_for_type(non_none_args[0])

    # Handle List
    if origin is list:
        args = get_args(type_hint)
        if args:
            return [_generate_example_for_type(args[0])]
        return []

    # Handle Dict
    if origin is dict:
        return {}

    # Handle Literal
    if (
        hasattr(type_hint, "__class__")
        and type_hint.__class__.__name__ == "_LiteralGenericAlias"
    ):
        args = get_args(type_hint)
        return args[0] if args else None

    # Handle Pydantic models
    if is_pydantic_model(type_hint):
        return generate_example_dict(type_hint)

    return None


# Import Union for Optional handling
try:
    from typing import Union
except ImportError:
    Union = None
