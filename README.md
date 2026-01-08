# Universal Expert Registry

> **ASI-Level Experts, Infinite Memory, Any Client**

An MCP server that provides:
1. **Universal LLM Access** - Call any LLM (Claude, GPT, Gemini, Bedrock, Azure, local models) through LiteLLM
2. **MCP Tool Orchestration** - Connect to 1000+ MCP servers (filesystem, databases, browsers, etc.)
3. **Shared Memory/Context** - Break context window limits via external storage with URI references
4. **Subagent Delegation** - Spawn subagents with full chat history, not just single messages

## Why This Exists

LLMs have fundamental limitations:
- **Single message I/O**: 32-64k tokens max
- **Context window**: 200k-2M tokens
- **No persistent memory**: Forget between sessions
- **No expert access**: Can't use specialized tools

Traditional multi-agent approaches waste tokens by copying full context to each subagent. This registry solves it by:
- Storing context externally (unlimited)
- Passing URI references instead of full data (50 tokens vs 50k)
- Building complete chat histories for subagents
- Persisting across sessions

## Architecture

```mermaid
graph TB
    subgraph clients["MCP Clients"]
        A1["Cursor"]
        A2["Claude Desktop"]
        A3["ChatGPT"]
        A4["VS Code"]
        A5["JetBrains"]
    end

    subgraph uer["UER - Universal Expert Registry"]
        direction TB
        B["MCP Tools<br/>llm_call, mcp_call, put, get, delegate, search"]

        subgraph litellm["LiteLLM Gateway"]
            C1["100+ LLM providers"]
            C2["Native MCP Gateway"]
            C3["A2A Protocol support"]
            C4["Cost tracking, rate limiting, fallbacks"]
        end

        subgraph store["Context Store"]
            D1["Local: SQLite"]
            D2["Cloud: Firebase"]
        end

        B --> litellm
        B --> store
    end

    subgraph providers["LLM Providers"]
        E1["Anthropic"]
        E2["OpenAI"]
        E3["Google"]
        E4["Azure"]
        E5["AWS Bedrock"]
        E6["Local: Ollama"]
    end

    subgraph mcpservers["MCP Servers"]
        F1["Filesystem"]
        F2["PostgreSQL"]
        F3["Slack"]
        F4["Browser"]
        F5["GitHub"]
        F6["1000+ more..."]
    end

    subgraph knowledge["Knowledge Sources"]
        G1["Context7"]
        G2["Company docs"]
        G3["Guidelines"]
        G4["Standards"]
    end

    clients -->|MCP Protocol| B
    litellm --> providers
    litellm --> mcpservers
    litellm --> knowledge
```

## Key Features

### 1. Universal LLM Access via LiteLLM

Call any LLM with a single interface:

```python
# All use the same interface - just change the model string
llm_call(model="anthropic/claude-sonnet-4-5-20250929", messages=[...])
llm_call(model="openai/gpt-5.2", messages=[...])
llm_call(model="gemini/gemini-3-flash-preview", messages=[...])
llm_call(model="bedrock/anthropic.claude-3-sonnet", messages=[...])
llm_call(model="azure/gpt-4-deployment", messages=[...])
llm_call(model="ollama/llama3.1:8b-instruct-q4_K_M", messages=[...])
```

Features included:
- Automatic fallbacks between providers
- Cost tracking per request
- Rate limit handling with retries
- Tool/function calling across all providers

### 2. MCP Tool Integration

Connect to any MCP server:

```python
# List available MCP tools
search(type="mcp")

# Call MCP tools directly
mcp_call(server="filesystem", tool="read_file", args={"path": "/data/report.txt"})
mcp_call(server="postgres", tool="query", args={"sql": "SELECT * FROM users"})
mcp_call(server="context7", tool="search", args={"query": "LiteLLM API reference"})
```

### 3. Shared Context (The Killer Feature)

Store data externally, pass URI references:

```python
# Store large document (200k tokens)
put("registry://context/doc_001", {"content": large_document})

# Pass only URI to subagent (50 tokens!)
delegate(
    model="anthropic/claude-sonnet-4-5-20250929",
    task="Analyze the document",
    context_refs=["registry://context/doc_001"]
)

# Subagent retrieves full content from registry
# Result stored back to registry
# Parent retrieves summary only
```

**Token savings: 99.9%** for multi-agent workflows.

### 4. Full Chat History for Subagents

Build complete conversation context, not just single messages:

```python
delegate(
    model="openai/gpt-5-mini",
    messages=[
        {"role": "system", "content": "You are a code reviewer..."},
        {"role": "user", "content": "Review this code for security issues"},
        {"role": "assistant", "content": "I'll analyze the code..."},
        {"role": "user", "content": "Focus on SQL injection risks"}
    ],
    tools=[...],  # MCP tools available to subagent
    context_refs=["registry://context/codebase"]  # Large context via URI
)
```

### 5. Continuation Across Sessions

Complex tasks can span multiple messages and sessions:

```
Message 1: Start analysis → Progress: 20% → {{continuation: registry://plan/001}}
Message 2: Continue → Progress: 60% → {{continuation: registry://plan/001}}
[Next day]
Message 3: Continue → Complete! Here's your report...
```

## Quick Start

### Prerequisites

- **Python 3.11+**
- **uv** package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Claude Desktop** (or any MCP-compatible client)
- **At least one LLM API key** (see below)

### Step 1: Get API Keys

You need at least one LLM API key to use UER. We recommend starting with **Google Gemini** as it offers a free tier:

#### Google Gemini (Free - Recommended for Testing)

1. Visit [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Copy your key (starts with `AIza...`)
4. Free tier includes: 10-15 requests/minute, 250K tokens/minute, 250-1000 requests/day (varies by model)

#### Other Providers (Optional)

| Provider | Get API Key | Free Tier |
|----------|-------------|-----------|
| **Anthropic** (Claude) | [console.anthropic.com](https://console.anthropic.com/) | $5 credit for new users |
| **OpenAI** (GPT) | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | $5 credit for new users |
| **Azure OpenAI** | [Azure Portal](https://portal.azure.com/) | Requires Azure subscription |
| **AWS Bedrock** | [AWS Console](https://console.aws.amazon.com/bedrock/) | Pay-as-you-go |

### Step 2: Installation

```bash
# Clone or download the repository
cd UER

# Install dependencies
uv sync
```

### Step 3: Configure Claude Desktop

Add UER as an MCP server to Claude Desktop:

**Location:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)

**Minimal Configuration (Gemini only):**
```json
{
  "mcpServers": {
    "uer": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\UER", "run", "python", "-m", "src.server"],
      "env": {
        "GEMINI_API_KEY": "AIza_your_key_here"
      }
    }
  }
}
```

**Full Configuration (All providers):**
```json
{
  "mcpServers": {
    "uer": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\UER", "run", "python", "-m", "src.server"],
      "env": {
        "GEMINI_API_KEY": "AIza_your_key_here",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "OPENAI_API_KEY": "sk-...",
        "AWS_ACCESS_KEY_ID": "...",
        "AWS_SECRET_ACCESS_KEY": "...",
        "AWS_REGION_NAME": "us-east-1",
        "AZURE_API_KEY": "...",
        "AZURE_API_BASE": "https://....openai.azure.com/"
      }
    }
  }
}
```

**Important:**
- Replace `C:\\path\\to\\UER` with your actual UER directory path
- Use double backslashes `\\` on Windows, or forward slashes `/` on Mac/Linux
- Only include API keys for providers you want to use

### Step 4: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Look for the 🔨 (hammer) icon indicating MCP tools are loaded

### Step 5: Test Your Setup

Try this in Claude Desktop:

```
"Use the llm_call tool to call Gemini 3 Flash and ask it to explain what an MCP server is in one sentence."
```

Expected behavior:
- Claude will use the `llm_call` tool
- Call `gemini/gemini-3-flash-preview`
- Return Gemini's response

### Example Usage Scenarios

**1. Call Different LLMs:**
```
User: "Use llm_call to ask Gemini what the capital of France is"
→ Calls gemini/gemini-3-flash-preview
→ Returns: "Paris"

User: "Now ask Claude Sonnet the same question"
→ Calls anthropic/claude-sonnet-4-5-20250929
→ Returns: "Paris"
```

**2. Compare LLM Responses:**
```
User: "Ask both Gemini and Claude Sonnet to write a haiku about programming"
→ Uses llm_call twice with different models
→ Returns both haikus for comparison
```

**3. Store and Share Context:**
```
User: "Store this document in the registry and have Gemini summarize it"
→ put("registry://context/doc", {...})
→ delegate(model="gemini/gemini-3-flash-preview", context_refs=["registry://context/doc"])
→ Returns: Summary without re-sending full document
```

## Troubleshooting

### "MCP server not found" or "No tools available"

1. Check that `claude_desktop_config.json` is in the correct location
2. Verify the `--directory` path is correct (use absolute path)
3. Ensure you've restarted Claude Desktop after configuration
4. Check Claude Desktop logs: `%APPDATA%\Claude\logs\` (Windows) or `~/Library/Logs/Claude/` (Mac)

### "API key invalid" errors

1. Verify your API key is correct and active
2. Check you're using the right key for the right provider
3. For Gemini, ensure the key starts with `AIza`
4. For Anthropic, ensure the key starts with `sk-ant-`
5. For OpenAI, ensure the key starts with `sk-`

### "Model not found" errors

1. Ensure you have an API key configured for that provider
2. Check the model name is correct (use LiteLLM format: `provider/model`)
3. Verify the model is available in your region/tier


## Tools Reference

| Tool | Description |
|------|-------------|
| `llm_call` | Call any LLM via LiteLLM (100+ providers) |
| `mcp_call` | Call any configured MCP server tool |
| `put` | Store data/context in registry |
| `get` | Retrieve data/context from registry |
| `search` | Search MCP servers, skills, or stored context |
| `delegate` | Spawn subagent with full chat history |
| `subscribe` | Watch for async results |
| `cancel` | Cancel subscription or execution |

## LiteLLM Integration

This project uses [LiteLLM](https://github.com/BerriAI/litellm) as the unified LLM gateway, providing:

- **100+ LLM providers** through single interface
- **Native MCP Gateway** with permission management
- **A2A Protocol** for agent-to-agent communication
- **Cost tracking** per request with spend reports
- **Rate limiting** with automatic retries
- **Fallbacks** between providers on failure
- **Tool/function calling** normalized across providers

### Supported Providers

| Provider | Model Examples |
|----------|---------------|
| Anthropic | `anthropic/claude-sonnet-4-5-20250929`, `anthropic/claude-opus-4-5-20251101` |
| OpenAI | `openai/gpt-5.2`, `openai/gpt-5-mini`, `openai/gpt-5.2-codex` |
| Google | `gemini/gemini-3-flash-preview`, `gemini/gemini-3-pro-preview` |
| Azure | `azure/gpt-4-deployment` |
| AWS Bedrock | `bedrock/anthropic.claude-3-sonnet` |
| Local | `ollama/llama3.1:8b-instruct-q4_K_M`, `lm_studio/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF` |

## Project Structure

```
UER/
├── README.md               # This file
├── ADR.plan.md            # Architecture Decision Record
├── TODO.md                # Implementation checklist
├── pyproject.toml
│
├── src/
│   ├── server.py          # MCP server entry point
│   ├── llm/
│   │   └── gateway.py     # LiteLLM wrapper
│   ├── mcp/
│   │   └── client.py      # MCP client for calling other servers
│   ├── storage/
│   │   ├── base.py        # Storage protocol
│   │   └── local.py       # SQLite + filesystem
│   ├── tools/
│   │   ├── llm_call.py    # LLM invocation tool
│   │   ├── mcp_call.py    # MCP tool invocation
│   │   ├── crud.py        # put/get/search
│   │   └── delegate.py    # Subagent delegation
│   └── models/
│       ├── context.py     # Context/blob schemas
│       └── message.py     # Chat message schemas
│
└── config/
    └── litellm_config.yaml
```

## Dependencies

```toml
[project]
dependencies = [
    "mcp>=1.0.0",
    "litellm>=1.77.0",
    "pydantic>=2.0.0",
    "httpx>=0.25.0",
]
```

## Hackathon Context

This project was built for the **[AI Manipulation Hackathon](https://apartresearch.com/sprints/ai-manipulation-hackathon-2026-01-09-to-2026-01-11)** organized by [Apart Research](https://apartresearch.com/).

### Event Details

- **Dates:** January 9-11, 2026
- **Theme:** Measuring, detecting, and defending against AI manipulation
- **Participants:** 500+ builders worldwide
- **Prizes:** $2,000 in cash prizes
- **Workshop:** Winners present at IASEAI workshop in Paris (February 26, 2026)

### The Challenge

AI systems are mastering deception, sycophancy, sandbagging, and psychological exploitation at scale, while our ability to detect, measure, and counter these behaviors remains dangerously underdeveloped. This hackathon brings together builders to prototype practical systems that address this critical AI safety challenge.

### How UER Addresses AI Manipulation

The Universal Expert Registry provides infrastructure for:

1. **Multi-Model Testing** - Compare responses across providers to detect inconsistencies and manipulation patterns
2. **Persistent Context** - Track conversation history across sessions to identify behavioral shifts
3. **Tool Integration** - Connect manipulation detection tools via MCP protocol
4. **Subagent Orchestration** - Deploy specialized agents for red-teaming and safety testing
5. **Transparent Logging** - Full visibility into LLM calls, costs, and behaviors

### Team

**The Risk Takers** - Building practical tools for AI safety and transparency.

## Related Projects

- [LiteLLM](https://github.com/BerriAI/litellm) - Unified LLM gateway
- [MCP Registry](https://registry.modelcontextprotocol.io) - Official MCP server directory
- [Context7](https://github.com/upstash/context7) - Library documentation MCP
- [Apart Research](https://apartresearch.com/) - AI safety research and hackathons

## License

MIT

---

*Built for the AI Manipulation Hackathon by The Risk Takers team*
