# Example usage of the new TracingManager

from faciliter_lib.tracing import TracingManager, setup_tracing

# Option 1: Using the new TracingManager class
def example_with_manager():
    # Initialize the tracing manager
    tracing_manager = TracingManager("my-service")
    
    # Setup tracing
    tracing_provider = tracing_manager.setup()
    
    # Add metadata to the current trace
    metadata = {
        "user_id": "12345",
        "operation": "data_processing",
        "version": "1.2.3"
    }
    tracing_manager.add_metadata(metadata)
    
    # Add more metadata with tags
    tracing_manager.add_metadata({
        "name": "process_data",
        "tags": ["processing", "important"]
    })

# Option 2: Using the backward-compatible function
def example_with_function():
    # Setup tracing (backward compatible)
    tracing_provider = setup_tracing("my-service")
    
    # Add metadata
    metadata = {
        "user_id": "12345",
        "operation": "data_processing"
    }
    tracing_provider.add_metadata(metadata)
    
    # Add more metadata with tags
    tracing_provider.add_metadata({
        "name": "process_data",
        "tags": ["processing"]
    })

if __name__ == "__main__":
    print("Example usage of the new tracing API")
    example_with_manager()
    example_with_function()
