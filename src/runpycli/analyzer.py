"""Function analysis utilities for Runpy"""

import inspect
from typing import Callable


def analyze_function(func: Callable) -> dict:
    """Analyze a function and extract metadata
    
    Args:
        func: Function to analyze
        
    Returns:
        Dictionary containing function metadata including name, parameters,
        docstring, and other attributes
    """
    try:
        from func_analyzer import analyze_function as _external_analyze
        return _external_analyze(func)
    except ImportError:
        # Fallback implementation if func_analyzer is not available
        return _analyze_function_fallback(func)


def _analyze_function_fallback(func: Callable) -> dict:
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