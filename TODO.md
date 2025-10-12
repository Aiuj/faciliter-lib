# Faciliter lib roadmap

## Changes done

### 0.2.10

- Implemented a dynamic api key authentication mechanism
- Added infinity server provider for embeddings
- Better settings singleton management
- Basic job queue implementation using Redis/Valkey

### 0.2.9

- Manage multi-tenancy on the cache manager
- Add methods to clear cache (global or company/related)
- Add better logging settings
- Add capability to log in local files

### 0.2.8

- Add a standard settings class to ease configuration management across all applications
- New fastAPI default configuration
- Add a connection pooling and healthcheck on cache manager (Redis and ValKey)

### 0.2.7

- Manage rate limits with retries on Google genai models

### 0.2.6

- Added returning the list of detected languages in the language detection utility
- Now cache embeddings for 24h in the memory cache
- Better manage excel file and byte loading with closing the file at the end

### 0.2.5

- Implementation of a file utils to create temporary files from MCP file objects
- Modified the cache manager to use valkey, a drop in open source replacement of Redis

### 0.2.4

- Implemented Embeddings module with Ollama, Google, OpenAI and local models

### 0.2.3

- Added an hardcoded list of categories for business documents in config
- Added ExcelManager in tools to convert Excel into Markdown or Json IR structure

## LLM client roadmap

- Add Tracing observability
- Add OpenAI model API
- Implement SGLang local model interface, especially for embeddings
- Implement a reranker implementation similar to the embedding
- Implement LangChain and LlamaIndex abstraction wrappers
- Add a circuit Breaker to the LLM interface (https://python.plainenglish.io/architecture-of-ai-driven-systems-what-every-technical-architect-should-know-767f5a1fdcd0)

