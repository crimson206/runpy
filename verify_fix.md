# Optional Parameter Bug Fix

## Problem
`Optional[T] = None` parameters were incorrectly treated as required in the CLI.

## Root Cause
In `core.py` line 265, the original code:
```python
is_required = default is None and param_info["kind"] != "VAR_POSITIONAL"
```

This made any parameter with `default=None` required, even if it was `Optional[T] = None`.

## Solution
Modified the logic to check if the parameter has a default value in the function signature:
```python
# Check if parameter has a default value (even if it's None)
import inspect
has_default = False
func = self.functions.get(command.name)
if func:
    sig = inspect.signature(func)
    if param_name in sig.parameters:
        param = sig.parameters[param_name]
        has_default = param.default != inspect.Parameter.empty

# If parameter has a default value (including None), it's optional
is_required = not has_default and param_info["kind"] != "VAR_POSITIONAL"
```

## Expected Behavior After Fix
- `func(arg1: Optional[str] = None)` → `--arg1` is optional
- `func(arg2: Optional[int] = None)` → `--arg2` is optional  
- `func(arg3: str = None)` → `--arg3` is optional
- `func(arg4: str)` → `--arg4` is required

## Test Cases
The fix should make all tests in `test_cli_invoke.py` pass, especially:
- `test_optional_argument_not_provided()` 
- `test_multiple_optional_arguments()`