"""Example: Using Infinity Embedding Provider with core-lib

This example demonstrates how to use the Infinity embedding provider
to generate embeddings using a local Infinity server.

Prerequisites:
1. Infinity server running on http://localhost:7997
2. core-lib installed with: pip install core-lib

Start Infinity server:
  docker run -d -p 7997:7997 michaelf34/infinity:latest --model-name-or-path BAAI/bge-small-en-v1.5
"""

from core_lib.embeddings import create_infinity_client, create_embedding_client

def example_basic_usage():
    """Basic usage with explicit Infinity client creation."""
    print("=" * 60)
    print("Example 1: Basic Infinity Usage")
    print("=" * 60)
    
    # Create Infinity client
    client = create_infinity_client(
        model="BAAI/bge-small-en-v1.5",
        base_url="http://localhost:7997",
        embedding_dim=384
    )
    
    # Generate single embedding
    text = "Hello, this is a test sentence for embeddings."
    embedding = client.generate_embedding(text)
    print(f"\nGenerated embedding for: '{text}'")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print(f"Generation time: {client.get_embedding_time_ms():.2f}ms")


def example_batch_processing():
    """Batch processing multiple texts at once."""
    print("\n" + "=" * 60)
    print("Example 2: Batch Processing")
    print("=" * 60)
    
    client = create_infinity_client()
    
    texts = [
        "Machine learning is a subset of artificial intelligence.",
        "Python is a popular programming language.",
        "Natural language processing enables computers to understand text.",
        "Deep learning uses neural networks with many layers."
    ]
    
    # Generate embeddings for all texts
    embeddings = client.generate_embedding(texts)
    print(f"\nGenerated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")
    print(f"Total processing time: {client.get_embedding_time_ms():.2f}ms")
    print(f"Average per text: {client.get_embedding_time_ms() / len(texts):.2f}ms")


def example_auto_detection():
    """Auto-detection from environment variables."""
    print("\n" + "=" * 60)
    print("Example 3: Auto-Detection from Environment")
    print("=" * 60)
    
    # Set environment variables:
    # EMBEDDING_PROVIDER=infinity
    # EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
    # INFINITY_URL=http://localhost:7997
    
    import os
    os.environ['EMBEDDING_PROVIDER'] = 'infinity'
    os.environ['EMBEDDING_MODEL'] = 'BAAI/bge-small-en-v1.5'
    os.environ['INFINITY_URL'] = 'http://localhost:7997'
    os.environ['EMBEDDING_DIMENSION'] = '384'
    
    # Create client with auto-detection
    client = create_embedding_client()
    
    text = "This text is embedded using auto-detected Infinity provider."
    embedding = client.generate_embedding(text)
    print(f"\nAuto-detected provider and generated embedding")
    print(f"Text: '{text}'")
    print(f"Embedding dimension: {len(embedding)}")


def example_health_check():
    """Check Infinity server health."""
    print("\n" + "=" * 60)
    print("Example 4: Health Check")
    print("=" * 60)
    
    client = create_infinity_client()
    
    if client.health_check():
        print("\n✓ Infinity server is healthy and responding")
        
        # Get available models
        models = client.get_available_models()
        print(f"\nAvailable models on server:")
        for model in models:
            print(f"  - {model}")
        
        # Get current model info
        info = client.get_model_info()
        print(f"\nCurrent model information:")
        print(f"  Model ID: {info.get('id', 'N/A')}")
        print(f"  Backend: {info.get('backend', 'N/A')}")
        print(f"  Capabilities: {info.get('capabilities', [])}")
    else:
        print("\n✗ Infinity server is not responding")
        print("  Make sure Infinity is running on http://localhost:7997")


def example_caching():
    """Demonstrate automatic caching."""
    print("\n" + "=" * 60)
    print("Example 5: Automatic Caching")
    print("=" * 60)
    
    client = create_infinity_client()
    
    text = "This text will be cached after first generation."
    
    # First call - generates embedding
    print("\nFirst call (generates embedding):")
    embedding1 = client.generate_embedding(text)
    time1 = client.get_embedding_time_ms()
    print(f"  Time: {time1:.2f}ms")
    
    # Second call - returns from cache
    print("\nSecond call (from cache):")
    embedding2 = client.generate_embedding(text)
    time2 = client.get_embedding_time_ms()
    print(f"  Time: {time2:.2f}ms")
    
    # Verify embeddings are identical
    print(f"\nEmbeddings identical: {embedding1 == embedding2}")
    print(f"Speedup: {time1 / time2:.1f}x faster")


def example_similarity_computation():
    """Compute similarity between texts."""
    print("\n" + "=" * 60)
    print("Example 6: Computing Text Similarity")
    print("=" * 60)
    
    import numpy as np
    
    client = create_infinity_client()
    
    # Example texts
    text1 = "The cat sat on the mat."
    text2 = "A cat was sitting on the mat."
    text3 = "Python is a programming language."
    
    # Generate embeddings
    embeddings = client.generate_embedding([text1, text2, text3])
    
    # Compute cosine similarities
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_1_2 = cosine_similarity(embeddings[0], embeddings[1])
    sim_1_3 = cosine_similarity(embeddings[0], embeddings[2])
    sim_2_3 = cosine_similarity(embeddings[1], embeddings[2])
    
    print(f"\nSimilarities:")
    print(f"  Text 1 vs Text 2: {sim_1_2:.4f} (similar sentences)")
    print(f"  Text 1 vs Text 3: {sim_1_3:.4f} (different topics)")
    print(f"  Text 2 vs Text 3: {sim_2_3:.4f} (different topics)")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Infinity Embedding Provider Examples" + " " * 11 + "║")
    print("╚" + "═" * 58 + "╝")
    
    try:
        example_basic_usage()
        example_batch_processing()
        example_auto_detection()
        example_health_check()
        example_caching()
        example_similarity_computation()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("\nMake sure:")
        print("  1. Infinity server is running on http://localhost:7997")
        print("  2. Run: docker run -d -p 7997:7997 michaelf34/infinity:latest --model-name-or-path BAAI/bge-small-en-v1.5")
        print("  3. core-lib is installed with requests: pip install requests")


if __name__ == "__main__":
    main()
