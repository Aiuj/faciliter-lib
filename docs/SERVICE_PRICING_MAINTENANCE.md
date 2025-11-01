# Service Pricing Quick Reference

This document provides quick instructions for maintaining the AI service pricing data.

## Pricing File Location

All pricing data is centralized in:
```
faciliter_lib/tracing/service_pricing.py
```

## How to Update Pricing

### Adding/Updating LLM Model Pricing

Edit `LLM_PRICING` dictionary:

```python
LLM_PRICING = {
    # Add new model
    "new-model-name": {"input": 0.001, "output": 0.002},
    
    # Update existing model
    "gpt-4o": {"input": 0.0025, "output": 0.01},  # Updated pricing
}
```

**Format**: Model names should be lowercase. Prices are per 1,000 tokens in USD.

### Adding/Updating Embedding Model Pricing

Edit `EMBEDDING_PRICING` dictionary:

```python
EMBEDDING_PRICING = {
    # Add new model
    "new-embedding-model": 0.00005,
    
    # Update existing model  
    "text-embedding-3-small": 0.00003,  # Updated pricing
}
```

**Format**: Prices are per 1,000 tokens in USD.

### Adding/Updating OCR Service Pricing

Edit `OCR_PRICING` dictionary:

```python
OCR_PRICING = {
    # Add new service (per page)
    "provider-name/service-name": {"per_page": 0.001},
    
    # Add service with per-image pricing
    "provider-name/other-service": {"per_image": 0.005},
    
    # Service with both
    "provider-name/advanced": {
        "per_page": 0.01,
        "per_image": 0.005
    },
}
```

**Format**: Key is `"provider/model"` (lowercase). Prices are per unit (page or image).

## Pricing Sources

### OpenAI
- Official pricing: https://openai.com/api/pricing/
- Update frequency: Check monthly or when new models released

### Google Gemini
- Official pricing: https://ai.google.dev/pricing
- Update frequency: Check quarterly

### Anthropic Claude
- Official pricing: https://www.anthropic.com/pricing
- Update frequency: Check quarterly

### Azure OpenAI
- Pricing typically matches OpenAI
- Official docs: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/

### Azure Document Intelligence (OCR)
- Official pricing: https://azure.microsoft.com/en-us/pricing/details/form-recognizer/

### Google Cloud Vision
- Official pricing: https://cloud.google.com/vision/pricing

## Model Name Matching

The pricing system uses **fuzzy matching** for model names:

1. **Exact match** (case-insensitive): `"gpt-4"` matches `"gpt-4"`
2. **Partial match**: `"gpt-4-turbo-2024-04-09"` matches `"gpt-4-turbo"`
3. **Prefix match**: `"gpt-4o-2024-08-06"` matches `"gpt-4o"`

This means you can add base model pricing and it will match versioned models:

```python
# Adding this:
"gpt-4o": {"input": 0.005, "output": 0.015}

# Will also match:
# - gpt-4o-2024-05-13
# - gpt-4o-2024-08-06
# - gpt-4o-mini (careful - add specific entry if different!)
```

## Testing After Updates

After updating pricing, run tests to ensure calculations work:

```bash
pytest tests/test_service_usage.py -v
```

Add test cases for new models:

```python
def test_new_model_cost():
    """Test cost calculation for new-model."""
    cost = calculate_llm_cost("provider", "new-model", 1000, 500)
    expected = (1000/1000 * 0.001) + (500/1000 * 0.002)
    assert cost == pytest.approx(expected)
```

## Common Updates Checklist

When a provider updates pricing:

- [ ] Update pricing in `service_pricing.py`
- [ ] Update pricing tables in `docs/SERVICE_USAGE_TRACKING.md`
- [ ] Add test case if new model
- [ ] Run `pytest tests/test_service_usage.py`
- [ ] Update "Last updated" comment in `service_pricing.py`
- [ ] Commit with message like "Update OpenAI pricing (October 2025)"

## Example: Adding a New Provider

To add pricing for a completely new provider:

```python
# 1. Add to LLM_PRICING
LLM_PRICING = {
    # ... existing entries ...
    
    # New provider
    "cohere-command": {"input": 0.001, "output": 0.002},
    "cohere-command-light": {"input": 0.0003, "output": 0.0006},
}

# 2. Add to EMBEDDING_PRICING if they have embeddings
EMBEDDING_PRICING = {
    # ... existing entries ...
    
    "cohere-embed-english-v3": 0.0001,
    "cohere-embed-multilingual-v3": 0.0001,
}

# 3. Update documentation
# - docs/SERVICE_USAGE_TRACKING.md (pricing tables)
# - Add provider to supported list in README.md

# 4. Test
# - Add test cases for new provider
# - Run pytest
```

## Free/Local Models

For free or self-hosted models, set pricing to 0:

```python
LLM_PRICING = {
    "ollama": {"input": 0.0, "output": 0.0},
    "local-model": {"input": 0.0, "output": 0.0},
}

EMBEDDING_PRICING = {
    "infinity": 0.0,
    "sentence-transformers": 0.0,
}
```

## Versioned Pricing

If a model has version-specific pricing:

```python
# Specific versions
"gpt-4o-2024-05-13": {"input": 0.005, "output": 0.015},
"gpt-4o-2024-08-06": {"input": 0.0025, "output": 0.01},  # Cheaper!

# Generic fallback (will match if no specific version)
"gpt-4o": {"input": 0.005, "output": 0.015},
```

The system will prefer exact matches, then fall back to partial matches.

## Questions?

If you're unsure about:
- **Pricing accuracy**: Check provider's official pricing page
- **Model naming**: Use lowercase, match provider's canonical name
- **Token calculation**: Most providers charge by tokens, not by characters
- **Regional pricing**: Use US pricing as default unless specified otherwise

## Maintenance Schedule

Recommended review frequency:
- **OpenAI**: Monthly (frequent updates)
- **Gemini**: Quarterly
- **Claude**: Quarterly  
- **Azure**: Quarterly
- **OCR services**: Semi-annually

Set a calendar reminder to review pricing regularly!
