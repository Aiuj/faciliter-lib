"""Example usage of the embedding functionality."""

import os
# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core_lib.embeddings import (
    create_embedding_client,
    create_openai_client,
    create_google_genai_client,
    create_ollama_client,
    create_local_client,
    EmbeddingFactory,
    TaskType,
)


def example_auto_detection():
    """Example of auto-detecting provider from environment."""
    print("=== Auto-Detection Example ===")
    
    try:
        # This will use the provider specified in EMBEDDING_PROVIDER env var
        client = create_embedding_client()
        print(f"Auto-detected provider: {client.__class__.__name__}")
        
        # Generate embedding for a single text
        text = "The quick brown fox jumps over the lazy dog"
        embedding = client.generate_embedding(text)
        print(f"Generated embedding with dimension: {len(embedding)}")
        
    except Exception as e:
        print(f"Auto-detection failed: {e}")
        print("Set EMBEDDING_PROVIDER environment variable (openai, google_genai, ollama, local)")
    print()


def example_openai_embeddings():
    """Example using OpenAI embeddings."""
    print("=== OpenAI Embeddings Example ===")
    
    try:
        # Create OpenAI client with specific model
        client = create_openai_client(
            model="text-embedding-3-small",
            # api_key="your-api-key-here"  # Or set OPENAI_API_KEY env var
        )
        
        # Single text embedding
        text = "Natural language processing with embeddings"
        embedding = client.generate_embedding(text)
        print(f"Single embedding dimension: {len(embedding)}")
        
        # Batch embeddings
        texts = [
            "Machine learning is fascinating",
            "Deep learning revolutionizes AI",
            "Transformers changed everything"
        ]
        embeddings = client.generate_embedding(texts)
        print(f"Batch embeddings: {len(embeddings)} texts, {len(embeddings[0])} dimensions each")
        
        # Custom dimensions (for supported models)
        client_custom = create_openai_client(
            model="text-embedding-3-small",
            embedding_dim=512  # Reduce dimensions
        )
        
        print(f"Model info: {client.get_model_info()}")
        
    except Exception as e:
        print(f"OpenAI example failed: {e}")
        print("Make sure to set OPENAI_API_KEY environment variable")
    print()


def example_google_genai_embeddings():
    """Example using Google GenAI embeddings with task types."""
    print("=== Google GenAI Embeddings Example ===")
    
    try:
        # Create Google GenAI client with task type
        client = create_google_genai_client(
            model="text-embedding-004",
            task_type=TaskType.SEMANTIC_SIMILARITY,
            # api_key="your-google-api-key"  # Or set GOOGLE_GENAI_API_KEY env var
        )
        
        # Semantic similarity task
        texts = [
            "The cat sat on the mat",
            "A feline rested on the rug"
        ]
        embeddings = client.generate_embedding(texts)
        print(f"Semantic similarity embeddings: {len(embeddings)} texts")
        
        # Classification task
        client_classify = create_google_genai_client(
            task_type=TaskType.CLASSIFICATION,
            title="Document Classification"  # Optional title
        )
        
        classification_texts = [
            "This is a positive review",
            "This product is terrible"
        ]
        class_embeddings = client_classify.generate_embedding(classification_texts)
        print(f"Classification embeddings: {len(class_embeddings)} texts")
        
        print(f"Supported task types: {client.get_supported_task_types()}")
        
    except Exception as e:
        print(f"Google GenAI example failed: {e}")
        print("Make sure to set GOOGLE_GENAI_API_KEY or GEMINI_API_KEY environment variable")
    print()


def example_local_embeddings():
    """Example using local HuggingFace models."""
    print("=== Local Embeddings Example ===")
    
    try:
        # Create local client with sentence-transformers
        client = create_local_client(
            model="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu",  # or "cuda" if available
            use_sentence_transformers=True
        )
        
        # Generate embeddings locally
        texts = [
            "Local embedding generation",
            "No API calls required",
            "Privacy-friendly approach"
        ]
        embeddings = client.generate_embedding(texts)
        print(f"Local embeddings: {len(embeddings)} texts, {len(embeddings[0])} dimensions each")
        
        print(f"Model info: {client.get_model_info()}")
        print(f"Popular models: {client.get_popular_models()[:3]}")  # Show first 3
        
        # Health check
        if client.health_check():
            print("Local model is working correctly")
        
    except Exception as e:
        print(f"Local embeddings example failed: {e}")
        print("Install with: pip install sentence-transformers")
    print()


def example_ollama_embeddings():
    """Example using Ollama embeddings."""
    print("=== Ollama Embeddings Example ===")
    
    try:
        client = create_ollama_client(
            model="nomic-embed-text"  # or another embedding model in Ollama
        )
        
        text = "Ollama local embedding generation"
        embedding = client.generate_embedding(text)
        print(f"Ollama embedding dimension: {len(embedding)}")
        
    except Exception as e:
        print(f"Ollama example failed: {e}")
        print("Make sure Ollama is running and has an embedding model installed")
    print()


def example_factory_patterns():
    """Example using the factory class directly."""
    print("=== Factory Pattern Examples ===")
    
    try:
        # Method 1: Auto-detect from environment
        print("1. Auto-detect from environment:")
        try:
            client = EmbeddingFactory.create()
            print(f"   Created: {client.__class__.__name__}")
        except Exception as e:
            print(f"   Auto-detection failed: {e}")
        
        # Method 2: Specify provider with parameters
        print("2. Explicit provider selection:")
        try:
            client = EmbeddingFactory.create(
                provider="openai",
                model="text-embedding-3-small"
            )
            print(f"   Created: {client.__class__.__name__}")
        except Exception as e:
            print(f"   OpenAI creation failed: {e}")
        
        # Method 3: Provider-specific factory methods
        print("3. Provider-specific methods:")
        try:
            openai_client = EmbeddingFactory.openai(model="text-embedding-3-large")
            print(f"   OpenAI: {openai_client.__class__.__name__}")
        except Exception as e:
            print(f"   OpenAI method failed: {e}")
            
        try:
            google_client = EmbeddingFactory.google_genai(
                task_type=TaskType.CLUSTERING
            )
            print(f"   Google: {google_client.__class__.__name__}")
        except Exception as e:
            print(f"   Google method failed: {e}")
        
        # Method 4: From configuration object
        print("4. From configuration object:")
        try:
            from core_lib.embeddings import EmbeddingsConfig
            config = EmbeddingsConfig(
                provider="openai",
                model="text-embedding-3-small",
                task_type=TaskType.SEMANTIC_SIMILARITY.value
            )
            client = EmbeddingFactory.from_config(config)
            print(f"   From config: {client.__class__.__name__}")
        except Exception as e:
            print(f"   Config creation failed: {e}")
            
    except Exception as e:
        print(f"Factory examples failed: {e}")
    print()


def example_task_types():
    """Example showing different task types."""
    print("=== Task Types Example ===")
    
    # Show all available task types
    print("Available task types:")
    for task_type in TaskType:
        print(f"  - {task_type.value}")
    
    # Example of using different task types with Google GenAI
    task_examples = {
        TaskType.SEMANTIC_SIMILARITY: [
            "The cat is sleeping",
            "A feline is resting"
        ],
        TaskType.CLASSIFICATION: [
            "This movie is amazing!",
            "This film is terrible."
        ],
        TaskType.CLUSTERING: [
            "Technology news article",
            "Sports match report",
            "Weather forecast update"
        ]
    }
    
    for task_type, texts in task_examples.items():
        try:
            print(f"\nTask type: {task_type.value}")
            client = create_google_genai_client(
                task_type=task_type.value,
                model="text-embedding-004"
            )
            embeddings = client.generate_embedding(texts)
            print(f"  Generated {len(embeddings)} embeddings for {task_type.value}")
        except Exception as e:
            print(f"  {task_type.value} failed: {e}")
    print()


def example_performance_comparison():
    """Example comparing different providers (mock timing)."""
    print("=== Provider Performance Comparison ===")
    
    test_text = "This is a test sentence for performance comparison."
    
    providers = [
        ("OpenAI", lambda: create_openai_client()),
        ("Google GenAI", lambda: create_google_genai_client()),
        ("Ollama", lambda: create_ollama_client()),
        ("Local", lambda: create_local_client()),
    ]
    
    for provider_name, client_factory in providers:
        try:
            client = client_factory()
            embedding = client.generate_embedding(test_text)
            time_ms = client.get_embedding_time_ms()
            print(f"{provider_name:12}: {len(embedding):4d} dims, {time_ms:6.1f}ms")
        except Exception as e:
            print(f"{provider_name:12}: Failed - {e}")
    print()


if __name__ == "__main__":
    print("core-lib Embeddings Examples")
    print("=" * 40)
    
    # Run examples (some may fail if dependencies/API keys not available)
    example_auto_detection()
    # example_openai_embeddings()  # Requires API key
    # example_google_genai_embeddings()  # Requires API key
    # example_local_embeddings()  # Requires sentence-transformers
    example_ollama_embeddings()  # Requires local Ollama
    example_factory_patterns()
    example_task_types()
    # example_performance_comparison()  # Requires various providers