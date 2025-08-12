"""Example usage of the LLM client functionality."""

import os
# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pydantic import BaseModel
from typing import List, Optional
from faciliter_lib import create_ollama_client, create_gemini_client, create_client_from_env


# Example structured output model
class WeatherResponse(BaseModel):
    location: str
    temperature: float
    condition: str
    humidity: Optional[int] = None


def example_basic_chat():
    """Example of basic chat functionality."""
    print("=== Basic Chat Example ===")
    
    # Create an Ollama client
    client = create_ollama_client(
        model="qwen3:1.7b",
        temperature=0.7,
        thinking_enabled=True
    )
    
    # Simple chat
    response = client.chat("What is the capital of France?")
    print("Response:", response["content"])
    print("Usage:", response["usage"])
    print()


def example_chat_with_history():
    """Example of chat with message history."""
    print("=== Chat with History Example ===")
    
    client = create_ollama_client(model="qwen3:1.7b")
    
    # Chat with conversation history
    messages = [
        {"role": "user", "content": "Hello, I'm planning a trip to Japan."},
        {"role": "assistant", "content": "That's exciting! Japan is a wonderful destination. What would you like to know about your trip?"},
        {"role": "user", "content": "What are some must-visit places in Tokyo?"}
    ]
    
    response = client.chat(messages, system_message="You are a helpful travel assistant.")
    print("Response:", response["content"])
    print()


def example_structured_output():
    """Example of getting structured JSON output."""
    print("=== Structured Output Example ===")

    # client = create_ollama_client(model="qwen3:1.7b")
    client = create_client_from_env()  # "ollama" or "gemini"
    # Request structured output
    response = client.chat(
        "What's the weather like in Paris today?",
        structured_output=WeatherResponse
    )
    
    if response["structured"] and not response.get("error"):
        weather_data = response["content"]
        print("Structured weather data:", weather_data)
    else:
        print("Error getting structured output:", response.get("error"))
    print()


def example_tools():
    """Example of using tools with the LLM."""
    print("=== Tools Example ===")

    client = create_client_from_env()  # "ollama" or "gemini"

    # Define tools in OpenAI format
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather information for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and country, e.g. 'Paris, France'"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    response = client.chat(
        "What's the weather like in Tokyo? Use tools if needed.",
        tools=tools
    )
    
    print("Response:", response["content"])
    print("Tool calls:", response["tool_calls"])
    print()


def example_gemini_client():
    """Example using Gemini client (requires API key)."""
    print("=== Gemini Client Example ===")
    
    # This would require a valid API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
    
    if api_key:
        client = create_gemini_client(
            api_key=api_key,
            model="gemini-1.5-flash",
            temperature=0.3
        )
        
        response = client.chat("Explain quantum computing in simple terms.")
        print("Gemini Response:", response["content"])
    else:
        print("GEMINI_API_KEY not set - skipping Gemini example")
    print()


def example_from_env():
    """Example of creating client from environment variables."""
    print("=== Client from Environment Example ===")
    
    # This will use environment variables for configuration
    try:
        client = create_client_from_env()  # "ollama" or "gemini"
        
        model_info = client.get_model_info()
        print("Model info:", model_info)
        
        response = client.chat("Tell me a short joke about programming.")
        print("Response:", response["content"])
    except Exception as e:
        print(f"Error creating client from environment: {e}")
    print()


if __name__ == "__main__":
    # Run examples (commented out ones that might not work without proper setup)
    # example_basic_chat()
    # example_chat_with_history() 
    # example_structured_output()  # Might not work with all models
    # example_tools()  # Might not work with all models
    example_gemini_client()  # Requires API key
    # example_from_env()
