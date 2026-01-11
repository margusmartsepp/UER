# Configuration Guide

This guide covers how to configure the UER MCP server for different clients and how to obtain API keys for various LLM providers.

## Table of Contents

- [API Keys (Required)](#api-keys-required)
- [Client-Specific Configuration](#client-specific-configuration)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

## API Keys (Required)

**⚠️ Important**: You must provide at least one LLM API key. The keys you provide determine which models you can access through UER.

### Quick Links to Get API Keys

| Provider | Get Your API Key | Environment Variable | Free Tier |
|----------|------------------|---------------------|-----------|
| **Cerebras** ⭐ | [cloud.cerebras.ai/platform](https://cloud.cerebras.ai/platform) | `CEREBRAS_API_KEY` | ✅ Free tier available (fast inference) |
| **LM Studio (Local)** 🏠 | [lmstudio.ai](https://lmstudio.ai) | `OPENAI_API_BASE` | ✅ 100% Free - runs locally |
| **Google Gemini** | [aistudio.google.com/api-keys](https://aistudio.google.com/api-keys) | `GEMINI_API_KEY` | ✅ Free tier available |
| **Anthropic (Claude)** | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) | `ANTHROPIC_API_KEY` | $5 credit for new users |
| **OpenAI (GPT)** | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | `OPENAI_API_KEY` | $5 credit for new users |
| **Azure OpenAI** | [portal.azure.com](https://portal.azure.com/) | `AZURE_API_KEY`, `AZURE_API_BASE` | Requires subscription |
| **AWS Bedrock** | [console.aws.amazon.com/bedrock](https://console.aws.amazon.com/bedrock/) | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION_NAME` | Pay-as-you-go |

⭐ **Recommended for testing**: Start with Cerebras (free cloud, very fast) or LM Studio (free local)!

### How to Get a Cerebras API Key (Free)

1. Visit [https://cloud.cerebras.ai/platform](https://cloud.cerebras.ai/platform)
2. Sign up or sign in with your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy your key and add it to your MCP configuration (see below)

**Free tier includes**:
- Very fast inference (optimized hardware)
- Generous token limits
- Access to Llama models

### How to Get a Gemini API Key (Free)

1. Visit [https://aistudio.google.com/api-keys](https://aistudio.google.com/api-keys)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your key (starts with `AIza...`)
5. Add it to your MCP configuration (see below)

**Free tier includes**:
- 10-15 requests/minute
- 250K tokens/minute
- 250-1000 requests/day (varies by model)

### How to Use LM Studio (100% Free, Runs Locally)

**LM Studio** lets you run LLMs locally on your computer - no API keys, no internet required, completely free!

1. **Download LM Studio**: Visit [lmstudio.ai](https://lmstudio.ai) and download for your OS
2. **Download a Model**:
   - Open LM Studio
   - Go to the "Discover" tab
   - Search for models (recommended: `llama-3.1-8b`, `mistral-7b`, `phi-3`)
   - Click download (models are 4-8GB typically)
3. **Start the Local Server**:
   - Load your downloaded model
   - Click "Start Server" (default port: 1234)
   - You'll see: `HTTP server listening on port 1234`
4. **Configure UER**:
   - Add `OPENAI_API_BASE` and `OPENAI_API_KEY` to your MCP config (see below)
   - Use any dummy value for `OPENAI_API_KEY` (e.g., `"sk-local"`) - it won't be validated

**Advantages**:
- ✅ 100% free, no usage limits
- ✅ Works offline
- ✅ Complete privacy - data never leaves your computer
- ✅ No rate limits or quotas

**Requirements**:
- 8GB+ RAM (16GB recommended)
- 10GB+ disk space for models
- Modern CPU (GPU optional but faster)

## Client-Specific Configuration

### Claude Desktop

**Location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Minimal Configuration (Cerebras only):**
```json
{
  "mcpServers": {
    "uer": {
      "command": "npx",
      "args": ["uer-mcp@latest"],
      "env": {
        "CEREBRAS_API_KEY": "your_actual_key_here"
      }
    }
  }
}
```

**Full Configuration (Multiple Providers):**
```json
{
  "mcpServers": {
    "uer": {
      "command": "npx",
      "args": ["uer-mcp@latest"],
      "env": {
        "CEREBRAS_API_KEY": "your_actual_key_here",
        "GEMINI_API_KEY": "AIza_your_actual_key_here",
        "ANTHROPIC_API_KEY": "sk-ant-your_actual_key_here",
        "OPENAI_API_KEY": "sk-your_actual_key_here",
        "AWS_ACCESS_KEY_ID": "your_aws_key",
        "AWS_SECRET_ACCESS_KEY": "your_aws_secret",
        "AWS_REGION_NAME": "us-east-1",
        "AZURE_API_KEY": "your_azure_key",
        "AZURE_API_BASE": "https://your-resource.openai.azure.com/"
      }
    }
  }
}
```

**LM Studio Configuration (Local Models):**
```json
{
  "mcpServers": {
    "uer": {
      "command": "npx",
      "args": ["uer-mcp@latest"],
      "env": {
        "OPENAI_API_BASE": "http://localhost:1234/v1",
        "OPENAI_API_KEY": "sk-local"
      }
    }
  }
}
```

**Note**: LM Studio requires `OPENAI_API_KEY` to be set (LiteLLM requirement), but the value can be any dummy string like `"sk-local"` since local servers don't validate it.

**Custom Port**: If you changed LM Studio's port (e.g., to 8080), use:
```json
"OPENAI_API_BASE": "http://localhost:8080/v1"
```

**Usage**: Call models with `openai/` prefix:
- `llm_call` with `model="openai/local-model"` (any name works)
- LM Studio uses whatever model is currently loaded

**After configuration:**
1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Look for the 🔨 (hammer) icon indicating MCP tools are loaded

### VS Code / VS Code Insiders

**Using the Install Button:**

Click the install button in the [README](README.md) or use the VS Code CLI:

```bash
# For VS Code
code --add-mcp '{"name":"uer","command":"npx","args":["uer-mcp@latest"]}'

# For VS Code Insiders
code-insiders --add-mcp '{"name":"uer","command":"npx","args":["uer-mcp@latest"]}'
```

**Manual Configuration:**

Follow the [VS Code MCP guide](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_add-an-mcp-server).

Add API keys through VS Code settings or your MCP configuration file.

### Cursor

**Using the Install Button:**

Click the Cursor install button in the [README](README.md).

**Manual Configuration:**

1. Go to `Cursor Settings` → `MCP` → `Add new MCP Server`
2. Name: `uer`
3. Type: `command`
4. Command: `npx uer-mcp@latest`
5. Add environment variables for your API keys

### Windsurf

Follow the [Windsurf MCP documentation](https://docs.windsurf.com/windsurf/cascade/mcp).

Add the standard configuration with your API keys to your Windsurf MCP settings.

### Other MCP Clients

For other MCP clients (Goose, Codex, Amp, etc.), add this configuration to your MCP settings file:

```json
{
  "mcpServers": {
    "uer": {
      "command": "npx",
      "args": ["uer-mcp@latest"],
      "env": {
        "GEMINI_API_KEY": "your-key-here"
      }
    }
  }
}
```

## Environment Variables

### Required (At Least One)

You must provide at least one of these:

- `GEMINI_API_KEY` - Google Gemini models
- `ANTHROPIC_API_KEY` - Claude models
- `OPENAI_API_KEY` - GPT models

### Optional (For Additional Providers)

**Azure OpenAI:**
- `AZURE_API_KEY` - Your Azure OpenAI API key
- `AZURE_API_BASE` - Your Azure OpenAI endpoint URL

**AWS Bedrock:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION_NAME` - AWS region (e.g., `us-east-1`)

### Security Notes

- API keys are stored locally in your MCP client configuration
- Keys are never sent to any server except the LLM provider APIs
- The UER server runs locally on your machine
- Each user brings their own keys (BYOK model)

## Troubleshooting

### "No providers available" error

**Cause**: No valid API keys were provided or detected.

**Solution**:
1. Check that you've added at least one API key to the `env` section
2. Verify your API key is correct (check for typos)
3. Ensure the key format is correct:
   - Gemini: starts with `AIza`
   - Anthropic: starts with `sk-ant-`
   - OpenAI: starts with `sk-`

### "Provider 'X' not available" error

**Cause**: You're trying to use a provider for which you haven't provided an API key.

**Solution**:
1. Add the required API key to your configuration
2. Restart your MCP client
3. Try again

### API key not working

**Checklist**:
- [ ] Key is copied correctly (no extra spaces)
- [ ] Key is active and not expired
- [ ] Key has the correct permissions
- [ ] For Gemini: API is enabled in Google Cloud Console
- [ ] For Claude/GPT: Account has credits or payment method

### Server not starting

**Check**:
1. Node.js 14+ is installed: `node --version`
2. Python 3.11+ is installed: `python --version`
3. MCP client configuration file is valid JSON
4. Restart your MCP client after configuration changes

### Need Help?

- Check the [main README](README.md) for general information
- Review the [PUBLISHING.md](PUBLISHING.md) for development setup
- Open an issue on [GitHub](https://github.com/margusmartsepp/UER/issues)

## Example Configurations

### Minimal Setup (Gemini Only)

Perfect for testing and free tier usage:

```json
{
  "mcpServers": {
    "uer": {
      "command": "npx",
      "args": ["uer-mcp@latest"],
      "env": {
        "GEMINI_API_KEY": "AIza_your_key_here"
      }
    }
  }
}
```

### Development Setup (Multiple Providers)

For developers who want access to all models:

```json
{
  "mcpServers": {
    "uer": {
      "command": "npx",
      "args": ["uer-mcp@latest"],
      "env": {
        "GEMINI_API_KEY": "AIza_your_key_here",
        "ANTHROPIC_API_KEY": "sk-ant-your_key_here",
        "OPENAI_API_KEY": "sk-your_key_here"
      }
    }
  }
}
```

### Enterprise Setup (All Providers)

For organizations using multiple cloud providers:

```json
{
  "mcpServers": {
    "uer": {
      "command": "npx",
      "args": ["uer-mcp@latest"],
      "env": {
        "GEMINI_API_KEY": "AIza_your_key_here",
        "ANTHROPIC_API_KEY": "sk-ant-your_key_here",
        "OPENAI_API_KEY": "sk-your_key_here",
        "AWS_ACCESS_KEY_ID": "your_aws_key",
        "AWS_SECRET_ACCESS_KEY": "your_aws_secret",
        "AWS_REGION_NAME": "us-east-1",
        "AZURE_API_KEY": "your_azure_key",
        "AZURE_API_BASE": "https://your-resource.openai.azure.com/"
      }
    }
  }
}
```
