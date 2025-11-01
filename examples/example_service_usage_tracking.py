"""Example demonstrating service usage tracking with OpenTelemetry/OpenSearch.

This example shows how to:
1. Enable OTLP logging to send metrics to OpenSearch
2. Use LLM and embedding services with automatic usage tracking
3. Add request context (user_id, session_id) for better analytics
4. Query and analyze service usage in OpenSearch

No span management or Langfuse context required!
"""

import asyncio
import os
from typing import Optional

# Configure environment (in production, use .env file)
os.environ.update({
    "OTLP_ENABLED": "true",
    "OTLP_ENDPOINT": "http://localhost:4318/v1/logs",
    "OTLP_SERVICE_NAME": "service-usage-example",
    "LOG_LEVEL": "INFO",
    "OPENAI_API_KEY": "your-api-key-here",
})

from faciliter_lib.config.logger_settings import LoggerSettings
from faciliter_lib.tracing import (
    setup_logging,
    LoggingContext,
    get_module_logger,
)
from faciliter_lib.llm import create_openai_client
from faciliter_lib.embeddings import create_openai_embedding_client


logger = get_module_logger()


def setup():
    """Initialize logging with OTLP for service usage tracking."""
    logger_settings = LoggerSettings(
        otlp_enabled=True,
        otlp_endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4318/v1/logs"),
        otlp_service_name=os.getenv("OTLP_SERVICE_NAME", "faciliter-lib"),
        otlp_service_version="1.0.0",
        log_level="INFO",
    )
    
    setup_logging(logger_settings=logger_settings, app_name="service-usage-example")
    logger.info("Service usage tracking enabled - metrics will be sent to OpenSearch")


async def example_llm_usage():
    """Demonstrate LLM usage tracking with cost calculation."""
    logger.info("=== LLM Usage Tracking Example ===")
    
    # Create LLM client
    client = create_openai_client(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",  # Cost-effective model
    )
    
    # Simulate a user request with context
    user_context = {
        "user_id": "user-12345",
        "session_id": "sess-abc-xyz",
        "company_id": "acme-corp",
        "app_name": "customer-support-bot",
        "app_version": "2.1.0",
    }
    
    # Use LoggingContext to add metadata - automatically included in all logs
    with LoggingContext(user_context):
        logger.info("Processing LLM request for user", extra={
            "extra_attrs": {"request_type": "chat"}
        })
        
        # This will automatically log to OpenSearch:
        # - service.type: "llm"
        # - service.provider: "openai"
        # - service.model: "gpt-4o-mini"
        # - tokens.input, tokens.output, tokens.total
        # - cost_usd (automatically calculated)
        # - latency_ms
        # - user.id, session.id, organization.id (from LoggingContext)
        response = client.chat(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"},
            ]
        )
        
        logger.info(f"LLM Response: {response['content'][:100]}...")
    
    # Example with structured output
    from pydantic import BaseModel
    
    class CityInfo(BaseModel):
        name: str
        country: str
        population: int
        
    with LoggingContext(user_context):
        logger.info("Processing structured LLM request")
        
        # This will log with features.structured_output: true
        response = client.chat(
            messages=[
                {"role": "user", "content": "Give me info about Paris, France"}
            ],
            structured_output=CityInfo,
        )
        
        logger.info(f"Structured response: {response['structured']}")


async def example_embedding_usage():
    """Demonstrate embedding usage tracking with cost calculation."""
    logger.info("=== Embedding Usage Tracking Example ===")
    
    # Create embedding client
    client = create_openai_embedding_client(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="text-embedding-3-small",  # Most cost-effective
    )
    
    # Simulate semantic search request
    user_context = {
        "user_id": "user-67890",
        "session_id": "sess-def-uvw",
        "company_id": "acme-corp",
    }
    
    with LoggingContext(user_context):
        logger.info("Generating embeddings for document search")
        
        texts = [
            "What is machine learning?",
            "How do neural networks work?",
            "Explain deep learning basics",
            "What are transformers in AI?",
            "Introduction to large language models",
        ]
        
        # This will automatically log to OpenSearch:
        # - service.type: "embedding"
        # - service.provider: "openai"
        # - service.model: "text-embedding-3-small"
        # - tokens.input (estimated or actual)
        # - embedding.num_texts: 5
        # - embedding.dimension: 1536
        # - cost_usd (automatically calculated)
        # - latency_ms
        embeddings = client.generate_embedding(texts)
        
        logger.info(f"Generated {len(embeddings)} embeddings, dimension: {len(embeddings[0])}")


async def example_multiple_services():
    """Demonstrate tracking multiple services in one request."""
    logger.info("=== Multiple Services Tracking Example ===")
    
    llm_client = create_openai_client(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )
    
    embedding_client = create_openai_embedding_client(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="text-embedding-3-small",
    )
    
    # RAG-style workflow: embed query, then generate answer
    user_context = {
        "user_id": "user-rag-123",
        "session_id": "sess-rag-456",
        "company_id": "acme-corp",
    }
    
    with LoggingContext(user_context):
        logger.info("Starting RAG pipeline")
        
        # Step 1: Embed the user query
        query = "What are the benefits of renewable energy?"
        query_embedding = embedding_client.generate_embedding([query])
        logger.info("Query embedded")
        
        # Step 2: Simulate retrieval (would query vector DB in real app)
        context_docs = [
            "Renewable energy reduces carbon emissions and helps fight climate change.",
            "Solar and wind power are cost-effective and sustainable energy sources.",
        ]
        
        # Step 3: Generate LLM response with context
        prompt = f"Context: {' '.join(context_docs)}\n\nQuestion: {query}\n\nAnswer:"
        response = llm_client.chat(
            messages=[{"role": "user", "content": prompt}]
        )
        
        logger.info(f"RAG response: {response['content'][:100]}...")
        
        # Both embedding and LLM usage are now logged separately in OpenSearch
        # You can query for total cost of this session using session.id


async def example_error_tracking():
    """Demonstrate error tracking in service usage logs."""
    logger.info("=== Error Tracking Example ===")
    
    client = create_openai_client(
        api_key="invalid-key",  # Intentionally invalid
        model="gpt-4o-mini",
    )
    
    user_context = {
        "user_id": "user-error-test",
        "session_id": "sess-error-test",
    }
    
    with LoggingContext(user_context):
        try:
            # This will fail and log an error event with:
            # - status: "error"
            # - error: "authentication failed..."
            # - All other metrics (provider, model, etc.)
            response = client.chat(
                messages=[{"role": "user", "content": "Hello"}]
            )
        except Exception as e:
            logger.error(f"LLM request failed (expected): {e}")
            logger.info("Error was logged to OpenSearch with full context")


def print_opensearch_query_examples():
    """Print example OpenSearch queries for analyzing service usage."""
    logger.info("=== OpenSearch Query Examples ===")
    
    print("""
1. Total cost in last 24 hours:
   
   GET /logs-*/_search
   {
     "size": 0,
     "query": {
       "bool": {
         "must": [
           {"exists": {"field": "attributes.service.type"}},
           {"range": {"@timestamp": {"gte": "now-24h"}}}
         ]
       }
     },
     "aggs": {
       "total_cost": {"sum": {"field": "attributes.cost_usd"}},
       "by_service": {
         "terms": {"field": "attributes.service.type"},
         "aggs": {"cost": {"sum": {"field": "attributes.cost_usd"}}}
       }
     }
   }

2. Usage by user:
   
   GET /logs-*/_search
   {
     "size": 0,
     "query": {
       "term": {"attributes.user.id": "user-12345"}
     },
     "aggs": {
       "total_cost": {"sum": {"field": "attributes.cost_usd"}},
       "total_tokens": {"sum": {"field": "attributes.tokens.total"}},
       "by_service": {
         "terms": {"field": "attributes.service.type"}
       }
     }
   }

3. Performance metrics:
   
   GET /logs-*/_search
   {
     "size": 0,
     "query": {"term": {"attributes.service.type": "llm"}},
     "aggs": {
       "latency_stats": {"stats": {"field": "attributes.latency_ms"}},
       "by_model": {
         "terms": {"field": "attributes.service.model"},
         "aggs": {
           "avg_latency": {"avg": {"field": "attributes.latency_ms"}},
           "p95_latency": {
             "percentiles": {"field": "attributes.latency_ms", "percents": [95]}
           }
         }
       }
     }
   }

4. Error rate:
   
   GET /logs-*/_search
   {
     "size": 0,
     "aggs": {
       "total": {"value_count": {"field": "_id"}},
       "errors": {"filter": {"term": {"attributes.status": "error"}}}
     }
   }
    """)


async def main():
    """Run all examples."""
    # Setup OTLP logging
    setup()
    
    # Wait a moment for setup
    await asyncio.sleep(1)
    
    # Run examples
    try:
        await example_llm_usage()
        await asyncio.sleep(1)
        
        await example_embedding_usage()
        await asyncio.sleep(1)
        
        await example_multiple_services()
        await asyncio.sleep(1)
        
        # Uncomment to test error tracking
        # await example_error_tracking()
        # await asyncio.sleep(1)
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
    
    # Print query examples
    print_opensearch_query_examples()
    
    logger.info("""
=== Summary ===

All service usage has been logged to OpenSearch with:
✓ Service type, provider, and model
✓ Token usage and cost (automatically calculated)
✓ Performance metrics (latency, throughput)
✓ User context (user_id, session_id, company_id)
✓ Error tracking with full context

Next steps:
1. Configure OpenSearch endpoint in OTLP_ENDPOINT environment variable
2. Create dashboards in OpenSearch for cost analysis, usage trends, and performance
3. Set up alerts for high cost, errors, or slow requests
4. Use the example queries above to analyze your data

No Langfuse spans required! 🎉
""")


if __name__ == "__main__":
    asyncio.run(main())
