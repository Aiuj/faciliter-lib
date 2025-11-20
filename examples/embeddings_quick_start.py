#!/usr/bin/env python3
"""
Embeddings Quick Start Example

This script demonstrates the key features of the core-lib embeddings module.
Run different sections by uncommenting the relevant function calls at the bottom.
"""

import os
from typing import List

# Set up environment (optional - for demo purposes)
# os.environ['EMBEDDING_PROVIDER'] = 'openai'
# os.environ['OPENAI_API_KEY'] = 'your-key-here'


def demo_basic_usage():
    """Demonstrate basic embedding generation."""
    print("=== Basic Usage Demo ===")
    
    try:
        from core_lib.embeddings import create_embedding_client
        
        # Auto-detect provider from environment
        client = create_embedding_client()
        print(f"Created client: {client.__class__.__name__}")
        
        # Single text embedding
        text = "The quick brown fox jumps over the lazy dog"
        embedding = client.generate_embedding(text)
        print(f"Single embedding - Dimension: {len(embedding)}")
        
        # Batch embedding generation
        texts = [
            "Machine learning transforms data into insights",
            "Natural language processing enables human-computer interaction",
            "Deep learning models learn complex patterns"
        ]
        embeddings = client.generate_embedding(texts)
        print(f"Batch embeddings - Count: {len(embeddings)}, Dimension: {len(embeddings[0])}")
        
        # Performance info
        time_ms = client.get_embedding_time_ms()
        print(f"Last operation took: {time_ms:.2f}ms")
        
    except Exception as e:
        print(f"Basic usage demo failed: {e}")
        print("Tip: Set EMBEDDING_PROVIDER and appropriate API keys in environment")
    
    print()


def demo_provider_specific():
    """Demonstrate provider-specific features."""
    print("=== Provider-Specific Demo ===")
    
    # OpenAI with custom dimensions
    try:
        from core_lib.embeddings import create_openai_client
        
        client = create_openai_client(
            model="text-embedding-3-small",
            embedding_dim=512,  # Reduced dimensions
            use_l2_norm=True
        )
        
        text = "OpenAI embedding with custom dimensions"
        embedding = client.generate_embedding(text)
        print(f"OpenAI - Dimension: {len(embedding)} (custom 512)")
        
        # Model information
        model_info = client.get_model_info()
        print(f"OpenAI model info: {model_info.get('dimensions', 'N/A')} default dims")
        
    except Exception as e:
        print(f"OpenAI demo failed: {e}")
    
    # Google GenAI with task types
    try:
        from core_lib.embeddings import create_google_genai_client, TaskType
        
        client = create_google_genai_client(
            model="text-embedding-004",
            task_type=TaskType.SEMANTIC_SIMILARITY,
            title="Document Similarity Demo"
        )
        
        texts = [
            "The cat sat on the mat",
            "A feline rested on the rug"
        ]
        embeddings = client.generate_embedding(texts)
        print(f"Google GenAI - Semantic similarity embeddings: {len(embeddings)} texts")
        
        # Show supported task types
        task_types = client.get_supported_task_types()
        print(f"Supported task types: {', '.join(task_types[:3])}...")
        
    except Exception as e:
        print(f"Google GenAI demo failed: {e}")
    
    # Local model
    try:
        from core_lib.embeddings import create_local_client
        
        client = create_local_client(
            model="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"
        )
        
        text = "Local embedding generation without API calls"
        embedding = client.generate_embedding(text)
        print(f"Local model - Dimension: {len(embedding)}")
        
        # Model info
        model_info = client.get_model_info()
        print(f"Local model: {model_info.get('model_name', 'Unknown')}")
        
    except Exception as e:
        print(f"Local model demo failed: {e}")
        print("Tip: Install sentence-transformers with: pip install sentence-transformers")
    
    print()


def demo_task_types():
    """Demonstrate different task types with Google GenAI."""
    print("=== Task Types Demo ===")
    
    try:
        from core_lib.embeddings import create_google_genai_client, TaskType
        
        # Different task types for different use cases
        task_examples = {
            TaskType.SEMANTIC_SIMILARITY: [
                "The weather is sunny today",
                "It's a bright and clear day"
            ],
            TaskType.CLASSIFICATION: [
                "This product is excellent!",
                "This item is disappointing."
            ],
            TaskType.CLUSTERING: [
                "Sports news update",
                "Technology breakthrough",
                "Weather forecast"
            ]
        }
        
        for task_type, texts in task_examples.items():
            try:
                client = create_google_genai_client(
                    task_type=task_type,
                    title=f"{task_type.value} Example"
                )
                
                embeddings = client.generate_embedding(texts)
                print(f"{task_type.value}: Generated {len(embeddings)} embeddings")
                
            except Exception as e:
                print(f"{task_type.value} failed: {e}")
    
    except Exception as e:
        print(f"Task types demo failed: {e}")
        print("Tip: Set GOOGLE_GENAI_API_KEY or GEMINI_API_KEY environment variable")
    
    print()


def demo_factory_patterns():
    """Demonstrate different factory creation patterns."""
    print("=== Factory Patterns Demo ===")
    
    try:
        from core_lib.embeddings import EmbeddingFactory, EmbeddingsConfig
        
        # Method 1: Auto-detection
        try:
            client = EmbeddingFactory.create()
            print(f"Auto-detected: {client.__class__.__name__}")
        except Exception as e:
            print(f"Auto-detection failed: {e}")
        
        # Method 2: Explicit provider
        try:
            client = EmbeddingFactory.create(
                provider="openai",
                model="text-embedding-3-small"
            )
            print(f"Explicit provider: {client.__class__.__name__}")
        except Exception as e:
            print(f"Explicit provider failed: {e}")
        
        # Method 3: Provider-specific factory methods
        providers = [
            ("openai", lambda: EmbeddingFactory.openai(model="text-embedding-3-small")),
            ("google_genai", lambda: EmbeddingFactory.google_genai(task_type="SEMANTIC_SIMILARITY")),
            ("local", lambda: EmbeddingFactory.local(model="sentence-transformers/all-MiniLM-L6-v2")),
        ]
        
        for provider_name, factory_func in providers:
            try:
                client = factory_func()
                print(f"Factory {provider_name}: {client.__class__.__name__}")
            except Exception as e:
                print(f"Factory {provider_name} failed: {e}")
        
        # Method 4: From configuration
        try:
            config = EmbeddingsConfig(
                provider="openai",
                model="text-embedding-3-small",
                api_key="dummy-key-for-demo"  # Would normally come from environment
            )
            client = EmbeddingFactory.from_config(config)
            print(f"From config: {client.__class__.__name__}")
        except Exception as e:
            print(f"Config-based creation failed: {e}")
    
    except Exception as e:
        print(f"Factory patterns demo failed: {e}")
    
    print()


def demo_error_handling():
    """Demonstrate proper error handling."""
    print("=== Error Handling Demo ===")
    
    from core_lib.embeddings import EmbeddingGenerationError
    
    # Test missing provider
    try:
        from core_lib.embeddings import EmbeddingFactory
        client = EmbeddingFactory.create(provider="nonexistent")
    except ValueError as e:
        print(f"✓ Caught provider error: {e}")
    
    # Test missing dependency
    try:
        from core_lib.embeddings import EmbeddingFactory
        with_patch = EmbeddingFactory.openai()
    except ImportError as e:
        print(f"✓ Caught import error: {e}")
    except Exception as e:
        print(f"✓ Caught configuration error: {e}")
    
    # Test invalid input
    try:
        from core_lib.embeddings import create_embedding_client
        client = create_embedding_client()
        # This should work, but test with invalid input type
        embedding = client.generate_embedding(12345)  # Invalid input type
    except ValueError as e:
        print(f"✓ Caught input validation error: {e}")
    except Exception as e:
        print(f"✓ Caught other error: {e}")
    
    print()


def demo_health_checks():
    """Demonstrate health checks and monitoring."""
    print("=== Health Checks Demo ===")
    
    try:
        from core_lib.embeddings import create_embedding_client
        
        client = create_embedding_client()
        
        # Health check
        is_healthy = client.health_check()
        print(f"Provider health status: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
        
        # Generate embedding and check timing
        if is_healthy:
            text = "Performance monitoring test"
            embedding = client.generate_embedding(text)
            time_ms = client.get_embedding_time_ms()
            print(f"Generated embedding in {time_ms:.2f}ms")
            print(f"Embedding dimension: {len(embedding)}")
            
            # Provider-specific info
            if hasattr(client, 'get_model_info'):
                info = client.get_model_info()
                print(f"Model info: {info}")
    
    except Exception as e:
        print(f"Health check demo failed: {e}")
    
    print()


def main():
    """Run all demos."""
    print("core-lib Embeddings Quick Start")
    print("=" * 50)
    
    # Uncomment the demos you want to run
    demo_basic_usage()
    demo_provider_specific()
    demo_task_types()
    demo_factory_patterns()
    demo_error_handling()
    demo_health_checks()
    
    print("Demo complete!")
    print("\nTo use embeddings in your code:")
    print("1. Set environment variables (EMBEDDING_PROVIDER, API keys)")
    print("2. Import: from core_lib.embeddings import create_embedding_client")
    print("3. Create client: client = create_embedding_client()")
    print("4. Generate: embedding = client.generate_embedding('your text')")


if __name__ == "__main__":
    main()