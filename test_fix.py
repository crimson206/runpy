#!/usr/bin/env python3
"""Quick test to verify the Optional parameter fix"""

import sys
sys.path.insert(0, 'src')

from typing import Optional
from runpycli import Runpy

def test_func(arg1: Optional[str] = None, arg2: Optional[int] = None) -> str:
    return f"arg1={arg1}, arg2={arg2}"

# Create CLI and register function
cli = Runpy("testcli")
cli.register(test_func)

# This should work now without requiring --arg1 or --arg2
if __name__ == "__main__":
    cli.app()