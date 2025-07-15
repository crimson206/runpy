#!/usr/bin/env python3
"""
Test script to demonstrate docs command functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from runpycli import Runpy
from pydantic import BaseModel, Field
from typing import Optional

# Create test CLI
cli = Runpy(name="test-docs", version="1.0.0")

class UserInfo(BaseModel):
    """User information model for testing docs"""
    name: str = Field(..., min_length=1, max_length=50, description="User's full name")
    age: int = Field(..., ge=0, le=150, description="User's age in years")
    email: Optional[str] = Field(None, description="User's email address")

@cli.register
def greet(name: str, greeting: str = "Hello") -> str:
    """Greet a user with a custom message
    
    This is a simple greeting function that demonstrates basic
    parameter handling and default values.
    
    Args:
        name: The name of the person to greet
        greeting: The greeting message to use (default: "Hello")
        
    Returns:
        A formatted greeting string
        
    Example:
        test-docs greet --name "Alice"
        test-docs greet --name "Bob" --greeting "Hi"
    """
    return f"{greeting}, {name}!"

@cli.register
def create_user(user: UserInfo) -> dict:
    """Create a new user with validation
    
    Creates a user object with validated input data. Demonstrates
    Pydantic model integration with detailed field validation.
    
    Args:
        user: User information object with name, age, and optional email
        
    Returns:
        Dictionary containing the created user data and status
        
    Example:
        test-docs create-user --user '{"name": "Alice", "age": 30}'
    """
    return {
        "status": "success",
        "user": user.model_dump(),
        "message": f"User {user.name} created successfully"
    }

@cli.register  
def calculate(x: float, y: float, operation: str = "add") -> float:
    """Perform basic mathematical operations
    
    This function supports four basic arithmetic operations: addition, subtraction, 
    multiplication, and division. The operation parameter determines which 
    calculation to perform on the two input numbers.
    
    Args:
        x: First number for the calculation
        y: Second number for the calculation  
        operation: Type of operation to perform (add, subtract, multiply, divide)
        
    Returns:
        Result of the mathematical operation as a float
        
    Example:
        test-docs calculate --x 10 --y 5 --operation "multiply"
        # Output: 50.0
    """
    if operation == "add":
        return x + y
    elif operation == "subtract":
        return x - y
    elif operation == "multiply":
        return x * y
    elif operation == "divide":
        if y == 0:
            raise ValueError("Cannot divide by zero")
        return x / y
    else:
        raise ValueError(f"Unknown operation: {operation}")

if __name__ == "__main__":
    print("=== Testing docs command ===")
    print("\nTry these commands:")
    print("python test_docs.py docs")
    print("python test_docs.py docs greet")
    print("python test_docs.py docs create-user")
    print("python test_docs.py docs --filter user")
    print("python test_docs.py schema")
    print("\n" + "="*50)
    
    cli.app()