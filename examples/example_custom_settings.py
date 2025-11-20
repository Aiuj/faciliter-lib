"""
Example demonstrating the simplified custom settings extension pattern.

This shows how ea        print(f"\n🚀 Standard Services:")
        print(f"   LLM Enabled: {settings.enable_llm}")
        if settings.llm and isinstance(settings.llm, dict):
            print(f"   LLM Provider: {settings.llm.get('provider', 'Not configured')}")
        print(f"   Cache Enabled: {settings.enable_cache}")
        if settings.cache and isinstance(settings.cache, dict):
            print(f"   Cache Host: {settings.cache.get('host', 'Not configured')}")s to extend StandardSettings with custom configuration
while keeping all the standard functionality.
"""

import os
from dataclasses import dataclass
from typing import Optional
from core_lib.config import StandardSettings


@dataclass(frozen=True)
class MyAppSettings(StandardSettings):
    """Custom app settings extending StandardSettings.
    
    This demonstrates the easy extension pattern - just add your fields
    and use extend_from_env() to configure environment variable mapping.
    """
    
    # Custom application settings
    api_timeout: int = 30
    debug_mode: bool = False
    api_key: Optional[str] = None
    max_workers: int = 4
    feature_flags: list = None
    
    @classmethod
    def from_env(cls, **kwargs):
        """Load settings from environment with custom field mappings."""
        return StandardSettings.extend_from_env(
            custom_config={
                "api_timeout": {
                    "env_vars": ["API_TIMEOUT", "TIMEOUT"], 
                    "default": 30, 
                    "env_type": int
                },
                "debug_mode": {
                    "env_vars": ["DEBUG_MODE", "DEBUG"], 
                    "default": False, 
                    "env_type": bool
                },
                "api_key": {
                    "env_vars": ["API_KEY", "MY_API_KEY"], 
                    "required": True
                },
                "max_workers": {
                    "env_vars": ["MAX_WORKERS", "WORKERS"], 
                    "default": 4, 
                    "env_type": int
                },
                "feature_flags": {
                    "env_vars": ["FEATURE_FLAGS"], 
                    "default": [], 
                    "env_type": list
                },
            },
            **kwargs
        )


def demo_custom_settings():
    """Demonstrate the custom settings in action."""
    print("=== Custom Settings Demo ===")
    
    # Set up some environment variables
    os.environ.update({
        "APP_NAME": "my-awesome-app",
        "ENVIRONMENT": "production",
        "API_KEY": "secret-api-key-123",
        "API_TIMEOUT": "60",
        "DEBUG_MODE": "false",
        "MAX_WORKERS": "8",
        "FEATURE_FLAGS": "feature_a,feature_b,feature_c",
        
        # Standard service configuration
        "OPENAI_API_KEY": "sk-test",
        "REDIS_HOST": "redis.example.com"
    })
    
    try:
        # Load custom settings - gets both standard and custom fields
        settings = MyAppSettings.from_env()
        
        print(f"\\n📱 App Configuration:")
        print(f"   Name: {settings.app_name}")
        print(f"   Environment: {settings.environment}")
        print(f"   Version: {settings.version}")
        
        print(f"\\n🔧 Custom Configuration:")
        print(f"   API Key: {settings.api_key[:8]}...")
        print(f"   API Timeout: {settings.api_timeout}s")
        print(f"   Debug Mode: {settings.debug_mode}")
        print(f"   Max Workers: {settings.max_workers}")
        print(f"   Feature Flags: {settings.feature_flags}")
        
        print(f"\\n🚀 Standard Services:")
        print(f"   LLM Enabled: {settings.enable_llm}")
        if settings.llm and isinstance(settings.llm, dict):
            print(f"   LLM Provider: {settings.llm.get('provider', 'Not configured')}")
        print(f"   Cache Enabled: {settings.enable_cache}")
        if settings.cache and isinstance(settings.cache, dict):
            print(f"   Cache Host: {settings.cache.get('host', 'Not configured')}")
        
        print(f"\\n✅ Validation: {'Passed' if settings.is_valid else 'Failed'}")
        
        # Show how easy it is to get existing config objects
        if settings.llm:
            llm_config = settings.get_llm_config()
            print(f"\\n🔗 Integration with existing systems:")
            print(f"   LLM Config Type: {type(llm_config).__name__}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\\n" + "="*50)


if __name__ == "__main__":
    demo_custom_settings()