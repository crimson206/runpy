# Before Moving to Next Task

## Version Control Workflow

Before proceeding to the next task, always follow this workflow:

### 1. Check Current Status
```bash
git status
git diff
```

### 2. Stage and Commit Changes
- Use conventional commit format
- Include clear, descriptive commit messages
- Reference the task/feature being implemented

Example commit messages:
```
feat: implement hierarchical command structure with groups
feat: add schema generation command with complex type support
feat: add docs command for documentation viewing
fix: update test assertions for command name transformations
```

### 3. Version Bumping
- For new features: bump minor version (0.1.0 � 0.2.0)
- For bug fixes: bump patch version (0.1.0 � 0.1.1)
- For breaking changes: bump major version (0.1.0 � 1.0.0)
- For pre-release: use appropriate suffix (-alpha.1, -beta.1, -rc.1)

### 4. Create Release Commit
```bash
# Update version in pyproject.toml or setup.py
# Commit with version bump
git commit -m "chore: bump version to v0.2.0-alpha.1"
```

### 5. Tag the Release
```bash
git tag -a v0.2.0-alpha.1 -m "Alpha release: hierarchical commands, schema generation, docs command"
```

### 6. Push Changes and Tags
```bash
git push origin <branch-name>
git push origin --tags
```

## Checklist Before Moving On

- [ ] All tests for current feature are passing
- [ ] Code is properly formatted and linted
- [ ] Changes are committed with conventional commit messages
- [ ] Version is bumped appropriately
- [ ] Release is tagged
- [ ] Changes and tags are pushed to remote

## Example Workflow

```bash
# 1. Check status
git status
git diff

# 2. Stage and commit feature
git add -A
git commit -m "feat: implement docs command with tree view and export formats"

# 3. Update version
# Edit pyproject.toml to bump version
git add pyproject.toml
git commit -m "chore: bump version to v0.2.0-alpha.1"

# 4. Create tag
git tag -a v0.2.0-alpha.1 -m "Alpha release: docs command implementation"

# 5. Push everything
git push origin dev
git push origin --tags
```

## Notes

- Always ensure CI/CD passes before creating a release
- Document any breaking changes in the commit message
- Consider creating a CHANGELOG.md entry for significant releases
- For alpha/beta releases, include a summary of what's been implemented so far