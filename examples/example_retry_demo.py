#!/usr/bin/env python3
"""
Demo script showing the retry functionality in faciliter_lib.

This example demonstrates:
1. The generic retry decorator with different strategies
2. How the GoogleGenAIProvider uses retry logic internally
3. Simulated failure scenarios to show retry behavior
"""

import time
from faciliter_lib.llm.retry import RetryConfig, RetryStrategy, retry_handler


class SimulatedAPIError(Exception):
    """Simulates an API error for demonstration."""
    pass


# Example 1: Basic retry with exponential backoff
@retry_handler(RetryConfig(
    max_retries=3,
    base_delay=0.1,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    retry_on_exceptions=(SimulatedAPIError,)
))
def flaky_api_call(success_on_attempt: int = 3):
    """Simulates an API call that fails until the specified attempt."""
    if not hasattr(flaky_api_call, 'attempt_count'):
        flaky_api_call.attempt_count = 0
    
    flaky_api_call.attempt_count += 1
    print(f"  API call attempt #{flaky_api_call.attempt_count}")
    
    if flaky_api_call.attempt_count < success_on_attempt:
        raise SimulatedAPIError(f"Simulated failure on attempt {flaky_api_call.attempt_count}")
    
    return {"status": "success", "attempt": flaky_api_call.attempt_count}


# Example 2: Fixed delay retry
@retry_handler(RetryConfig(
    max_retries=2,
    base_delay=0.1,
    strategy=RetryStrategy.FIXED_DELAY,
    retry_on_exceptions=(SimulatedAPIError,)
))
def another_flaky_call():
    """Always fails to demonstrate max retries."""
    print("  Attempting call that will always fail...")
    raise SimulatedAPIError("This always fails")


def main():
    print("🔄 Demonstrating retry functionality\n")
    
    # Example 1: Successful retry after failures
    print("1️⃣ Example: API call succeeds on 3rd attempt")
    try:
        result = flaky_api_call(success_on_attempt=3)
        print(f"✅ Success: {result}\n")
    except Exception as e:
        print(f"❌ Failed: {e}\n")
    
    # Reset counter for next test
    delattr(flaky_api_call, 'attempt_count')
    
    # Example 2: All retries exhausted
    print("2️⃣ Example: API call fails after all retries")
    try:
        result = another_flaky_call()
        print(f"✅ Success: {result}\n")
    except Exception as e:
        print(f"❌ Failed after all retries: {e}\n")
    
    # Example 3: Show GoogleGenAI retry configuration
    print("3️⃣ GoogleGenAI Provider Retry Configuration:")
    print("   - Max retries: 3")
    print("   - Strategy: Exponential backoff")
    print("   - Base delay: 1.0s")
    print("   - Max delay: 60.0s")
    print("   - Retries on: Rate limits, server errors, network issues")
    print("   - Jitter: 50% to prevent thundering herd\n")
    
    print("✨ Retry demo completed!")


if __name__ == "__main__":
    main()