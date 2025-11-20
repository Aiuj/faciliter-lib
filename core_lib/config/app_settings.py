"""Application Core Configuration Settings.

This module contains the core application settings that extend
the base AppSettings with BaseSettings compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from .base_settings import BaseSettings, EnvParser
from ..utils.app_settings import AppSettings as BaseAppSettings


@dataclass(frozen=True)
class AppSettings(BaseSettings):
    """Core application settings with BaseSettings compatibility.
    
    Extends the base AppSettings with environment variable parsing
    and validation capabilities from BaseSettings.
    """
    
    app_name: str = "app"
    version: str = "0.2.8"
    environment: str = "dev"
    log_level: str = "DEBUG"
    project_root: Optional[Path] = None
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "AppSettings":
        """Create app settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        # Try to auto-detect project root if not provided
        project_root = overrides.get("project_root")
        if project_root is None:
            try:
                # Try to find project root by looking for pyproject.toml
                current = Path.cwd()
                for parent in [current] + list(current.parents):
                    if (parent / "pyproject.toml").exists():
                        project_root = parent
                        break
            except Exception:
                project_root = None
        
        # Use the base AppSettings to get version from pyproject.toml
        base_settings = BaseAppSettings(
            app_name=EnvParser.get_env("APP_NAME", default="app"),
            project_root=project_root
        )
        
        settings_dict = {
            "app_name": base_settings.app_name,
            "version": base_settings.version,
            "environment": base_settings.environment,
            "log_level": base_settings.log_level,
            "project_root": base_settings.project_root,
        }
        
        settings_dict.update(overrides)
        return cls(**settings_dict)
    
    def validate(self) -> None:
        """Validate app settings."""
        if not self.app_name or not self.app_name.strip():
            raise ValueError("App name cannot be empty")
        
        valid_environments = ["dev", "development", "staging", "prod", "production", "test", "testing"]
        if self.environment.lower() not in valid_environments:
            # Don't raise error, just warn - environment can be custom
            pass
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_log_levels)}")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("dev", "development")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ("prod", "production")
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment.lower() in ("test", "testing")
    
    def as_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "environment": self.environment,
            "log_level": self.log_level,
            "project_root": str(self.project_root) if self.project_root else None,
        }