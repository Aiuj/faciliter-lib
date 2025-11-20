"""Example: High Availability Embeddings with Fallback Client

This example demonstrates how to use FallbackEmbeddingClient for production reliability
with automatic failover between multiple embedding providers.

Features demonstrated:
- Automatic failover to backup providers
- Health status caching for smart provider selection
- Prevention of infinite retry loops
- Monitoring and statistics
"""

from core_lib.embeddings import FallbackEmbeddingClient, EmbeddingGenerationError
import time


def example_basic_fallback():
    """Basic example with multiple Infinity hosts and health caching."""
    print("\n=== Example 1: Multiple Infinity Hosts with Health Caching ===\n")
    
    # Configure three Infinity servers for redundancy
    # Health caching is enabled by default if cache is available
    client = FallbackEmbeddingClient.from_config([
        {"provider": "infinity", "base_url": "http://localhost:7997"},
        {"provider": "infinity", "base_url": "http://localhost:7998"},  
        {"provider": "infinity", "base_url": "http://localhost:7999"},
    ], common_model="BAAI/bge-small-en-v1.5")
    
    # Generate embeddings - automatically fails over if primary is down
    text = "High availability embedding system"
    embedding = client.generate_embedding(text)
    
    print(f"Generated embedding with dimension: {len(embedding)}")
    print(f"First few values: {embedding[:5]}")
    
    # Check provider stats including cached health status
    stats = client.get_provider_stats()
    print(f"\nActive provider: {stats['current_provider']}")
    print(f"Total providers: {stats['total_providers']}")
    print(f"Health cache enabled: {stats['health_cache_enabled']}")
    
    if 'preferred_provider' in stats:
        print(f"Preferred provider (cached): {stats['preferred_provider']}")
    
    # Show health status of each provider
    print("\nProvider Health Status:")
    for provider in stats['providers']:
        cached_health = provider.get('cached_healthy')
        health_str = "healthy (cached)" if cached_health else "unknown/unhealthy"
        print(f"  Provider {provider['index']} ({provider['base_url']}): {health_str}")
    
    # Second request - should use cached preferred provider without retrying failed ones
    print("\nMaking second request (should use cached healthy provider)...")
    embedding2 = client.generate_embedding("Second request with cache optimization")
    print(f"Success! Dimension: {len(embedding2)}")


def example_mixed_providers():
    """Example with mixed local and cloud providers."""
    print("\n=== Example 2: Mixed Providers (Local + Cloud Backup) ===\n")
    
    client = FallbackEmbeddingClient.from_config([
        # Try local Infinity first (fast, free)
        {"provider": "infinity", "base_url": "http://localhost:7997"},
        # Fallback to Ollama (also local)
        {"provider": "ollama", "base_url": "http://localhost:11434"},
        # Last resort: OpenAI (requires API key)
        # {"provider": "openai", "api_key": "sk-..."},  # Uncomment with real key
    ], 
        common_model="BAAI/bge-small-en-v1.5",
        common_embedding_dim=384,
    )
    
    texts = [
        "First embedding request",
        "Second embedding request",
        "Third batch request",
    ]
    
    try:
        embeddings = client.generate_embedding(texts)
        print(f"Successfully generated {len(embeddings)} embeddings")
        
        # Show which provider was used
        stats = client.get_provider_stats()
        active_provider = stats['providers'][stats['current_provider']]
        print(f"Used provider: {active_provider['type']} (index {active_provider['index']})")
        
    except EmbeddingGenerationError as e:
        print(f"All providers failed: {e}")


def example_environment_config():
    """Example using simplified comma-separated URL configuration."""
    print("\n=== Example 3: Simplified Environment Configuration ===\n")
    
    import os
    
    # Set up environment variables with comma-separated URLs
    os.environ["EMBEDDING_PROVIDER"] = "infinity"
    os.environ["INFINITY_BASE_URL"] = "http://localhost:7997,http://localhost:7998,http://localhost:7999"
    os.environ["EMBEDDING_MODEL"] = "BAAI/bge-small-en-v1.5"
    os.environ["EMBEDDING_DIMENSION"] = "384"
    os.environ["EMBEDDING_TIMEOUT"] = "30"
    
    # Or use generic EMBEDDING_BASE_URL:
    # os.environ["EMBEDDING_BASE_URL"] = "http://host1:7997,http://host2:7997"
    
    try:
        # Auto-create fallback chain from comma-separated URLs
        client = FallbackEmbeddingClient.from_env()
        
        embedding = client.generate_embedding("Environment-configured embedding")
        print(f"Generated embedding with dimension: {len(embedding)}")
        
        stats = client.get_provider_stats()
        print(f"Configured {stats['total_providers']} providers from comma-separated URLs")
        print(f"Providers: {[p['base_url'] for p in stats['providers']]}")
        
    except ValueError as e:
        print(f"Configuration error: {e}")


def example_health_monitoring():
    """Example demonstrating health checks and monitoring."""
    print("\n=== Example 4: Health Monitoring ===\n")
    
    client = FallbackEmbeddingClient.from_config([
        {"provider": "infinity", "base_url": "http://localhost:7997"},
        {"provider": "infinity", "base_url": "http://localhost:7998"},
    ], common_model="BAAI/bge-small-en-v1.5")
    
    # Check overall health
    is_healthy = client.health_check()
    print(f"System health: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
    
    # Generate some embeddings to potentially trigger failures
    for i in range(3):
        try:
            text = f"Test embedding {i + 1}"
            embedding = client.generate_embedding(text)
            print(f"  Request {i + 1}: Success ({len(embedding)} dims)")
        except EmbeddingGenerationError:
            print(f"  Request {i + 1}: Failed")
    
    # Get detailed stats
    stats = client.get_provider_stats()
    print("\nProvider Statistics:")
    for provider in stats['providers']:
        status = "✓ Active" if provider['index'] == stats['current_provider'] else "  Standby"
        print(f"  [{status}] Provider {provider['index']}: {provider['type']}")
        print(f"         Model: {provider['model']}")
        print(f"         Failures: {provider['failures']}")


def example_retry_behavior():
    """Example showing retry and failover behavior."""
    print("\n=== Example 5: Retry and Failover Behavior ===\n")
    
    client = FallbackEmbeddingClient.from_config(
        provider_configs=[
            {"provider": "infinity", "base_url": "http://localhost:7997"},
            {"provider": "infinity", "base_url": "http://localhost:7998"},
        ],
        common_model="BAAI/bge-small-en-v1.5",
        max_retries_per_provider=3,  # Try each provider 3 times
    )
    
    print(f"Configured with {client.max_retries_per_provider} retries per provider")
    
    try:
        start = time.time()
        embedding = client.generate_embedding("Testing retry behavior")
        elapsed = (time.time() - start) * 1000
        
        print(f"Success! Generated in {elapsed:.1f}ms")
        print(f"Embedding dimension: {len(embedding)}")
        
    except EmbeddingGenerationError as e:
        print(f"All providers exhausted: {e}")


def example_graceful_degradation():
    """Example with graceful degradation (no exceptions)."""
    print("\n=== Example 6: Graceful Degradation ===\n")
    
    client = FallbackEmbeddingClient.from_config(
        provider_configs=[
            {"provider": "infinity", "base_url": "http://localhost:7997"},
            {"provider": "infinity", "base_url": "http://localhost:7998"},
        ],
        common_model="BAAI/bge-small-en-v1.5",
        fail_on_all_providers=False,  # Don't raise exceptions
    )
    
    embedding = client.generate_embedding("Graceful degradation test")
    
    if embedding is None:
        print("All providers failed, using fallback logic")
        # Your fallback logic here:
        # - Use cached embeddings
        # - Return zero vector
        # - Skip this document
        # etc.
    else:
        print(f"Success! Embedding dimension: {len(embedding)}")


def example_production_pattern():
    """Real-world production deployment pattern with health caching."""
    print("\n=== Example 7: Production Deployment with Smart Health Tracking ===\n")
    
    import os
    
    # Production configuration with multi-region deployment
    client = FallbackEmbeddingClient.from_config(
        provider_configs=[
            # Primary region
            {
                "provider": "infinity",
                "base_url": os.getenv("INFINITY_PRIMARY_URL", "http://infinity-us-east:7997"),
                "timeout": 10,
            },
            # Secondary region
            {
                "provider": "infinity", 
                "base_url": os.getenv("INFINITY_SECONDARY_URL", "http://infinity-us-west:7997"),
                "timeout": 15,
            },
            # Cloud backup (only if configured)
            *([{
                "provider": "openai",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "timeout": 30,
            }] if os.getenv("OPENAI_API_KEY") else []),
        ],
        common_model="BAAI/bge-small-en-v1.5",
        common_embedding_dim=384,
        max_retries_per_provider=2,
    )
    
    # Simulate production usage
    documents = [
        "Production document 1",
        "Production document 2", 
        "Production document 3",
    ]
    
    successful = 0
    failed = 0
    
    print("Processing documents (watch health caching optimize retries)...\n")
    for i, doc in enumerate(documents, 1):
        try:
            start_time = time.time()
            embedding = client.generate_embedding(doc)
            elapsed = (time.time() - start_time) * 1000
            successful += 1
            print(f"  Document {i}: Success in {elapsed:.1f}ms")
        except EmbeddingGenerationError as e:
            failed += 1
            print(f"  Document {i}: Failed - {e}")
    
    stats = client.get_provider_stats()
    print(f"\nProcessed {successful} documents successfully, {failed} failed")
    print(f"Active provider: {stats['providers'][stats['current_provider']]['type']}")
    print(f"Total failures across all providers: {sum(stats['provider_failures'].values())}")
    
    # Show health cache effectiveness
    if stats.get('health_cache_enabled'):
        print("\nHealth Cache Status:")
        for provider in stats['providers']:
            cached = provider.get('cached_healthy')
            status = "✓ cached as healthy" if cached else "✗ not cached/failed"
            print(f"  Provider {provider['index']}: {status}")


def example_health_monitoring():
    """Example demonstrating health monitoring and cache behavior."""
    print("\n=== Example 8: Health Monitoring and Cache Behavior ===\n")
    
    client = FallbackEmbeddingClient.from_config([
        {"provider": "infinity", "base_url": "http://localhost:7997"},
        {"provider": "infinity", "base_url": "http://localhost:7998"},
    ],
        common_model="BAAI/bge-small-en-v1.5",
        health_check_interval=60,  # Check failed providers every 60s
        use_health_cache=True,     # Enable health caching (default)
    )
    
    print("Initial health check:")
    is_healthy = client.health_check()
    print(f"  At least one provider healthy: {is_healthy}")
    
    # Get detailed stats
    stats = client.get_provider_stats()
    print(f"\nDetailed Provider Stats:")
    print(f"  Health caching: {'enabled' if stats['health_cache_enabled'] else 'disabled'}")
    print(f"  Preferred provider: {stats.get('preferred_provider', 'none')}")
    
    for provider in stats['providers']:
        print(f"\n  Provider {provider['index']} ({provider.get('base_url', 'N/A')}):")
        print(f"    Type: {provider['type']}")
        print(f"    Failures: {provider['failures']}")
        print(f"    Cached as healthy: {provider.get('cached_healthy')}")
        if provider.get('last_health_check'):
            print(f"    Last health check: {time.ctime(provider['last_health_check'])}")
    
    # Demonstrate reset
    print("\n\nResetting failure counters and health cache...")
    client.reset_failures()
    
    stats_after = client.get_provider_stats()
    print(f"Failures after reset: {sum(stats_after['provider_failures'].values())}")


if __name__ == "__main__":
    print("=" * 70)
    print("High Availability Embeddings - Fallback Client Examples")
    print("=" * 70)
    
    # Note: These examples assume you have Infinity servers running
    # Start with: docker run -d -p 7997:7997 michaelf34/infinity:latest --model-name-or-path BAAI/bge-small-en-v1.5
    
    try:
        example_basic_fallback()
    except Exception as e:
        print(f"Example 1 failed: {e}")
    
    try:
        example_mixed_providers()
    except Exception as e:
        print(f"Example 2 failed: {e}")
    
    try:
        example_environment_config()
    except Exception as e:
        print(f"Example 3 failed: {e}")
    
    try:
        example_health_monitoring()
    except Exception as e:
        print(f"Example 4 failed: {e}")
    
    try:
        example_retry_behavior()
    except Exception as e:
        print(f"Example 5 failed: {e}")
    
    try:
        example_graceful_degradation()
    except Exception as e:
        print(f"Example 6 failed: {e}")
    
    try:
        example_production_pattern()
    except Exception as e:
        print(f"Example 7 failed: {e}")
    
    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
