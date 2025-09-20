# Faciliter lib roadmap

## Changes done

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
- Manage rate limits with retries
