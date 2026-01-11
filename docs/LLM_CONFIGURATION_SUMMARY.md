# LLM Configuration System - Complete Implementation

## Overview

The UER LLM Gateway now features a comprehensive configuration system that combines:
1. **Disk-based model cache** with timestamps
2. **Configuration registry** for LLM-managed provider setup
3. **Support for user-specific cloud instances** (Azure, AWS, etc.)
4. **Auto-discovery** of local and configured providers

## System Components

### 1. Model Cache System (`~/.uer/model_cache.json`)

**Purpose**: Cache actual available models from provider APIs with timestamps.

**Features**:
- No hardcoded fallbacks - all data from API queries
- Timestamp updated on every query (even if models unchanged)
- LLMs can judge cache age and decide if refresh needed
- Persisted to disk, loaded on gateway init

**Structure**:
```json
{
  "openai": {
    "models": ["openai/o4-mini-2025-04-16", ...57 total],
    "last_updated": "2026-01-11T10:03:30+00:00",
    "total_count": 57
  }
}
```

### 2. Configuration Registry (`~/.uer/provider_config.json`)

**Purpose**: Allow LLMs to manage provider configurations for non-technical users.

**Features**:
- LLMs can read/write provider configurations
- Support for user-specific cloud instances
- Credentials, endpoints, and provider-specific settings
- Persisted to disk with metadata

**Structure**:
```json
{
  "_metadata": {
    "version": "1.0",
    "created_at": "2026-01-11T10:19:08+00:00",
    "last_updated": "2026-01-11T10:19:08+00:00"
  },
  "providers": {
    "azure": {
      "instances": [
        {
          "name": "my-gpt4-deployment",
          "endpoint": "https://my-resource.openai.azure.com",
          "deployment_name": "gpt-4o",
          "api_version": "2024-02-15-preview"
        }
      ]
    }
  }
}
```

## MCP Tools

### Model Discovery Tools

1. **`llm_list_models`** - List available providers and models
   - Queries live APIs for current models
   - Returns cached data with timestamps
   - Includes ground truth message for LLMs

2. **`check_model_exists`** - Verify if a model exists
   - Checks against cached/live data
   - Returns suggestions if model not found
   - Helps LLMs ground their responses

### Configuration Management Tools

3. **`llm_config_get`** - Get provider configuration
   - Read current provider setup
   - Show all providers or specific provider
   - Helps users understand their setup

4. **`llm_config_set`** - Set/update provider configuration
   - LLMs can configure providers for users
   - Set API keys, endpoints, settings
   - No manual env var editing needed

5. **`llm_config_add_instance`** - Add provider instance
   - Configure user-specific cloud deployments
   - Azure OpenAI deployments
   - AWS Bedrock endpoints
   - Custom OpenAI-compatible servers

## Key Features

### For Non-Technical Users

**Problem**: Users don't know how to set environment variables or edit config files.

**Solution**: LLMs can configure providers through natural language:

```
User: "I want to use OpenAI but don't know how to set it up"
LLM: [Asks for API key, calls llm_config_set]
Result: OpenAI configured without touching env vars
```

### For Cloud Provider Users

**Problem**: Users have their own Azure/AWS deployments but can't configure them.

**Solution**: LLMs can add user-specific instances:

```
User: "Add my Azure OpenAI deployment"
LLM: [Asks for details, calls llm_config_add_instance]
Result: Azure deployment configured with user's specific endpoint
```

### For Model Discovery

**Problem**: LLMs don't know what models are actually available (knowledge cutoff).

**Solution**: Ground truth data with timestamps:

```json
{
  "current_time": "2026-01-11T10:03:30+00:00",
  "message": "This serves as ground truth. Your knowledge cutoff may be older.",
  "providers": {
    "openai": {
      "models": [...actual models...],
      "last_updated": "2026-01-11T10:03:30+00:00"
    }
  }
}
```

## Workflow Examples

### Example 1: First-Time Setup

```
User: "Help me set up Claude"

LLM: "I can help you configure Claude (Anthropic). You'll need an API key
      from Anthropic. Do you have one?"

User: "Yes, sk-ant-..."

LLM: [Calls llm_config_set]
     {
       "provider": "anthropic",
       "config": {
         "credentials": {
           "ANTHROPIC_API_KEY": "sk-ant-..."
         }
       }
     }

LLM: "Great! Claude is now configured. You can use it with:
      llm_call with model 'anthropic/claude-3-5-sonnet-20241022'"
```

### Example 2: Azure Deployment

```
User: "I have an Azure OpenAI deployment I want to use"

LLM: "I'll help you configure your Azure deployment. I need:
      - Resource endpoint
      - Deployment name
      - API version"

User: [Provides details]

LLM: [Calls llm_config_add_instance]
     {
       "provider": "azure",
       "instance": {
         "name": "production-gpt4",
         "endpoint": "https://my-resource.openai.azure.com",
         "deployment_name": "gpt-4o",
         "api_version": "2024-02-15-preview"
       }
     }

LLM: "Your Azure deployment is configured! Use it with:
      llm_call with model 'azure/gpt-4o'"
```

### Example 3: Check Setup

```
User: "What providers do I have configured?"

LLM: [Calls llm_config_get]

LLM: "You have 3 providers configured:
      1. OpenAI - Cloud API
      2. Anthropic (Claude) - Cloud API
      3. Azure OpenAI - 2 deployments:
         - production-gpt4 (gpt-4o)
         - dev-gpt35 (gpt-3.5-turbo)"
```

### Example 4: Model Discovery

```
User: "What OpenAI models are available?"

LLM: [Calls llm_list_models]

LLM: "Based on live API query (updated 2 minutes ago), OpenAI has 57 chat
      models available. The latest ones include:
      - o4-mini-2025-04-16 (newest reasoning model)
      - o3-mini (reasoning)
      - gpt-5.2-pro (latest GPT-5 series)
      - gpt-4o (GPT-4 optimized)

      Note: My knowledge cutoff is older than this data, so I'm using the
      live API results as ground truth."
```

## Architecture Benefits

### 1. No Hardcoding
- **Before**: Hardcoded example models in code
- **After**: All data from disk cache populated by API queries

### 2. Timestamp Tracking
- **Purpose**: LLMs can judge data freshness
- **Behavior**: Updated on every query, even if models unchanged
- **Use**: "Cache is 3 days old, should I refresh?"

### 3. Dual Configuration
- **Environment variables**: Traditional approach (still works)
- **Config registry**: LLM-managed approach (new)
- **Priority**: Registry overrides environment

### 4. User-Specific Instances
- **Azure**: User's own deployments
- **AWS**: User's own endpoints
- **Custom**: Any user-specific server

### 5. Auto-Discovery
- **Local servers**: Ollama, LM Studio (auto-detected)
- **Configured providers**: From env vars + registry
- **Dynamic**: No hardcoded provider lists

## File Locations

- **Model cache**: `~/.uer/model_cache.json`
- **Provider config**: `~/.uer/provider_config.json`

Both created automatically on first use.

## Scripts

- `scripts/seed_model_cache.py` - Populate model cache from APIs
- `scripts/test_disk_cache.py` - Test model cache system
- `scripts/test_config_registry.py` - Test configuration registry
- `scripts/compare_models.py` - Compare live vs cached models

## Documentation

- `docs/DISK_CACHE_SYSTEM.md` - Model cache details
- `docs/CONFIG_REGISTRY_SYSTEM.md` - Configuration registry details
- `docs/MODEL_GROUNDING.md` - Model discovery and grounding

## Testing

All systems tested and working:

**Model Cache**:
- ✓ Loads from disk on init
- ✓ Timestamp updated on every query
- ✓ Persists to disk automatically
- ✓ No hardcoded fallbacks
- ✓ Returns all available models (57 for OpenAI)

**Config Registry**:
- ✓ LLMs can read configurations
- ✓ LLMs can set/update configurations
- ✓ LLMs can add provider instances
- ✓ Persists to disk with metadata
- ✓ Supports both env vars and registry

**Integration**:
- ✓ Gateway detects providers from both sources
- ✓ Registry credentials override environment
- ✓ Auto-discovery of local providers
- ✓ MCP tools working correctly

## Summary

The system now provides:

1. **Ground truth model data** - No speculation, all from APIs
2. **Timestamp tracking** - LLMs can judge freshness
3. **LLM-managed configuration** - Help non-technical users
4. **User-specific instances** - Azure, AWS, custom deployments
5. **No hardcoding** - Dynamic, flexible, extensible

This enables LLMs to:
- Help users set up providers without technical knowledge
- Use actual current model data (not training data)
- Configure user-specific cloud deployments
- Assess data freshness and decide when to refresh
- Provide accurate, grounded responses about available models
