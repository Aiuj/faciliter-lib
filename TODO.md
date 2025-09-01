# Faciliter lib roadmap

## Changes done

### 0.2.3

- Added an hardcoded list of categories for business documents in config
- Added ExcelManager in tools to convert Excel into Markdown or Json IR structure

## LLM client roadmap

- Use low level official libraries instead of langchain
- Add Tracing observability
- Add OpenAI model API
- Implement LangChain and LlamaIndex abstraction wrappers
- Add a circuit Breaker to the LLM interface (https://python.plainenglish.io/architecture-of-ai-driven-systems-what-every-technical-architect-should-know-767f5a1fdcd0)
- Manage rate limits with retries
