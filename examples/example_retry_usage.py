"""Example demonstrating retry logic and rate limiting in GoogleGenAIProvider.

This script shows how the provider handles transient failures with automatic
retries and respects model-specific rate limits.
"""

import time
from typing import Dict, Any

from faciliter_lib.llm.retry import RetryConfig, retry_handler, RetryStrategy
from faciliter_lib.llm.providers.google_genai_provider import GoogleGenAIProvider, GeminiConfig


def example_basic_retry():
    """Demonstrate basic retry functionality with a simple function."""
    print("=== Basic Retry Example ===")
    
    # Configure retry with exponential backoff
    retry_config = RetryConfig(
        max_retries=3,
        base_delay=0.5,
        max_delay=5.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retry_on_exceptions=(ValueError, ConnectionError),
    )
    
    attempt_count = 0
    
    @retry_handler(retry_config)
    def flaky_function(should_succeed_on_attempt: int = 3) -> str:
        nonlocal attempt_count
        attempt_count += 1
        print(f"  Attempt {attempt_count}")
        
        if attempt_count < should_succeed_on_attempt:
            raise ValueError(f"Simulated failure on attempt {attempt_count}")
        
        return f"Success on attempt {attempt_count}!"
    
    try:
        result = flaky_function(should_succeed_on_attempt=3)
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Final failure: {e}")
    
    print()


def example_provider_rate_limiting():
    """Show how GoogleGenAIProvider respects model-specific rate limits."""
    print("=== Rate Limiting Example ===")
    
    # Different models have different RPM limits
    models_and_limits = [
        ("gemini-2.5-pro", 5),        # 5 RPM
        ("gemini-2.5-flash", 10),     # 10 RPM
        ("gemini-2.5-flash-lite", 15), # 15 RPM
        ("gemma-3", 30),              # 30 RPM
    ]
    
    for model, expected_rpm in models_and_limits:
        config = GeminiConfig(
            api_key="fake-key-for-demo",  # Won't actually call API
            model=model,
        )
        provider = GoogleGenAIProvider(config)
        
        print(f"  Model: {model}")
        print(f"    Expected RPM: {expected_rpm}")
        print(f"    Rate limiter RPM: {provider._rate_limiter.config.requests_per_minute}")
        print(f"    Rate limiter RPS: {provider._rate_limiter.config.requests_per_second:.3f}")
        print()


def example_retry_strategies():
    """Demonstrate different retry strategies."""
    print("=== Retry Strategies Example ===")
    
    strategies = [
        (RetryStrategy.EXPONENTIAL_BACKOFF, "Exponential Backoff"),
        (RetryStrategy.LINEAR_BACKOFF, "Linear Backoff"),
        (RetryStrategy.FIXED_DELAY, "Fixed Delay"),
    ]
    
    for strategy, name in strategies:
        print(f"  {name}:")
        
        retry_config = RetryConfig(
            max_retries=4,
            base_delay=0.1,  # Small delay for demo
            strategy=strategy,
            retry_on_exceptions=(RuntimeError,),
        )
        
        attempt_count = 0
        
        @retry_handler(retry_config)
        def always_fail():
            nonlocal attempt_count
            attempt_count += 1
            print(f"    Attempt {attempt_count} at {time.time():.2f}")
            raise RuntimeError("Always fails")
        
        start_time = time.time()
        try:
            always_fail()
        except RuntimeError:
            total_time = time.time() - start_time
            print(f"    Total time: {total_time:.2f}s with {attempt_count} attempts")
        
        attempt_count = 0  # Reset for next strategy
        print()


if __name__ == "__main__":
    print("Retry and Rate Limiting Examples")
    print("=" * 40)
    print()
    
    example_basic_retry()
    example_provider_rate_limiting()
    example_retry_strategies()
    
    print("Note: The GoogleGenAIProvider examples don't make actual API calls")
    print("since no valid API key is provided. In real usage, the retry logic")
    print("would handle actual network failures, rate limits, and server errors.")