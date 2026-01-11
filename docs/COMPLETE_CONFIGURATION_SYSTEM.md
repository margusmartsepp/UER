# Complete LLM Configuration System

## Overview

The UER LLM Gateway features a comprehensive configuration system with **security-first design** that protects users from accidentally exposing API keys in chat conversations.

## System Architecture

### Three-Layer System

1. **Model Cache** (`~/.uer/model_cache.json`)
   - Actual available models from API queries
   - Timestamp tracking for freshness
   - No hardcoded fallbacks

2. **Configuration Registry** (`~/.uer/provider_config.json`)
   - LLM-managed provider setup
   - User-specific cloud instances
   - **Security warnings for API keys**

3. **Configuration Guide** (MCP Tool)
   - Detects MCP client location
   - Provides secure setup instructions
   - **Prevents key exposure in chat**

## Security-First Design

### The Problem We Solve

**Context**: This feature is strictly for ease of use and following security best practices.

**User Responsibility**: Users can often opt out of having their conversations used for training (check your LLM provider's settings). However:
- Some providers make this a premium feature (free users may not have the option)
- Users may not be aware of these settings
- Ultimately, users are responsible for managing their data sharing preferences

**Why Environment Variables Are Better**:
- More convenient than sharing keys in chat
- Never transmitted in conversations
- Follows industry security best practices
- Keeps credentials in one secure location

### Our Solution

#### 1. Automatic Security Warnings

When API keys detected in config:
```json
{
  "_security_risk": {
    "level": "high",
    "issue": "API keys stored in plaintext config file",
    "risk": "If this conversation is used for LLM training, your API keys could be exposed...",
    "recommendation": "Use environment variables instead",
    "alternative_method": "Use llm_config_guide tool"
  }
}
```

#### 2. Configuration Guide Tool

**`llm_config_guide`** - Secure setup assistant:
- Detects user's MCP client (Claude Desktop, Cline, Windsurf)
- Locates config file automatically
- Provides step-by-step instructions
- **Never asks for keys in chat**

#### 3. LLM Workflow Protection

**Tool Description** explicitly warns LLMs:
```
⚠️ SECURITY WARNING: Never ask users to share API keys in chat!
This tool detects the user's MCP client and provides instructions for
securely setting environment variables in the client config file.
Use this instead of llm_config_set when API keys are involved.
```

## MCP Tools

### Model Discovery

1. **`llm_list_models`** - List available models
   - Live API queries with timestamps
   - Ground truth for LLMs
   - Cache age assessment

2. **`check_model_exists`** - Verify model availability
   - Checks against live/cached data
   - Provides suggestions

### Configuration Management

3. **`llm_config_get`** - Read provider configuration
   - View current setup
   - Check configured providers

4. **`llm_config_set`** - Set provider configuration
   - **Triggers security warnings for API keys**
   - Use for non-sensitive config only
   - Instances, endpoints, settings

5. **`llm_config_add_instance`** - Add cloud instances
   - Azure deployments
   - AWS Bedrock endpoints
   - Custom servers

6. **`llm_config_guide`** ⭐ **NEW - Secure Setup**
   - **Primary tool for API key setup**
   - Detects MCP client
   - Provides secure instructions
   - Prevents key exposure

## Secure Workflow Examples

### Example 1: OpenAI Setup (Secure)

```
User: "I want to use OpenAI"

LLM: [Calls llm_config_guide with provider="openai"]

LLM: "I can help you set up OpenAI securely. I've detected you're using
      Claude Desktop. Here's how to add your API key:

      1. Open: C:\Users\...\Claude\claude_desktop_config.json
      2. Find the 'uer' server entry
      3. Add to the 'env' section:

         \"uer\": {
           \"env\": {
             \"OPENAI_API_KEY\": \"your-key-here\"
           }
         }

      ⚠️ IMPORTANT: Add the key directly to the file - don't share it
      here. This keeps your credentials secure."

User: [Adds key to config file]
User: "Done"

LLM: "Perfect! OpenAI is now configured securely."
```

### Example 2: Azure Deployment (Secure)

```
User: "Add my Azure OpenAI deployment"

LLM: "I'll help you configure your Azure deployment. First, let me guide
      you on adding your Azure API key securely..."

      [Calls llm_config_guide with provider="azure"]

      [Shows instructions for adding AZURE_API_KEY to MCP config]

User: [Adds key to config file]
User: "Done, now add the deployment"

LLM: [Calls llm_config_add_instance with deployment details]
     "Your Azure deployment is configured!"
```

### Example 3: Check Setup

```
User: "What providers do I have?"

LLM: [Calls llm_config_get]
     "You have 3 providers configured:
      1. OpenAI - Cloud API (via env vars ✓ secure)
      2. Anthropic - Cloud API (via env vars ✓ secure)
      3. Azure - 2 deployments:
         - production-gpt4 (gpt-4o)
         - dev-gpt35 (gpt-3.5-turbo)"
```

## Supported MCP Clients

| Client | Platform | Config Location |
|--------|----------|----------------|
| Claude Desktop | macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop | Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cline | macOS | `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` |
| Cline | Windows | `%APPDATA%\Code\User\globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` |
| Cline | Linux | `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` |
| Windsurf | macOS | `~/Library/Application Support/Windsurf/User/globalStorage/windsurf.windsurf/settings/windsurf_mcp_settings.json` |
| Windsurf | Windows | `%APPDATA%\Windsurf\User\globalStorage/windsurf.windsurf/settings/windsurf_mcp_settings.json` |
| Windsurf | Linux | `~/.config/Windsurf/User/globalStorage/windsurf.windsurf/settings/windsurf_mcp_settings.json` |

## Configuration Examples

### Secure Setup (Environment Variables)

```json
{
  "mcpServers": {
    "uer": {
      "command": "uv",
      "args": ["--directory", "C:\\Users\\margu\\UER", "run", "uer"],
      "env": {
        "OPENAI_API_KEY": "sk-proj-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GEMINI_API_KEY": "AIza...",
        "AZURE_API_KEY": "...",
        "AZURE_API_BASE": "https://my-resource.openai.azure.com"
      }
    }
  }
}
```

### Registry Config (Non-Sensitive Only)

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
          "name": "production-gpt4",
          "endpoint": "https://my-resource.openai.azure.com",
          "deployment_name": "gpt-4o",
          "api_version": "2024-02-15-preview"
        }
      ]
    }
  }
}
```

## Provider Environment Variables

| Provider | Required | Optional |
|----------|----------|----------|
| OpenAI | `OPENAI_API_KEY` | `OPENAI_API_BASE` |
| Anthropic | `ANTHROPIC_API_KEY` | - |
| Gemini | `GEMINI_API_KEY` | `GOOGLE_API_KEY` |
| Azure | `AZURE_API_KEY`, `AZURE_API_BASE` | `AZURE_API_VERSION` |
| Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | `AWS_REGION_NAME` |
| Cerebras | `CEREBRAS_API_KEY` | - |
| Groq | `GROQ_API_KEY` | - |
| Ollama | `OLLAMA_API_BASE` | - |

## Security Features

### ✓ Automatic Protection
- Detects API keys in config
- Triggers high-level warnings
- Suggests secure alternatives

### ✓ Client Detection
- Finds MCP client automatically
- Platform-aware (Windows, macOS, Linux)
- Supports Claude Desktop, Cline, Windsurf

### ✓ Clear Guidance
- Step-by-step instructions
- Exact file paths
- Example configurations
- Security explanations

### ✓ LLM Education
- Tool descriptions warn about security
- Recommends secure methods
- Explains training data risks

## Testing

### Test Scripts

```bash
# Test security warnings
python scripts/test_security_warnings.py

# Test configuration registry
python scripts/test_config_registry.py

# Test model cache
python scripts/test_disk_cache.py
```

### Test Coverage

**Security Warnings**:
- ✓ Detects API keys in config
- ✓ Triggers security warnings
- ✓ Detects MCP client location
- ✓ Generates secure instructions
- ✓ No warning for non-sensitive config

**Configuration Registry**:
- ✓ Read/write provider configs
- ✓ Add provider instances
- ✓ Disk persistence
- ✓ Dual source support (env + registry)

**Model Cache**:
- ✓ Loads from disk on init
- ✓ Timestamp updates
- ✓ No hardcoded fallbacks
- ✓ Returns all available models

## Best Practices

### For LLMs

1. **Always use `llm_config_guide`** when API keys needed
2. **Never ask users** to share keys in chat
3. **Explain security risks** clearly
4. **Provide step-by-step** instructions
5. **Verify user** added keys to config file

### For Users

1. **Never share API keys** in chat
2. **Add keys to MCP config** file directly
3. **Use environment variables** not registry
4. **Restart MCP client** after changes
5. **Rotate keys regularly** for security

### For Developers

1. **Environment variables** for sensitive data
2. **Registry config** for non-sensitive settings
3. **Security warnings** for all credential operations
4. **Client detection** for better UX
5. **Clear documentation** for users

## Benefits

### Security
- ✓ Prevents key exposure in chat
- ✓ Protects training data
- ✓ Educates users about risks
- ✓ Provides secure alternatives

### Usability
- ✓ Automatic client detection
- ✓ Clear instructions
- ✓ No manual path finding
- ✓ Works for non-technical users

### Flexibility
- ✓ Supports multiple MCP clients
- ✓ Platform-aware
- ✓ Provider-agnostic
- ✓ Extensible design

## Documentation

- `docs/SECURITY_WARNINGS.md` - Security system details
- `docs/CONFIG_REGISTRY_SYSTEM.md` - Registry documentation
- `docs/DISK_CACHE_SYSTEM.md` - Model cache details
- `docs/LLM_CONFIGURATION_SUMMARY.md` - System overview

## Summary

The UER configuration system provides:

1. **Security-first design** - Protects against key exposure
2. **Automatic detection** - Finds MCP client and config location
3. **Clear guidance** - Step-by-step secure setup instructions
4. **LLM protection** - Tools designed to prevent insecure workflows
5. **User-friendly** - Works for non-technical users
6. **Flexible** - Supports multiple clients and providers
7. **Ground truth** - Actual model data with timestamps
8. **Persistent** - Disk-based cache and registry

This enables LLMs to help users securely configure providers without exposing credentials in chat conversations that may be used for training data.
