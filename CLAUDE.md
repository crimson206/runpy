# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Miniature is a Python package for managing local git repositories and publishing packages with version tagging. It provides functions to load packages from local git repositories with version control and publish packages with automatic tagging.

## Essential Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_load.py

# Run with verbose output
pytest -v
```

### Development
```bash
# Install package in development mode
pip install -e .

# Install with dependencies (pyshell and packaging are required but not in pyproject.toml)
pip install pyshell packaging runpycli gitpython
```

### CLI Usage
```bash
# Using the CLI
miniature --help

# Load package from repository
miniature load --repo https://github.com/user/repo --version latest

# Load from configuration file
miniature load-from-file --config-file pkg.json

# Publish package
miniature publish --message "Update package"

# Manage cache
miniature cache-list
miniature cache-clear
```

## Architecture

### Core Modules
- **`src/miniature/load.py`**: Package loading functionality
  - `load_pkg()`: Load single package from local git repo
  - `load_pkgs_from_file()`: Batch load packages from config
  
- **`src/miniature/publish.py`**: Package publishing functionality  
  - `publish_pkg()`: Publish package with optional tagging/pushing
  
- **`src/miniature/push.py`**: Git push operations
  - `push_pkg()`: Push package changes to repository
  
- **`src/miniature/tag.py`**: Git tagging functionality
  - `tag_pkg()`: Create and manage version tags

- **`src/miniature/cache.py`**: Repository cache management
  - `RepositoryCache`: Manages local cache of git repositories
  - `get_cache()`: Get global cache instance

- **`src/miniature/cli.py`**: CLI interface using runpycli
  - Exposes all main functions as CLI commands

### Configuration Files
1. **`pkg.json`**: Package metadata with dependencies array (new format)
2. **`miniature.json/repotree.json`**: Legacy configuration with miniatures array
3. **Cache**: `~/.miniature/cache/` for repository caching

### Key Design Patterns
- All functions return structured dictionaries with `success`, `message`, and relevant data
- Repository caching system replaces gitdbs.json configuration
- Version specifications support exact versions, "latest", and semantic version constraints
- Uses GitPython for Git operations instead of shell commands
- CLI commands automatically generated from function signatures

## Important Notes
- Dependencies: `runpycli`, `pyshell`, `packaging`, `gitpython`
- Repository caching system for better performance
- Supports multiple configuration formats for backward compatibility
- CLI integration with runpycli for zero-config command exposure
- Current branch is `newbranch/mypkg.py`, main branch is `main`

## Configuration Formats

### New pkg.json format (with dependencies)
```json
{
  "name": "project-name",
  "version": "1.0.0",
  "dependencies": [
    {
      "pkgName": "package-name",
      "domain": "https://github.com/",
      "repoName": "user/repo",
      "pathName": "path/to/package",
      "branch": "main",
      "localDir": "local-directory",
      "version": ">=1.0.0"
    }
  ]
}
```

### Legacy miniature.json format
```json
{
  "miniatures": [
    {
      "pkgName": "package-name",
      "domain": "https://github.com/",
      "repoName": "user/repo",
      "pathName": "path/to/package",
      "branch": "main",
      "localDir": "local-directory",
      "loaded": true
    }
  ]
}
```

## Recent Changes
- Updated to use repository cache system instead of gitdbs.json
- Added CLI interface with runpycli
- Fixed default target directory to use repository name instead of current directory
- Support for new pkg.json format with dependencies array
- Backward compatibility with existing configuration formats