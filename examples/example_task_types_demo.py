#!/usr/bin/env python3
"""
Demo script showing the official Google GenAI task types, including RETRIEVAL_DOCUMENT and RETRIEVAL_QUERY.

This script demonstrates all available task types in the embeddings module.
"""

from core_lib.embeddings import TaskType, EmbeddingFactory
import os

def demonstrate_task_types():
    """Demonstrate all available task types."""
    print("=== Official Google GenAI Task Types Demo ===\n")
    
    # Show all available task types
    print("Available TaskType values:")
    for task_type in TaskType:
        print(f"  - {task_type.value}")
    print()
    
    # Example usage of RETRIEVAL_DOCUMENT and RETRIEVAL_QUERY
    print("Example: Creating embedding clients with RETRIEVAL task types")
    
    # Example for document indexing
    print("\n1. RETRIEVAL_DOCUMENT (for indexing documents):")
    try:
        doc_client = EmbeddingFactory.google_genai(
            task_type=TaskType.RETRIEVAL_DOCUMENT,
            model="text-embedding-004"
        )
        print(f"   ✓ Created client with task type: {TaskType.RETRIEVAL_DOCUMENT}")
        print("   Use this for: Embedding documents for retrieval systems")
    except Exception as e:
        print(f"   ⚠ Mock client created (Google GenAI not configured): {type(e).__name__}")
    
    # Example for query processing  
    print("\n2. RETRIEVAL_QUERY (for search queries):")
    try:
        query_client = EmbeddingFactory.google_genai(
            task_type=TaskType.RETRIEVAL_QUERY,
            model="text-embedding-004"  
        )
        print(f"   ✓ Created client with task type: {TaskType.RETRIEVAL_QUERY}")
        print("   Use this for: Embedding user queries for retrieval systems")
    except Exception as e:
        print(f"   ⚠ Mock client created (Google GenAI not configured): {type(e).__name__}")
    
    # Show other task types
    print("\n3. Other Available Task Types:")
    other_types = [
        (TaskType.SEMANTIC_SIMILARITY, "Similarity search and comparison"),
        (TaskType.CLASSIFICATION, "Text classification tasks"),
        (TaskType.CLUSTERING, "Grouping similar content"),
        (TaskType.CODE_RETRIEVAL_QUERY, "Code search queries"),
        (TaskType.QUESTION_ANSWERING, "Q&A systems"),
        (TaskType.FACT_VERIFICATION, "Fact-checking applications"),
    ]
    
    for task_type, description in other_types:
        print(f"   {task_type.value}: {description}")
    
    print("\n=== Configuration Example ===")
    print("To use with environment variables:")
    print("export GEMINI_API_KEY='your-key-here'")
    print("export EMBEDDING_PROVIDER='google-genai'")
    print("export EMBEDDING_TASK_TYPE='RETRIEVAL_DOCUMENT'")
    print()
    print("Then create client from environment:")
    print("client = EmbeddingFactory.from_env()")

if __name__ == "__main__":
    demonstrate_task_types()