# Model Grounding System

## Overview

The UER LLM Gateway now uses **grounded model examples** based on actual API queries, with clear timestamps and guidance for LLMs about data freshness.

## Key Features

### 1. Grounded Examples (`_get_example_models`)

**Generated:** 2026-01-11T09:37:32+00:00
**Source:** Actual API responses, not speculation

Examples are now grounded in real API queries with:
- **Timestamp**: When the data was generated
- **Source tracking**: Live query vs cached fallback
- **Total count**: How many models are actually available
- **LLM guidance**: Clear instructions about knowledge cutoff and data freshness

```python
# Example: OpenAI models (10 of 57 total)
"openai": [
    "openai/o4-mini-2025-04-16",
    "openai/o4-mini",
    "openai/o3-mini-2025-01-31",
    "openai/o3-mini",
    "openai/o3-2025-04-16",
    "openai/o3",
    "openai/o1-pro-2025-03-19",
    "openai/o1-pro",
    "openai/o1-2024-12-17",
    "openai/o1",
]
```

### 2. Live Model Querying

**OpenAI Cloud:**
- Queries `https://api.openai.com/v1/models`
- Returns all chat models (57 total as of 2026-01-11)
- Filters out specialized models (audio, embedding, transcribe, etc.)
- No artificial limits or priority scoring

**Gemini:**
- Queries `https://generativelanguage.googleapis.com/v1beta/models`
- Returns models with `generateContent` capability
- Actual model names (not speculative)

**Local Servers (LM Studio, Ollama):**
- Queries `/v1/models` endpoint
- Returns actual deployed models
- Real-time data

### 3. Model Existence Checker

`check_model_exists(model: str)` provides grounding verification:

```python
result = await gateway.check_model_exists("openai/gpt-4o")
# Returns:
{
    "exists": True,
    "model": "openai/gpt-4o",
    "provider": "openai",
    "provider_type": "cloud",
    "source": "live_query",
    "available_models_count": 57,
    "suggestion": None  # or alternative if model doesn't exist
}
```

### 4. LLM List Models Tool

The `llm_list_models` MCP tool now includes:

```json
{
    "current_time": "2026-01-11T09:37:32+00:00",
    "queried_at": "2026-01-11T09:37:32+00:00",
    "important_note_for_llms": "Your knowledge cutoff may be older than this data...",
    "providers": {
        "openai": {
            "type": "cloud",
            "source": "live_query",
            "available_models": [...57 models...],
            "configured": true
        }
    }
}
```

## For LLMs Using This System

### Important Guidelines

1. **Knowledge Cutoff Awareness**
   - Your training data cutoff may be older than the generated timestamp
   - Compare `current_time` with `generated_at` to assess data freshness
   - Trust the provided data over your training knowledge

2. **Data Source Priority**
   - `source: "live_query"` = Real-time API data (most reliable)
   - `source: "examples"` = Cached fallback (may be deprecated)

3. **Verification Workflow**
   ```
   1. Query llm_list_models to see available models
   2. Use check_model_exists to verify specific model
   3. If model doesn't exist, query live data rather than assuming
   ```

4. **Cached vs Live Data**
   - Examples in `_get_example_models` are cached (generated 2026-01-11)
   - Always prefer `llm_list_models` for current data
   - This cached view may become deprecated over time

## Regenerating Grounded Examples

To update examples with fresh API data:

```bash
python scripts/generate_grounded_examples.py
```

This will:
1. Query all configured provider APIs
2. Generate grounded examples with timestamps
3. Output Python code for `_get_example_models()`
4. Save JSON to `scripts/grounded_examples.json`

## Statistics (as of 2026-01-11)

**OpenAI:**
- Total models from API: 57
- Example models: 10
- Match rate: 100% (10/10)
- Source: live_query

**Match Rate:**
- Before grounding: 50% (2/4 with speculative models)
- After grounding: 100% (10/10 with actual API data)

## Benefits

1. **No Speculation**: All examples come from actual API responses
2. **Timestamp Tracking**: Clear data freshness indicators
3. **LLM Guidance**: Explicit instructions about knowledge cutoff
4. **Verification Tools**: `check_model_exists` for grounding
5. **100% Accuracy**: Examples match live API data
