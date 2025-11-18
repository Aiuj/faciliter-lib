# Version Management with faciliter-lib

This document explains how application name and version are managed in faciliter-lib-based projects.

## Single Source of Truth: `pyproject.toml`

The application name and version are defined **only** in your project's `pyproject.toml`:

```toml
[project]
name = "my-application"
version = "0.1.0"
```

## Automatic Detection

The `faciliter-lib` library automatically reads the version from `pyproject.toml`:

- **Application Name**: Read from `[project].name` in `pyproject.toml`
- **Version**: Read from `[project].version` in `pyproject.toml`
- **Service Name (OTLP)**: Automatically derived from application name
- **Service Version (OTLP)**: Automatically read from `pyproject.toml`

## How It Works

1. **Settings Initialization**: When settings are initialized, `faciliter-lib.config.AppSettings` automatically locates and reads `pyproject.toml`
2. **Project Root Detection**: Walks up from the current directory to find `pyproject.toml`
3. **Version Resolution Priority**:
   - First: `[project].version` from `pyproject.toml`
   - Fallback: `APP_VERSION` environment variable
   - Default: `"0.1.0"`

## Accessing Version Information

In Python code using `StandardSettings` or `AppSettings`:

```python
from faciliter_lib.config import get_settings

settings = get_settings()

# Access via settings
app_name = settings.app.app_name      # "my-application"
version = settings.app.version        # "0.1.0" (from pyproject.toml)
environment = settings.app.environment  # "dev" or "production"
```

Or use `AppSettings` directly:

```python
from faciliter_lib.utils.app_settings import AppSettings
from pathlib import Path

# Auto-detect project root
app_settings = AppSettings(app_name="my-app")

# Or specify project root explicitly
project_root = Path(__file__).resolve().parents[1]
app_settings = AppSettings(app_name="my-app", project_root=project_root)

print(f"Version: {app_settings.version}")  # Read from pyproject.toml
```

## Environment Variables

### ❌ Do NOT Set These

Do **not** set these environment variables (they are ignored or auto-detected):

- `APP_NAME` - Always read from `pyproject.toml` `[project].name`
- `APP_VERSION` - Always read from `pyproject.toml` `[project].version`
- `OTLP_SERVICE_NAME` - Automatically derived from app name
- `OTLP_SERVICE_VERSION` - Automatically read from `pyproject.toml`

### ✅ Required Environment Variables

Set these in `.env` files:

- `ENVIRONMENT` - Deployment environment (`dev`, `production`, `staging`, `test`)
- `LOG_LEVEL` - Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

See your project's `.env.example` for full configuration options.

## Updating the Version

### Manual Update

Edit `pyproject.toml`:

```toml
[project]
version = "0.2.0"  # Update this line
```

The new version is automatically picked up on next application start.

### Automated Update Tools

#### 1. **bump2version** (Recommended)

```bash
pip install bump2version

# Initialize configuration
cat > .bumpversion.cfg << EOF
[bumpversion]
current_version = 0.1.0
commit = True
tag = True
tag_name = v{new_version}

[bumpversion:file:pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"
EOF

# Bump version
bump2version patch  # 0.1.0 -> 0.1.1
bump2version minor  # 0.1.1 -> 0.2.0
bump2version major  # 0.2.0 -> 1.0.0
```

#### 2. **poetry** (if using Poetry)

```bash
poetry version patch  # 0.1.0 -> 0.1.1
poetry version minor  # 0.1.1 -> 0.2.0
poetry version major  # 0.2.0 -> 1.0.0
```

#### 3. **setuptools-scm** (Version from Git Tags)

Automatically derive version from Git tags:

```toml
[build-system]
requires = ["setuptools>=64", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[tool.setuptools_scm]
write_to = "src/_version.py"
version_scheme = "post-release"
local_scheme = "no-local-version"
```

Then version is automatically determined from Git tags:

```bash
git tag v0.2.0
# Version automatically becomes 0.2.0
```

### Git Tagging Workflow

```bash
# Update version in pyproject.toml
vim pyproject.toml

# Commit the change
git add pyproject.toml
git commit -m "Bump version to 0.2.0"

# Create an annotated Git tag
git tag -a v0.2.0 -m "Release version 0.2.0"

# Push with tags
git push origin main --tags
```

## CI/CD Integration

### GitHub Actions

Extract version for use in CI/CD pipelines:

```yaml
name: Build and Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Get version from pyproject.toml
        id: get_version
        run: |
          VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
          echo "version=$VERSION" >> $GITHUB_OUTPUT
      
      - name: Build Docker image
        run: |
          docker build -t myapp:${{ steps.get_version.outputs.version }} .
          docker tag myapp:${{ steps.get_version.outputs.version }} myapp:latest
      
      - name: Push to registry
        run: |
          docker push myapp:${{ steps.get_version.outputs.version }}
          docker push myapp:latest
```

### GitLab CI

```yaml
variables:
  VERSION: ""

before_script:
  - export VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

build:
  script:
    - docker build -t myapp:$VERSION .
    - docker tag myapp:$VERSION myapp:latest
```

## Observability Integration

### OTLP (OpenTelemetry)

Service name and version are automatically propagated to OTLP:

```python
# No configuration needed - automatic!
from faciliter_lib.config import StandardSettings

settings = StandardSettings.from_env()

# OTLP will automatically use:
# - service.name = settings.app.app_name (from pyproject.toml)
# - service.version = settings.app.version (from pyproject.toml)
```

### Langfuse Tracing

```python
from faciliter_lib.tracing import setup_tracing
from faciliter_lib.config import get_settings

settings = get_settings()

# Automatically uses app name and version
tracing_client = setup_tracing(name=settings.app.app_name)
```

### Logging

```python
from faciliter_lib import setup_logging
from faciliter_lib.config import get_settings

settings = get_settings()

# App name and version automatically included in log metadata
setup_logging(app_name=settings.app.app_name, level=settings.app.log_level)
```

## Testing

In tests, the version is automatically detected from `pyproject.toml`:

```python
import pytest
from faciliter_lib.utils.app_settings import AppSettings
from pathlib import Path

def test_app_version():
    """Test that version is correctly read from pyproject.toml."""
    project_root = Path(__file__).resolve().parents[1]
    settings = AppSettings(app_name="my-app", project_root=project_root)
    
    # Version is automatically read from pyproject.toml
    assert settings.version  # Not empty
    assert settings.version != "0.0.0"  # Has real version
    
def test_settings_version():
    """Test version through StandardSettings."""
    from your_app.config import get_settings
    
    settings = get_settings()
    assert settings.app.version == "0.1.0"  # Matches pyproject.toml
```

## Benefits

✅ **Single source of truth** - No duplication across config files  
✅ **Automatic propagation** - Version used everywhere automatically  
✅ **Standard format** - Follows Python packaging standards (PEP 621)  
✅ **CI/CD friendly** - Easy to parse in automation scripts  
✅ **Git tag integration** - Can use setuptools-scm for auto-versioning  
✅ **Observability ready** - Automatically flows to OTLP, Langfuse, logs  
✅ **Zero configuration** - Works out of the box with faciliter-lib  

## Migration from Old Approach

### Before (Environment Variables)

```python
# ❌ Old approach - brittle and error-prone
import os

APP_NAME = os.getenv("APP_NAME", "unknown")
VERSION = os.getenv("APP_VERSION", "0.1.0")
```

```bash
# Had to set in .env, .env.docker, CI/CD, etc.
APP_NAME=my-app
APP_VERSION=0.1.0
OTLP_SERVICE_NAME=my-app
OTLP_SERVICE_VERSION=0.1.0
```

### After (faciliter-lib)

```python
# ✅ New approach - automatic and consistent
from faciliter_lib.config import get_settings

settings = get_settings()
app_name = settings.app.app_name   # From pyproject.toml
version = settings.app.version     # From pyproject.toml
```

```toml
# Only set once in pyproject.toml
[project]
name = "my-app"
version = "0.1.0"
```

### Migration Steps

1. **Remove environment variables**:
   ```bash
   # Remove from .env, .env.docker, etc.
   # APP_NAME=...
   # APP_VERSION=...
   # OTLP_SERVICE_NAME=...
   # OTLP_SERVICE_VERSION=...
   ```

2. **Ensure pyproject.toml has correct name/version**:
   ```toml
   [project]
   name = "my-application"
   version = "0.1.0"
   ```

3. **Update code to use settings**:
   ```python
   # Replace hardcoded values or env vars
   from faciliter_lib.config import get_settings
   settings = get_settings()
   ```

4. **Remove version from deployment configs** (optional):
   - Let CI/CD read from `pyproject.toml` dynamically
   - Use Git tags with setuptools-scm for full automation

## Best Practices

### 1. Keep pyproject.toml Clean

```toml
[project]
name = "my-application"  # Use lowercase with hyphens
version = "0.1.0"        # Follow semantic versioning
```

### 2. Use Semantic Versioning

- **MAJOR** version: Incompatible API changes (1.0.0 → 2.0.0)
- **MINOR** version: Backward-compatible new features (1.0.0 → 1.1.0)
- **PATCH** version: Backward-compatible bug fixes (1.0.0 → 1.0.1)

### 3. Tag Releases

Always create Git tags for releases:

```bash
git tag -a v0.2.0 -m "Release 0.2.0: Added feature X"
git push origin --tags
```

### 4. Automate with CI/CD

Let your CI/CD pipeline handle versioning and releases automatically.

### 5. Document Releases

Use GitHub Releases or CHANGELOG.md to document version changes:

```markdown
## [0.2.0] - 2025-11-18
### Added
- New feature X
- New feature Y

### Fixed
- Bug #123
```

## Troubleshooting

### Version Shows as "0.1.0" in Production

**Problem**: Version not being read from `pyproject.toml`

**Solution**: Ensure `pyproject.toml` is included in your Docker image:

```dockerfile
# In Dockerfile
COPY pyproject.toml /app/
```

### Version is None or Empty

**Problem**: `pyproject.toml` not found

**Solution**: Verify project root detection:

```python
from pathlib import Path
from faciliter_lib.utils.app_settings import AppSettings

project_root = Path(__file__).resolve().parents[1]
print(f"Project root: {project_root}")
print(f"pyproject.toml exists: {(project_root / 'pyproject.toml').exists()}")

settings = AppSettings(app_name="my-app", project_root=project_root)
print(f"Version: {settings.version}")
```

### CI/CD Can't Parse pyproject.toml

**Problem**: Python 3.10 or older doesn't have `tomllib`

**Solution**: Install `tomli` package:

```yaml
# GitHub Actions
- name: Get version
  run: |
    pip install tomli
    VERSION=$(python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])")
```

## Summary

- **Application Name**: `pyproject.toml` → `[project].name`
- **Version**: `pyproject.toml` → `[project].version`
- **No environment variables needed** for app name/version
- **Automatically propagated** to OTLP, logging, tracing, etc.
- **Update once** in `pyproject.toml` and it's used everywhere
- **faciliter-lib handles everything** automatically

For more information:
- [Settings Singleton Guide](SETTINGS_SINGLETON_QUICK_REF.md)
- [OTLP Quick Reference](OTLP_QUICK_REFERENCE.md)
- [Centralized Logging](centralized-logging.md)
