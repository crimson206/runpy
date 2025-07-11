# Runpy - Convert Python Functions to CLI Commands

[![PyPI version](https://badge.fury.io/py/runpycli.svg)](https://badge.fury.io/py/runpycli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Runpy automatically converts your Python functions into command-line interfaces (CLIs) with minimal code changes. Simply decorate your functions, and Runpy generates a fully-featured CLI with argument parsing, help text, and type validation.

## Features

- 🚀 **Zero Configuration**: Convert functions to CLI commands with a single decorator
- 📝 **Automatic Help Generation**: Docstrings become help text automatically
- 🔍 **Type Validation**: Automatic type checking based on type hints
- 📊 **Rich Output**: Support for structured output (JSON, tables, etc.)
- 🏗️ **Command Groups**: Organize commands in hierarchical groups
- 🔧 **Flexible Configuration**: YAML/JSON config file support
- 📦 **Pydantic Integration**: Full support for Pydantic models as parameters
- 🌐 **Multiple Input Formats**: Accept JSON, Python dict, and TypeScript object notation
- 🎨 **Customizable**: Extensive customization options for advanced use cases

## Installation

```bash
pip install runpycli
```

## Quick Start

Create a file `mycli.py`:

```python
from runpycli import Runpy

# Create a Runpy instance
cli = Runpy()

# Register functions as commands
@cli.register
def hello(name: str = "World") -> str:
    """Say hello to someone"""
    return f"Hello, {name}!"

@cli.register
def add(x: int, y: int) -> int:
    """Add two numbers"""
    return x + y

if __name__ == "__main__":
    cli.app()
```

Run your CLI:

```bash
python mycli.py hello --name Alice
# Output: Hello, Alice!

python mycli.py add --x 5 --y 3
# Output: 8
```

## Advanced Features

### Pydantic Models as Parameters

```python
from pydantic import BaseModel, Field
from typing import List

class UserInput(BaseModel):
    """User information"""
    name: str = Field(..., description="User's full name")
    age: int = Field(..., ge=0, le=150, description="User's age")
    emails: List[str] = Field(default_factory=list, description="Email addresses")

@cli.register
def create_user(user: UserInput) -> dict:
    """Create a new user from the provided data"""
    return {"status": "created", "user": user.model_dump()}
```

Usage with multiple input formats:
```bash
# JSON format (standard)
python mycli.py create-user --user '{"name": "John Doe", "age": 30, "emails": ["john@example.com"]}'

# Python dict format
python mycli.py create-user --user "{'name': 'John Doe', 'age': 30, 'emails': ['john@example.com']}"

# TypeScript/JavaScript object format
python mycli.py create-user --user '{name: "John Doe", age: 30, emails: ["john@example.com"]}'
```

### Command Groups

```python
# Create command groups
cli = Runpy(name="myapp/db")

@cli.register
def migrate():
    """Run database migrations"""
    pass

@cli.register
def seed():
    """Seed the database"""
    pass
```

### Configuration Files

Create a `config.json`:
```json
{
  "defaults": {
    "environment": "development",
    "debug": true
  },
  "shortcuts": {
    "env": "e",
    "debug": "d"
  }
}
```

Use in your CLI:
```python
cli = Runpy(config_file="config.json")

@cli.register
def deploy(environment: str, debug: bool = False):
    """Deploy the application"""
    print(f"Deploying to {environment} (debug: {debug})")
```

### Register Multiple Functions

```python
import math

# Register all public functions from a module
cli.register_module(math)

# Or selectively register functions
cli.register(math.sin)
cli.register(math.cos)
```

## Documentation Commands

Runpy automatically adds two special commands:

### `docs` Command
View detailed documentation for any command:

```bash
python mycli.py docs create-user
```

### `schema` Command
Generate OpenAPI-style schema documentation:

```bash
python mycli.py schema
python mycli.py schema --json  # JSON output
python mycli.py schema --save api-docs.json  # Save to file
```

## Type Support

Runpy supports a wide range of Python types:

- Basic types: `str`, `int`, `float`, `bool`
- Container types: `List[T]`, `Dict[K, V]`, `Set[T]`, `Tuple[T, ...]`
- Optional types: `Optional[T]`, `Union[T1, T2]`
- Pydantic models: Any class inheriting from `pydantic.BaseModel`
- Enums: `Enum` subclasses
- File types: `Path`, `FilePath`, `DirectoryPath`

### Boolean Parameters

Boolean parameters are handled as regular options, not flags:

```bash
# Correct usage
python mycli.py command --bool-param true
python mycli.py command --bool-param false

# NOT as flags (this is not supported)
python mycli.py command --bool-param  # ❌
```

### Optional Parameters

Parameters with default values (including `None`) are automatically optional:

```python
def process(
    required_param: str,  # Required: must provide --required-param
    optional_str: Optional[str] = None,  # Optional: can omit
    optional_int: Optional[int] = None,  # Optional: can omit
    optional_with_default: str = "default"  # Optional: uses default if omitted
):
    pass
```

## Best Practices

1. **Use Type Hints**: Always add type hints to get automatic type validation
2. **Write Docstrings**: Function and parameter docstrings become help text
3. **Set Defaults**: Default values make parameters optional
4. **Return Values**: Return values are automatically displayed
5. **Use Pydantic**: For complex inputs, Pydantic models provide validation

## Examples

### Simple Calculator

```python
from runpycli import Runpy
import math

cli = Runpy(name="calc", version="1.0.0")

cli.register(math.sin)
cli.register(math.cos)
cli.register(math.sqrt)

@cli.register
def divide(x: float, y: float) -> float:
    """Divide x by y"""
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y

if __name__ == "__main__":
    cli.app()
```

### Task Manager

```python
from runpycli import Runpy
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

cli = Runpy(name="tasks")

class Task(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: List[str] = []

tasks_db = []

@cli.register
def add(task: Task) -> dict:
    """Add a new task"""
    task_dict = task.model_dump()
    task_dict["id"] = len(tasks_db) + 1
    tasks_db.append(task_dict)
    return task_dict

@cli.register
def list_tasks(tag: Optional[str] = None) -> List[dict]:
    """List all tasks, optionally filtered by tag"""
    if tag:
        return [t for t in tasks_db if tag in t.get("tags", [])]
    return tasks_db

if __name__ == "__main__":
    cli.app()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [PyPI Package](https://pypi.org/project/runpycli/)
- [GitHub Repository](https://github.com/crimson206/runpy)
- [Documentation](https://github.com/crimson206/runpy/wiki)
- [Issue Tracker](https://github.com/crimson206/runpy/issues)