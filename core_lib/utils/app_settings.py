"""
app_settings.py

Reusable application settings helper for FacilitÂ­er projects.

Features:
- Reads app version from pyproject.toml ([project].version) with safe fallbacks.
- Exposes common environment-driven settings (environment, log level).
- Provides a small, dependency-free API using stdlib tomllib (Python 3.11+).

Usage:
    from core_lib.utils.app_settings import AppSettings
    settings = AppSettings(app_name="MyApp", project_root=Path(__file__).resolve().parents[1])
    print(settings.version)

This class is intentionally minimal; projects can extend it or compose
project-specific settings files around it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except Exception as _e:  # pragma: no cover - our projects target 3.12
    tomllib = None  # type: ignore[assignment]


@dataclass(frozen=True)
class AppSettings:
    """Minimal cross-project application settings.

    Args:
        app_name: Logical application name.
        project_root: Filesystem path to the project root containing a
            pyproject.toml. If None, auto-detect by walking up from CWD.

    Attributes:
        app_name: The provided application name.
        version: The application version resolved from pyproject.toml.
        environment: Normalized environment name (dev/prod/etc.).
        log_level: Effective log level (defaults DEBUG in dev, else INFO).
        project_root: Resolved project root Path if found, else None.

    Notes:
        - Version resolution prefers pyproject.toml over environment variables.
        - If pyproject.toml is not found or unreadable, falls back to the
          APP_VERSION env var, then "0.1.0".
    """

    app_name: str
    version: str
    environment: str
    log_level: str
    project_root: Path | None

    def __init__(self, app_name: str, project_root: str | Path | None = None) -> None:
        object.__setattr__(self, "app_name", app_name)

        resolved_root = self._resolve_project_root(project_root)
        object.__setattr__(self, "project_root", resolved_root)

        version = self._resolve_version(resolved_root)
        object.__setattr__(self, "version", version)

        env = os.getenv("ENVIRONMENT", "dev").lower()
        object.__setattr__(self, "environment", env)

        default_level = "DEBUG" if env == "dev" else "INFO"
        level = os.getenv("LOG_LEVEL", default_level).upper()
        object.__setattr__(self, "log_level", level)

    # ----------------------------
    # Resolution helpers
    # ----------------------------
    @staticmethod
    def _resolve_project_root(project_root: str | Path | None) -> Path | None:
        """Resolve the project root path.

        Strategy:
            1) Use provided path if given and exists.
            2) Else, attempt to walk up from CWD to find a pyproject.toml.
            3) If not found, return None.

        Returns:
            A Path to the directory containing pyproject.toml or None.
        """
        if project_root is not None:
            root = Path(project_root).resolve()
            return root if root.exists() else None

        # Walk upwards from CWD looking for pyproject.toml
        cwd = Path(os.getcwd()).resolve()
        for parent in [cwd, *cwd.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        return None

    @staticmethod
    def _read_pyproject_version(pyproject_path: Path) -> str | None:
        """Read the version from a pyproject.toml file.

        Returns None if the file cannot be parsed or the version is missing.
        """
        if tomllib is None:
            return None
        try:
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)  # type: ignore[no-untyped-call]
            project = data.get("project") or {}
            version = project.get("version")
            if isinstance(version, str) and version.strip():
                return version.strip()
        except Exception:
            return None
        return None

    def _resolve_version(self, project_root: Path | None) -> str:
        """Resolve application version.

        Precedence:
            1) pyproject.toml [project].version (if project_root is known)
            2) APP_VERSION environment variable
            3) "0.1.0" default
        """
        if project_root is not None:
            pyproject = project_root / "pyproject.toml"
            if pyproject.exists():
                v = self._read_pyproject_version(pyproject)
                if v:
                    return v

        return os.getenv("APP_VERSION", "0.1.0")

    # ----------------------------
    # Convenience
    # ----------------------------
    def as_dict(self) -> dict:
        """Return a dict representation of core settings."""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "environment": self.environment,
            "log_level": self.log_level,
            "project_root": str(self.project_root) if self.project_root else None,
        }
