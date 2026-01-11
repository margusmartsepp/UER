# Security Warning System for API Key Protection

## Overview

The UER system now includes comprehensive security warnings to protect users from accidentally exposing API keys in chat conversations that may be used for LLM training data.

## The Problem

**Context**: Many LLM providers allow users to opt out of having their conversations used for training. However:
- Some providers make this a premium feature (free users may not have the option)
- Users may not be aware of these settings or forget to configure them
- Ultimately, **the responsibility is with the user** to manage their data sharing preferences

**This feature is strictly for ease of use** - it helps users avoid accidentally sharing credentials in chat by providing a more convenient configuration method through environment variables.

**Example Scenario**:
```
User: "Set up OpenAI for me"
LLM: "Please provide your OpenAI API key"
User: "sk-proj-abc123..." ⚠️ KEY SHARED IN CHAT
```

**Why this matters**:
- Chat logs can be leaked or accessed by monitoring systems
- Environment variables in MCP config are never transmitted in conversations
- This approach is more convenient and follows security best practices
- Reduces attack surface for credential exposure

## The Solution

### 1. Security Warnings in Config Registry

When LLMs attempt to store API keys in config files, the system automatically detects and warns:

```json
{
  "_security_risk": {
    "level": "high",
    "issue": "API keys stored in plaintext config file",
    "risk": "Storing credentials in chat conversations is less secure than using environment variables. While you can often opt out of training data usage (check your LLM provider's settings), this approach is simply more convenient and follows security best practices.",
    "recommendation": "Use environment variables in MCP client config instead",
    "alternative_method": "Use llm_config_guide tool to get instructions for secure setup",
    "user_responsibility": "You are responsible for managing your data sharing preferences with your LLM provider"
  }
}
```

### 2. Configuration Guide Tool (`llm_config_guide`)

**Purpose**: Detect user's MCP client and provide secure configuration instructions.

**Features**:
- Automatically detects MCP client (Claude Desktop, Cline, Windsurf)
- Locates client config file
- Provides step-by-step instructions for adding env vars
- Never asks user to share keys in chat

**Example Usage**:
```json
{
  "provider": "openai"
}
```

**Response**:
```json
{
  "provider": "openai",
  "client_detection": {
    "system": "Windows",
    "detected_clients": [
      {
        "name": "Claude Desktop",
        "config_file": "C:\\Users\\...\\Claude\\claude_desktop_config.json",
        "detected": true
      }
    ]
  },
  "configuration_guide": {
    "required_env_vars": ["OPENAI_API_KEY"],
    "security_note": "⚠️ SECURITY: Never share API keys in chat conversations...",
    "instructions": "To securely configure openai in Claude Desktop:\n\n1. Open your MCP client configuration file:\n   C:\\Users\\...\\claude_desktop_config.json\n\n2. Find the UER MCP server entry...\n\n3. Add or update the 'env' section:\n   \"uer\": {\n     \"env\": {\n       \"OPENAI_API_KEY\": \"your-key-here\"\n     }\n   }"
  },
  "why_this_matters": {
    "risk": "LLM providers may use chat conversations for training...",
    "solution": "Environment variables in MCP client config files are never sent in chat...",
    "best_practice": "Always configure API keys via environment variables..."
  }
}
```

## Supported MCP Clients

### Claude Desktop
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Cline (VS Code Extension)
- **macOS**: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Windows**: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
- **Linux**: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

### Windsurf
- **macOS**: `~/Library/Application Support/Windsurf/User/globalStorage/windsurf.windsurf/settings/windsurf_mcp_settings.json`
- **Windows**: `%APPDATA%\Windsurf\User\globalStorage\windsurf.windsurf\settings\windsurf_mcp_settings.json`
- **Linux**: `~/.config/Windsurf/User/globalStorage/windsurf.windsurf/settings/windsurf_mcp_settings.json`

## LLM Workflow Examples

### Secure Setup (Recommended)

```
User: "I want to use OpenAI"

LLM: [Calls llm_config_guide with provider="openai"]

LLM: "I can help you set up OpenAI securely. I've detected you're using
      Claude Desktop. Here's how to add your API key safely:

      1. Open: C:\Users\...\Claude\claude_desktop_config.json
      2. Find the 'uer' server entry
      3. Add your API key to the 'env' section:

         \"uer\": {
           \"env\": {
             \"OPENAI_API_KEY\": \"your-key-here\"
           }
         }

      4. Save and restart Claude Desktop

      ⚠️ IMPORTANT: Add the key directly to the file - don't share it in
      this chat. This keeps your credentials secure and prevents exposure
      in training data."

User: [Adds key to config file]

User: "Done"

LLM: "Great! OpenAI is now configured securely."
```

### Insecure Setup (Prevented)

```
User: "Set up OpenAI for me"

LLM: [Attempts to call llm_config_set with API key]

System: [Returns security warning]

LLM: "⚠️ SECURITY WARNING: I was about to ask for your API key, but that
      would expose it in our conversation. Let me show you a secure way
      to configure OpenAI instead..."

      [Calls llm_config_guide and provides instructions]
```

## Security Features

### 1. Automatic Detection
- ✓ Detects API keys in config (patterns: API_KEY, SECRET, PASSWORD, TOKEN)
- ✓ Triggers high-level security warning
- ✓ Provides alternative secure method

### 2. Client Detection
- ✓ Automatically finds MCP client config file
- ✓ Supports Claude Desktop, Cline, Windsurf
- ✓ Platform-aware (Windows, macOS, Linux)

### 3. Clear Instructions
- ✓ Step-by-step guide for each client
- ✓ Exact file paths
- ✓ Example configuration snippets
- ✓ Security explanations

### 4. LLM Guidance
- ✓ Tool description warns LLMs about security
- ✓ Recommends llm_config_guide over llm_config_set
- ✓ Explains training data exposure risk

## Configuration Examples

### OpenAI (Claude Desktop)
```json
{
  "mcpServers": {
    "uer": {
      "command": "uv",
      "args": ["--directory", "C:\\Users\\margu\\UER", "run", "uer"],
      "env": {
        "OPENAI_API_KEY": "sk-proj-..."
      }
    }
  }
}
```

### Multiple Providers
```json
{
  "mcpServers": {
    "uer": {
      "command": "uv",
      "args": ["--directory", "C:\\Users\\margu\\UER", "run", "uer"],
      "env": {
        "OPENAI_API_KEY": "sk-proj-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GEMINI_API_KEY": "AIza..."
      }
    }
  }
}
```

### Azure with Deployment
```json
{
  "mcpServers": {
    "uer": {
      "command": "uv",
      "args": ["--directory", "C:\\Users\\margu\\UER", "run", "uer"],
      "env": {
        "AZURE_API_KEY": "...",
        "AZURE_API_BASE": "https://my-resource.openai.azure.com",
        "AZURE_API_VERSION": "2024-02-15-preview"
      }
    }
  }
}
```

## Provider-Specific Environment Variables

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

## Testing

Run the security warning test:

```bash
python scripts/test_security_warnings.py
```

**Test Coverage**:
- ✓ Detects MCP client location
- ✓ Triggers security warning for API keys
- ✓ Generates configuration guide
- ✓ Provides client-specific instructions
- ✓ No warning for non-sensitive config

## Benefits

### For Users
- ✓ Protected from accidentally exposing API keys
- ✓ Clear guidance on secure configuration
- ✓ No need to understand security risks
- ✓ Automatic detection of their setup

### For LLMs
- ✓ Clear tool descriptions about security
- ✓ Alternative secure methods provided
- ✓ Prevents inadvertent key exposure
- ✓ Maintains user trust

### For Training Data
- ✓ No API keys in chat conversations
- ✓ No credentials in training data
- ✓ Future models can't reveal keys
- ✓ Protects user privacy

## Best Practices

### For LLMs
1. **Always use `llm_config_guide`** when API keys are needed
2. **Never ask users** to share API keys in chat
3. **Explain the risk** of training data exposure
4. **Provide clear instructions** for secure setup
5. **Verify user understanding** before proceeding

### For Users
1. **Never share API keys** in chat conversations
2. **Add keys to MCP client config** file directly
3. **Use environment variables** not config registry
4. **Restart client** after adding keys
5. **Rotate keys regularly** for security

## Future Enhancements

1. **Encryption**: Encrypt config registry for additional security
2. **Key Validation**: Test keys before saving
3. **Expiration Warnings**: Warn about old keys
4. **Audit Logs**: Track configuration changes
5. **Key Rotation**: Automated key rotation reminders
