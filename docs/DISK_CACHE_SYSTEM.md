# Disk-Based Model Cache System

## Overview

The LLM Gateway now uses a **disk-based cache system** where model data is serialized to JSON at `~/.uer/model_cache.json`. No hardcoded fallbacks - all model data comes from actual API queries and is persisted to disk.

## Key Features

### 1. Disk Persistence
- **Cache Location**: `~/.uer/model_cache.json`
- **Format**: JSON with metadata
- **Auto-load**: Cache loaded from disk on gateway initialization
- **Auto-save**: Cache saved to disk after every API query

### 2. Timestamp Updates
- **Always updated**: Timestamp refreshed on every query, even if models unchanged
- **Purpose**: LLMs can judge cache age and decide if refresh needed
- **Format**: ISO 8601 UTC timestamp

### 3. No Hardcoded Fallbacks
- **Before**: Hardcoded example models in code
- **After**: All data from disk cache or API queries
- **Empty cache**: Returns `[]` (prompts user to seed cache)

## Cache Structure

```json
{
  "openai": {
    "models": [
      "openai/o4-mini-2025-04-16",
      "openai/o4-mini",
      ...57 total
    ],
    "last_updated": "2026-01-11T10:03:30.345992+00:00",
    "total_count": 57
  },
  "gemini": {
    "models": [...],
    "last_updated": "2026-01-11T10:05:00.000000+00:00",
    "total_count": 15
  }
}
```

### Required Fields
- `models`: List of model identifiers
- `last_updated`: ISO 8601 timestamp of last query
- `total_count`: Number of models

## Usage

### Seeding the Cache

```bash
python scripts/seed_model_cache.py
```

This will:
1. Query all configured provider APIs
2. Populate `~/.uer/model_cache.json`
3. Save with timestamps

### Updating the Cache

Cache is automatically updated when:
- `get_provider_info()` is called
- `llm_list_models` MCP tool is used
- `check_model_exists()` is called

**Important**: Timestamp is updated on every query, even if models haven't changed.

### Reading from Cache

```python
gateway = LLMGateway()  # Loads cache from disk

# Get all cached data with metadata
cache_data = gateway.get_cached_models()
# Returns:
# {
#   "current_time": "2026-01-11T10:03:30+00:00",
#   "message": "This serves as ground truth...",
#   "providers": {...cache...}
# }

# Get models for specific provider
models = gateway._get_example_models("openai")
# Returns from cache or [] if not cached
```

## For LLMs Using This System

### Cache Age Assessment

```python
cache_data = gateway.get_cached_models()
provider_data = cache_data['providers']['openai']

last_updated = provider_data['last_updated']  # "2026-01-11T10:03:30+00:00"
current_time = cache_data['current_time']     # "2026-01-11T12:00:00+00:00"

# Calculate age and decide if refresh needed
# Example: If cache is > 24 hours old, refresh
```

### Decision Flow

1. **Check cache exists**: Does provider have cached data?
2. **Check cache age**: Is `last_updated` recent enough?
3. **Decide action**:
   - Fresh cache (< 24h): Use cached data
   - Stale cache (> 24h): Call `llm_list_models` to refresh
   - No cache: Call `llm_list_models` to populate

### Ground Truth Message

The cache includes this message for LLMs:

> "This serves as ground truth for what models are available. Due to your knowledge cutoff date, you may not know about these models. This data is fetched from cache. To update the cache, use llm_list_models or check_model_exists which will query the provider APIs."

## Implementation Details

### Cache Loading (on init)
```python
def _load_cache_from_disk(self) -> None:
    if self._cache_file.exists():
        with open(self._cache_file, "r") as f:
            self._model_cache = json.load(f)
```

### Cache Saving (after query)
```python
def _save_cache_to_disk(self) -> None:
    self._cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(self._cache_file, "w") as f:
        json.dump(self._model_cache, f, indent=2)
```

### Timestamp Update (always)
```python
# Always update timestamp, even if models unchanged
self._model_cache["openai"] = {
    "models": models,
    "last_updated": datetime.now(timezone.utc).isoformat(),
    "total_count": len(models),
}
self._save_cache_to_disk()
```

## Test Results

All tests passing ✓:

1. **Cache loaded from disk on init** ✓
2. **Timestamp updated on every query** ✓
3. **Cache persisted to disk automatically** ✓
4. **_get_example_models returns from disk cache** ✓
5. **No hardcoded fallbacks** ✓
6. **Cache structure correct** ✓

## Benefits

1. **No Hardcoding**: All model data from actual APIs
2. **Persistent**: Survives restarts
3. **Timestamp Tracking**: LLMs can judge freshness
4. **Ground Truth**: Clear message about data authority
5. **Automatic Updates**: Timestamp refreshed on every query
6. **Graceful Degradation**: Returns `[]` if cache empty

## Scripts

- `scripts/seed_model_cache.py` - Initial cache population
- `scripts/test_disk_cache.py` - Comprehensive cache system tests
- `scripts/compare_models.py` - Compare live vs cached models

## Migration from Hardcoded Examples

**Before**: Hardcoded examples in `_get_example_models()`
```python
examples = {
    "openai": ["openai/gpt-4o", ...],  # Hardcoded
}
```

**After**: Disk-based cache
```python
# Load from ~/.uer/model_cache.json
if provider in self._model_cache:
    return self._model_cache[provider]["models"]
return []  # No hardcoded fallbacks
```

## Cache Location

- **Linux/Mac**: `~/.uer/model_cache.json`
- **Windows**: `C:\Users\<username>\.uer\model_cache.json`

The cache directory is automatically created if it doesn't exist.
