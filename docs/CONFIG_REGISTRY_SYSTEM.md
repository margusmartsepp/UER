# Configuration Registry System

## Overview

The Configuration Registry allows **LLMs to manage provider configurations** on behalf of users, eliminating the need for manual environment variable editing. This helps non-technical users set up LLM providers through natural language conversation.

## Key Features

### 1. LLM-Managed Configuration
- **Read**: LLMs can query current provider configurations
- **Write**: LLMs can set/update provider configurations
- **Persist**: All changes saved to `~/.uer/provider_config.json`
- **No manual editing**: Users don't need to edit env vars or config files

### 2. User-Specific Cloud Instances
- **Azure**: Configure user's Azure OpenAI deployments
- **AWS Bedrock**: Configure user's Bedrock endpoints
- **Custom endpoints**: Any provider with user-specific instances
- **Multiple instances**: Support multiple deployments per provider

### 3. Dual Configuration Sources
- **Environment variables**: Traditional approach (still supported)
- **Config registry**: LLM-managed approach (new)
- **Priority**: Registry takes precedence over environment
- **Compatibility**: Both can coexist

### 4. Auto-Discovery
- **Local providers**: Automatically detected (Ollama, LM Studio)
- **Configured providers**: From both env vars and registry
- **No hardcoding**: Dynamic provider detection

## Architecture

### Config File Structure

**Location**: `~/.uer/provider_config.json`

```json
{
  "_metadata": {
    "version": "1.0",
    "created_at": "2026-01-11T10:19:08+00:00",
    "last_updated": "2026-01-11T10:19:08+00:00"
  },
  "providers": {
    "openai": {
      "credentials": {
        "OPENAI_API_KEY": "sk-...",
        "OPENAI_API_BASE": "https://api.openai.com/v1"
      },
      "description": "OpenAI cloud API",
      "_updated_at": "2026-01-11T10:19:08+00:00"
    },
    "azure": {
      "instances": [
        {
          "name": "my-gpt4-deployment",
          "endpoint": "https://my-resource.openai.azure.com",
          "deployment_name": "gpt-4o",
          "api_version": "2024-02-15-preview",
          "description": "My Azure OpenAI GPT-4o deployment",
          "_added_at": "2026-01-11T10:19:08+00:00"
        }
      ],
      "_updated_at": "2026-01-11T10:19:08+00:00"
    },
    "bedrock": {
      "instances": [
        {
          "name": "us-east-1-claude",
          "region": "us-east-1",
          "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
          "description": "Claude 3.5 Sonnet on AWS Bedrock",
          "_added_at": "2026-01-11T10:19:08+00:00"
        }
      ],
      "_updated_at": "2026-01-11T10:19:08+00:00"
    }
  }
}
```

## MCP Tools

### 1. `llm_config_get`

Get provider configuration from registry.

**Parameters:**
- `provider` (optional): Specific provider name. Omit to get all providers.

**Example:**
```json
{
  "provider": "azure"
}
```

**Response:**
```json
{
  "provider": "azure",
  "config": {
    "instances": [...],
    "_updated_at": "2026-01-11T10:19:08+00:00"
  }
}
```

### 2. `llm_config_set`

Set or update provider configuration.

**Parameters:**
- `provider` (required): Provider name
- `config` (required): Configuration object
- `merge` (optional): Merge with existing (default: true)

**Example:**
```json
{
  "provider": "openai",
  "config": {
    "credentials": {
      "OPENAI_API_KEY": "sk-..."
    },
    "description": "OpenAI cloud API"
  },
  "merge": true
}
```

**Response:**
```json
{
  "success": true,
  "provider": "openai",
  "config": {...},
  "message": "Configuration updated for provider 'openai'"
}
```

### 3. `llm_config_add_instance`

Add a provider instance (e.g., Azure deployment, AWS endpoint).

**Parameters:**
- `provider` (required): Provider name
- `instance` (required): Instance configuration

**Example:**
```json
{
  "provider": "azure",
  "instance": {
    "name": "my-gpt4-deployment",
    "endpoint": "https://my-resource.openai.azure.com",
    "deployment_name": "gpt-4o",
    "api_version": "2024-02-15-preview",
    "description": "My Azure OpenAI GPT-4o deployment"
  }
}
```

**Response:**
```json
{
  "success": true,
  "provider": "azure",
  "instance": {...},
  "total_instances": 1,
  "message": "Instance added to provider 'azure'"
}
```

## Use Cases

### Use Case 1: Non-Technical User Setup

**User**: "I want to use OpenAI but I don't know how to set it up"

**LLM Workflow**:
1. Ask user for API key
2. Call `llm_config_set`:
   ```json
   {
     "provider": "openai",
     "config": {
       "credentials": {
         "OPENAI_API_KEY": "sk-user-provided-key"
       }
     }
   }
   ```
3. Confirm setup complete
4. User can now use OpenAI without touching env vars

### Use Case 2: Azure Deployment

**User**: "Add my Azure OpenAI deployment"

**LLM Workflow**:
1. Ask for deployment details (endpoint, deployment name, etc.)
2. Call `llm_config_add_instance`:
   ```json
   {
     "provider": "azure",
     "instance": {
       "name": "production-gpt4",
       "endpoint": "https://my-resource.openai.azure.com",
       "deployment_name": "gpt-4o",
       "api_version": "2024-02-15-preview"
     }
   }
   ```
3. Instance added and ready to use

### Use Case 3: Check Current Setup

**User**: "What providers do I have configured?"

**LLM Workflow**:
1. Call `llm_config_get` (no parameters)
2. Show user all configured providers
3. List instances for cloud providers (Azure, AWS, etc.)

### Use Case 4: Local Server

**User**: "Set up Ollama for me"

**LLM Workflow**:
1. Call `llm_config_set`:
   ```json
   {
     "provider": "ollama",
     "config": {
       "credentials": {
         "OLLAMA_API_BASE": "http://localhost:11434"
       },
       "type": "local"
     }
   }
   ```
2. Ollama configured and auto-discovered

## Integration with Gateway

### Provider Detection

The `LLMGateway` checks both sources:

```python
def _detect_providers(self) -> list[str]:
    providers = set()

    # Check environment variables
    for env_var, provider_name in self.PROVIDER_ENV_MAP.items():
        if os.getenv(env_var):
            providers.add(provider_name)

    # Check config registry
    configured_providers = self.config_registry.list_configured_providers()
    providers.update(configured_providers)

    return sorted(providers)
```

### Credential Priority

Registry credentials override environment variables:

```python
def get_provider_credentials(self, provider_name: str) -> dict[str, str]:
    credentials = {}

    # Get from environment first
    for env_var in env_map[provider_name]:
        value = os.getenv(env_var)
        if value:
            credentials[env_var] = value

    # Override with registry config
    provider_config = self.get_provider(provider_name)
    if provider_config and "credentials" in provider_config:
        credentials.update(provider_config["credentials"])

    return credentials
```

## Benefits

### For Non-Technical Users
- ✓ No need to edit environment variables
- ✓ No need to understand config files
- ✓ Natural language setup via LLM
- ✓ Visual confirmation of setup

### For Cloud Provider Users
- ✓ Configure user-specific instances (Azure, AWS)
- ✓ Multiple deployments per provider
- ✓ Instance-specific settings
- ✓ Easy to add/remove instances

### For Developers
- ✓ Backward compatible with env vars
- ✓ Programmatic configuration
- ✓ Persistent storage
- ✓ Clean separation of concerns

## Security Considerations

### Credential Storage
- **Location**: `~/.uer/provider_config.json`
- **Permissions**: User-only read/write (default)
- **Format**: Plain JSON (consider encryption for production)

### Best Practices
1. **Sensitive data**: Consider using environment variables for production
2. **File permissions**: Ensure config file is not world-readable
3. **API keys**: Rotate regularly
4. **Instances**: Use least-privilege credentials

## Testing

Run the test script:

```bash
python scripts/test_config_registry.py
```

**Test Coverage**:
- ✓ Get all providers (initial state)
- ✓ Set provider configuration
- ✓ Add provider instances
- ✓ Get specific provider
- ✓ List configured providers
- ✓ Verify disk persistence

## Example Conversation Flow

```
User: I want to use Claude but I don't know how to set it up

LLM: I can help you set up Claude (Anthropic). You'll need an API key from
     Anthropic. Do you have one?

User: Yes, it's sk-ant-...

LLM: [Calls llm_config_set with Anthropic credentials]
     Great! I've configured Claude for you. You can now use it with:
     llm_call with model "anthropic/claude-3-5-sonnet-20241022"

User: Can I use my Azure OpenAI deployment?

LLM: Yes! I'll need some information about your Azure deployment:
     - Resource endpoint (e.g., https://my-resource.openai.azure.com)
     - Deployment name
     - API version

User: [Provides details]

LLM: [Calls llm_config_add_instance with Azure deployment]
     Perfect! Your Azure deployment is now configured. You can use it with:
     llm_call with model "azure/gpt-4o"

User: What providers do I have set up?

LLM: [Calls llm_config_get]
     You have 2 providers configured:
     1. Anthropic (Claude) - Cloud API
     2. Azure OpenAI - 1 deployment: my-gpt4-deployment
```

## Future Enhancements

1. **Encryption**: Encrypt sensitive credentials in config file
2. **Validation**: Validate credentials before saving
3. **Templates**: Pre-configured templates for common setups
4. **Import/Export**: Share configurations between machines
5. **UI**: Web-based configuration interface
