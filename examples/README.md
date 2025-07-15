# Runpy Examples

This directory contains examples demonstrating various features of Runpy.

## Examples

### 1. Simple Calculator (`simple_calculator.py`)
A basic calculator showing fundamental Runpy usage:
- Basic function registration
- Type hints and validation
- Direct math module integration
- List parameter handling

**Usage:**
```bash
# Basic operations
python simple_calculator.py add --x 5 --y 3
python simple_calculator.py sqrt --x 16
python simple_calculator.py sum-list --numbers '[1.5, 2.5, 3.0]'

# View documentation
python simple_calculator.py docs
python simple_calculator.py docs add
```

### 2. Task Manager (`task_manager.py`)
Advanced example with Pydantic models:
- Complex data models with validation
- Enum types
- Optional parameters
- JSON/Python/TypeScript input formats
- Structured data output

**Usage:**
```bash
# Add a task (JSON format)
python task_manager.py add-task --task '{"title": "Buy groceries", "priority": "high", "tags": ["shopping", "urgent"]}'

# Add a task (Python dict format)
python task_manager.py add-task --task "{'title': 'Write report', 'priority': 'medium', 'due_date': '2024-12-31T17:00:00'}"

# List all tasks
python task_manager.py list-tasks

# Filter tasks
python task_manager.py list-tasks --filters '{"priority": "high", "completed": false}'

# Get statistics
python task_manager.py get-stats

# View documentation
python task_manager.py docs
python task_manager.py docs add-task
python task_manager.py docs --filter task
```

### 3. File Processor (`file_processor.py`)
File operations and complex return types:
- File and directory analysis
- Hash calculation
- Duplicate detection
- Optional nested models
- Error handling

**Usage:**
```bash
# Analyze a single file
python file_processor.py analyze-file --file-path "/path/to/file.txt"

# Analyze with hash calculation
python file_processor.py analyze-file --file-path "/path/to/file.txt" --options '{"calculate_hash": true, "include_content": true}'

# Analyze directory
python file_processor.py analyze-directory --dir-path "/path/to/directory" --recursive true

# Find duplicates
python file_processor.py find-duplicates --dir-path "/path/to/directory"

# Create manifest
python file_processor.py create-manifest --dir-path "/path/to/directory" --output-file "manifest.json"

# View documentation
python file_processor.py docs
python file_processor.py docs analyze-file
python file_processor.py docs --filter analyze
```

### 4. Documentation Test (`test_docs.py`)
Simple example to test docs functionality:
- Basic functions with detailed docstrings
- Pydantic model integration
- Parameter validation and examples

**Usage:**
```bash
# View all commands in tree format
python test_docs.py docs

# View specific command documentation
python test_docs.py docs greet
python test_docs.py docs create-user

# Filter commands by pattern
python test_docs.py docs --filter user

# Generate schema
python test_docs.py schema
```

## Common Features Demonstrated

### Input Formats
All examples support multiple input formats for complex parameters:

1. **JSON format** (standard):
   ```bash
   --parameter '{"key": "value", "number": 42}'
   ```

2. **Python dict format**:
   ```bash
   --parameter "{'key': 'value', 'number': 42}"
   ```

3. **TypeScript/JavaScript format**:
   ```bash
   --parameter '{key: "value", number: 42}'
   ```

### Built-in Commands
All examples automatically include:

- `docs` - View all commands in enhanced tree format with descriptions
- `docs <command>` - View detailed documentation for specific command
- `docs --filter <pattern>` - Filter commands by pattern
- `schema` - Generate OpenAPI-style schema
- `--help` - Command help

**Enhanced Documentation Features:**
The `docs` command now provides comprehensive help information including:
- Complete command descriptions from docstrings
- Full parameter lists with types and descriptions
- Required vs optional parameter indicators
- Return type information
- Pydantic model schemas with field details and constraints
- All information that `--help` shows, but for all commands at once

**Documentation Examples:**
```bash
# View all commands with enhanced details
python task_manager.py docs

# View specific command documentation
python task_manager.py docs add-task

# Filter commands by pattern
python file_processor.py docs --filter analyze

# Test enhanced docs output
python test_docs.py docs

# Generate schema
python simple_calculator.py schema
```

### Output Formatting
Examples demonstrate different output types:
- Simple values (strings, numbers)
- Lists and arrays
- Complex nested dictionaries
- Error handling with structured responses

## Running Examples

1. Make sure runpycli is installed:
   ```bash
   pip install runpycli
   ```

2. Run any example:
   ```bash
   python examples/simple_calculator.py --help
   ```

3. View available commands:
   ```bash
   python examples/task_manager.py
   ```

4. Get detailed documentation:
   ```bash
   python examples/file_processor.py docs analyze-file
   ```

5. Generate schema:
   ```bash
   python examples/task_manager.py schema --json
   ```