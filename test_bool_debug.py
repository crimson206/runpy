"""Debug boolean parameter type detection"""

import sys
sys.path.insert(0, 'src')

from typing import Optional
import inspect

def test_func(arg3: Optional[bool] = False) -> str:
    return f"arg3={arg3}"

# Check how the type annotation appears
sig = inspect.signature(test_func)
param = sig.parameters['arg3']

print(f"Parameter: {param.name}")
print(f"Annotation: {param.annotation}")
print(f"Annotation str: {str(param.annotation)}")
print(f"Default: {param.default}")
print(f"Has default: {param.default != inspect.Parameter.empty}")

# Check what func_analyzer would return
from func_analyzer import analyze_function

func_info = analyze_function(test_func)
for param_info in func_info['parameters']:
    if param_info['name'] == 'arg3':
        print(f"\nfunc_analyzer result:")
        print(f"Name: {param_info['name']}")
        print(f"Annotation: {param_info['annotation']}")
        print(f"Default: {param_info['default']}")
        print(f"Kind: {param_info['kind']}")