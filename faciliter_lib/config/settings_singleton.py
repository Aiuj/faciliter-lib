"""
Settings Singleton Manager

Provides a thread-safe singleton pattern for managing a single StandardSettings 
instance throughout an application's lifecycle. This is particularly useful for 
client applications that extend StandardSettings with custom fields.

Features:
- Thread-safe singleton implementation with double-checked locking
- Easy initialization with environment variables
- Ability to reset/reconfigure settings
- Factory functions for common usage patterns
- Type hints for better IDE support

Usage:
    # Simple initialization with defaults
    settings = initialize_settings()
    
    # Initialize with custom Settings class
    @dataclass(frozen=True)
    class MySettings(StandardSettings):
        custom_field: str = "default"
    
    settings = initialize_settings(settings_class=MySettings)
    
    # Get the current settings instance
    settings = get_settings()
    
    # Reset and reinitialize
    reset_settings()
    settings = initialize_settings(enable_cache=True)
    
    # Check if settings are initialized
    if has_settings():
        settings = get_settings()
"""

from __future__ import annotations

import threading
from typing import Optional, Type, TypeVar, Any, List, Union
from pathlib import Path

from .standard_settings import StandardSettings
from .base_settings import SettingsError


T = TypeVar('T', bound=StandardSettings)


class SettingsSingletonManager:
    """Thread-safe singleton manager for Settings instances.
    
    This class ensures that only one Settings instance exists throughout
    the application lifecycle. It provides methods to initialize, access,
    and reset the settings instance.
    
    The manager uses double-checked locking to ensure thread safety during
    initialization while maintaining performance for subsequent access.
    """
    
    _instance: Optional[StandardSettings] = None
    _lock = threading.Lock()
    _initialized = False
    
    @classmethod
    def get_settings(cls) -> StandardSettings:
        """Get the current settings instance.
        
        Returns:
            The current settings instance
            
        Raises:
            SettingsError: If settings have not been initialized
        """
        if cls._instance is None:
            raise SettingsError(
                "Settings not initialized. Call initialize_settings() first."
            )
        return cls._instance
    
    @classmethod
    def set_settings(cls, settings: StandardSettings) -> None:
        """Set the settings instance.
        
        This method allows direct setting of a settings instance, useful when
        you've already created a configured instance elsewhere.
        
        Args:
            settings: The settings instance to use
            
        Raises:
            TypeError: If settings is not a StandardSettings instance
        """
        if not isinstance(settings, StandardSettings):
            raise TypeError(
                f"settings must be a StandardSettings instance, got {type(settings)}"
            )
        
        with cls._lock:
            cls._instance = settings
            cls._initialized = True
    
    @classmethod
    def initialize_settings(
        cls,
        settings_class: Type[T] = StandardSettings,  # type: ignore
        force: bool = False,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides: Any
    ) -> T:
        """Initialize the settings singleton.
        
        This method creates a new settings instance using the from_env() method
        of the provided settings class. It uses double-checked locking to ensure
        thread-safe initialization.
        
        Args:
            settings_class: The Settings class to instantiate (must extend StandardSettings)
            force: If True, reinitialize even if already initialized
            load_dotenv: Whether to load .env files
            dotenv_paths: Custom paths to search for .env files
            **overrides: Direct value overrides passed to from_env()
            
        Returns:
            The initialized settings instance
            
        Example:
            >>> settings = initialize_settings(enable_cache=True, log_level="DEBUG")
            >>> settings = initialize_settings(settings_class=MyCustomSettings)
        """
        # Fast path: already initialized and not forcing
        if cls._initialized and not force:
            if not isinstance(cls._instance, settings_class):
                raise SettingsError(
                    f"Settings already initialized with different class. "
                    f"Expected {settings_class.__name__}, got {type(cls._instance).__name__}. "
                    f"Use force=True to reinitialize."
                )
            return cls._instance  # type: ignore
        
        # Slow path: need to initialize
        with cls._lock:
            # Double-check inside lock
            if cls._initialized and not force:
                if not isinstance(cls._instance, settings_class):
                    raise SettingsError(
                        f"Settings already initialized with different class. "
                        f"Expected {settings_class.__name__}, got {type(cls._instance).__name__}. "
                        f"Use force=True to reinitialize."
                    )
                return cls._instance  # type: ignore
            
            # Create new settings instance
            try:
                cls._instance = settings_class.from_env(
                    load_dotenv=load_dotenv,
                    dotenv_paths=dotenv_paths,
                    **overrides
                )
                cls._initialized = True
                return cls._instance  # type: ignore
            except Exception as e:
                raise SettingsError(f"Failed to initialize settings: {e}") from e
    
    @classmethod
    def reset_settings(cls) -> None:
        """Reset the settings singleton.
        
        This removes the current settings instance and marks the singleton as
        uninitialized. The next call to get_settings() will raise an error until
        initialize_settings() is called again.
        
        This is primarily useful for testing or when you need to completely
        reconfigure the application settings.
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False
    
    @classmethod
    def has_settings(cls) -> bool:
        """Check if settings have been initialized.
        
        Returns:
            True if settings are initialized, False otherwise
        """
        return cls._initialized and cls._instance is not None
    
    @classmethod
    def get_settings_safe(cls) -> Optional[StandardSettings]:
        """Get settings instance without raising an error.
        
        Returns:
            The settings instance if initialized, None otherwise
        """
        return cls._instance if cls._initialized else None


# Factory functions for convenient access
def initialize_settings(
    settings_class: Type[T] = StandardSettings,  # type: ignore
    force: bool = False,
    load_dotenv: bool = True,
    dotenv_paths: Optional[List[Union[str, Path]]] = None,
    **overrides: Any
) -> T:
    """Initialize the global settings singleton.
    
    This is a convenience function that delegates to SettingsSingletonManager.
    
    Args:
        settings_class: The Settings class to instantiate (must extend StandardSettings)
        force: If True, reinitialize even if already initialized
        load_dotenv: Whether to load .env files
        dotenv_paths: Custom paths to search for .env files
        **overrides: Direct value overrides passed to from_env()
        
    Returns:
        The initialized settings instance
        
    Example:
        >>> from faciliter_lib.config import initialize_settings, StandardSettings
        >>> settings = initialize_settings()
        
        >>> from dataclasses import dataclass
        >>> @dataclass(frozen=True)
        ... class MySettings(StandardSettings):
        ...     custom_field: str = "default"
        >>> settings = initialize_settings(settings_class=MySettings)
    """
    return SettingsSingletonManager.initialize_settings(
        settings_class=settings_class,
        force=force,
        load_dotenv=load_dotenv,
        dotenv_paths=dotenv_paths,
        **overrides
    )


def get_settings() -> StandardSettings:
    """Get the current settings instance.
    
    Returns:
        The current settings instance
        
    Raises:
        SettingsError: If settings have not been initialized
        
    Example:
        >>> from faciliter_lib.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.app_name)
    """
    return SettingsSingletonManager.get_settings()


def set_settings(settings: StandardSettings) -> None:
    """Set the settings instance directly.
    
    Args:
        settings: The settings instance to use
        
    Raises:
        TypeError: If settings is not a StandardSettings instance
        
    Example:
        >>> from faciliter_lib.config import set_settings, StandardSettings
        >>> custom_settings = StandardSettings.from_env(app_name="my-app")
        >>> set_settings(custom_settings)
    """
    SettingsSingletonManager.set_settings(settings)


def reset_settings() -> None:
    """Reset the settings singleton.
    
    This removes the current settings instance. Useful for testing or
    when you need to completely reconfigure settings.
    
    Example:
        >>> from faciliter_lib.config import reset_settings, initialize_settings
        >>> reset_settings()
        >>> settings = initialize_settings(log_level="DEBUG")
    """
    SettingsSingletonManager.reset_settings()


def has_settings() -> bool:
    """Check if settings have been initialized.
    
    Returns:
        True if settings are initialized, False otherwise
        
    Example:
        >>> from faciliter_lib.config import has_settings, initialize_settings
        >>> if not has_settings():
        ...     initialize_settings()
    """
    return SettingsSingletonManager.has_settings()


def get_settings_safe() -> Optional[StandardSettings]:
    """Get settings without raising an error if not initialized.
    
    Returns:
        The settings instance if initialized, None otherwise
        
    Example:
        >>> from faciliter_lib.config import get_settings_safe
        >>> settings = get_settings_safe()
        >>> if settings:
        ...     print(settings.app_name)
    """
    return SettingsSingletonManager.get_settings_safe()
