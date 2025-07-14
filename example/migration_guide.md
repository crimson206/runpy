# Migration Guide: From miniature.json to pkg.json with dependencies

This guide shows how to migrate from the old miniature.json format to the new pkg.json format with dependencies array.

## Old Format (miniature.json)

```json
{
    "miniatures": [
        {
            "pathName": "component/my-card",
            "repo": "https://github.com/crimson206/db-repo",
            "version": "0.1.0",
            "link": "src/component/my_card"
        },
        {
            "pathName": "component/any-name",
            "repo": "https://github.com/crimson206/my-card2",
            "version": "0.1.0",
            "link": "src/component/my_card2"
        }
    ]
}
```

## New Format (pkg.json)

```json
{
    "name": "my-project",
    "version": "1.0.0",
    "description": "My project using miniature packages",
    "dependencies": [
        {
            "pkgName": "my-card",
            "domain": "https://github.com/",
            "repoName": "crimson206/db-repo",
            "pathName": "component/my-card",
            "branch": "main",
            "localDir": "src/component/my_card",
            "version": "0.1.0"
        },
        {
            "pkgName": "my-card2",
            "domain": "https://github.com/",
            "repoName": "crimson206/my-card2",
            "pathName": "component/any-name",
            "branch": "main",
            "localDir": "src/component/my_card2",
            "version": "0.1.0"
        }
    ]
}
```

## Key Differences

1. **File Name**: Change from `miniature.json` to `pkg.json`
2. **Root Structure**: Add project metadata (`name`, `version`, `description`)
3. **Array Name**: Change from `"miniatures"` to `"dependencies"`
4. **Field Mapping**:
   - `repo` → Split into `domain` + `repoName`
   - `link` → `localDir`
   - Add `pkgName` for each dependency
   - Add `branch` (defaults to "main")

## Benefits of the New Format

1. **Better Integration**: The pkg.json format aligns with standard package managers
2. **More Flexibility**: Separate domain and repo name allows better URL construction
3. **Enhanced Features**: Support for custom configurations, package types, and version constraints
4. **Project Metadata**: Include project-level information alongside dependencies

## Loading Dependencies

Both formats are supported for backward compatibility:

```python
from miniature.load import load_pkgs_from_file

# Works with both formats
results = load_pkgs_from_file("pkg.json")  # New format
results = load_pkgs_from_file("miniature.json")  # Old format
```

## Advanced Features in New Format

The new format supports additional features:

```json
{
    "name": "advanced-project",
    "version": "2.0.0",
    "dependencies": [
        {
            "pkgName": "python-package",
            "pkgType": "python",
            "domain": "https://github.com/",
            "repoName": "user/python-pkg",
            "pathName": "src",
            "branch": "develop",
            "localDir": "deps/python-pkg",
            "version": ">=1.0.0",
            "customConfig": {
                "install": "pip install -e .",
                "test": "pytest"
            }
        },
        {
            "pkgName": "npm-package",
            "pkgType": "npm",
            "domain": "https://gitlab.com/",
            "repoName": "org/npm-pkg",
            "pathName": "packages/core",
            "tag": "v2.0.0",
            "localDir": "node_modules/@org/core",
            "customConfig": {
                "install": "npm install",
                "build": "npm run build"
            }
        }
    ]
}
```

Features shown:
- `pkgType`: Specify package type (python, npm, etc.)
- `version`: Use version constraints like `">=1.0.0"`
- `tag`: Use specific tags instead of branches
- `customConfig`: Define custom commands for different operations