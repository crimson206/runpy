#!/usr/bin/env python3
"""
Simple Calculator Example - Basic Runpy Usage

This example demonstrates how to create a simple calculator CLI using Runpy.
It shows basic function registration and type handling.
"""

from runpycli import Runpy
import math
from typing import List

# Create Runpy instance
cli = Runpy(name="calc", version="1.0.0")

# Register basic math functions
@cli.register
def add(x: float, y: float) -> float:
    """Add two numbers together
    
    Args:
        x: First number to add
        y: Second number to add
        
    Returns:
        The sum of x and y
        
    Example:
        calc add --x 5 --y 3
        # Output: 8.0
    """
    return x + y

@cli.register
def subtract(x: float, y: float) -> float:
    """Subtract y from x"""
    return x - y

@cli.register
def multiply(x: float, y: float) -> float:
    """Multiply two numbers"""
    return x * y

@cli.register
def divide(x: float, y: float) -> float:
    """Divide x by y"""
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y

@cli.register
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent"""
    return base ** exponent

@cli.register
def sqrt(x: float) -> float:
    """Calculate square root of x"""
    if x < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return math.sqrt(x)

@cli.register
def sum_list(numbers: List[float]) -> float:
    """Calculate sum of a list of numbers
    
    Args:
        numbers: List of numbers to sum
        
    Returns:
        The total sum of all numbers
        
    Example:
        calc sum-list --numbers '[1.5, 2.5, 3.0]'
        # Output: 7.0
    """
    return sum(numbers)

@cli.register
def factorial(n: int) -> int:
    """Calculate factorial of n"""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    return math.factorial(n)

# Register some math module functions directly
cli.register(math.sin, name="sin")
cli.register(math.cos, name="cos")
cli.register(math.tan, name="tan")
cli.register(math.log, name="log")

if __name__ == "__main__":
    cli.app()