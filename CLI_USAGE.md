# Miniature CLI Usage Guide

After installing miniature with `pip install -e .`, you can use the CLI commands:

## Available Commands

### 1. Load Package
```bash
# Load a repository from git
miniature load --repo https://github.com/user/repo --version latest

# Load to specific directory
miniature load --repo https://github.com/user/repo --target-dir my-repo

# Load from specific branch
miniature load --repo https://github.com/user/repo --branch dev

# Load experimental branch to different folder
miniature load --repo https://github.com/user/repo --branch experimental
```

### 2. Load from Configuration File
```bash
# Load all packages from pkg.json
miniature load-from-file --config-file pkg.json

# Load specific packages
miniature load-from-file --config-file pkg.json --packages "package1,package2"

# Clean existing directories before loading
miniature load-from-file --config-file pkg.json --clean
```

### 3. Publish Package
```bash
# Publish current directory
miniature publish

# Publish specific directory with custom message
miniature publish --pkg-dir ./my-package --message "Add new feature"

# Publish without tagging
miniature publish --no-tag

# Force overwrite existing tag
miniature publish --force-tag
```

### 4. Tag Package
```bash
# Create version tag
miniature tag-package

# Force overwrite existing tag
miniature tag-package --force

# Tag without pushing to remote
miniature tag-package --no-push
```

### 5. Push Package
```bash
# Push package changes (without tagging)
miniature push

# Push with custom message
miniature push --message "Update documentation"

# Commit only, don't push to remote
miniature push --no-push-remote
```

### 6. Cache Management
```bash
# List cached repositories
miniature cache-list

# Clear entire cache
miniature cache-clear

# Remove specific repository from cache
miniature cache-remove --repo-url https://github.com/user/repo
```

## Example Workflow

```bash
# 1. Load packages from configuration
miniature load-from-file --config-file pkg.json

# 2. Work on your packages...

# 3. Publish changes
miniature publish --message "feat: Add new functionality"

# 4. Check cache status
miniature cache-list
```

## Configuration Files

The CLI works with these configuration formats:

### `miniature.json` - Repository Loading (Editable)
For loading repositories that you want to edit and push:
```json
{
  "miniatures": [
    {
      "pkgName": "my-package",
      "domain": "https://github.com/", 
      "repoName": "user/repo",
      "pathName": "src/package",
      "branch": "main",
      "localDir": "local/path",
      "loaded": true
    }
  ]
}
```
- **Has `localDir`**: Where to load the repository
- **No `version`**: Always loads latest for editing/pushing
- **Use case**: Working repositories that you modify and push

### `pkg.json` - Dependencies (Read-only)
For installing packages as dependencies:
```json
{
  "name": "my-project",
  "version": "1.0.0", 
  "dependencies": [
    {
      "pkgName": "my-package",
      "domain": "https://github.com/",
      "repoName": "user/repo", 
      "pathName": "src/package",
      "branch": "main",
      "version": "1.2.0",
      "pkgType": "python"
    }
  ]
}
```
- **Has `version`**: Specific version to install
- **No `localDir`**: Install location determined by system
- **Use case**: External dependencies you consume but don't edit

### Common Properties
Both formats share: `pkgName`, `domain`, `repoName`, `pathName`, `branch`

## Getting Help

```bash
# Show all available commands
miniature --help

# Show help for specific command
miniature load --help
miniature publish --help
```