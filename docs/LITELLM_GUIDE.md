# LiteLLM Integration Guide

> Reference document for Universal Expert Registry  
> Source: Deep research on LiteLLM capabilities

---

## Overview

LiteLLM is the unified gateway layer for our Universal Expert Registry. It provides:

- **100+ LLM providers** through single interface
- **Native MCP Gateway** with permission management
- **A2A Protocol** for agent-to-agent communication
- **Cost tracking** per request
- **Rate limiting** with automatic retries
- **Fallbacks** between providers on failure

---

## Quick Start

### Installation

```bash
uv add litellm
```

### Basic Usage

```python
from litellm import completion
import os

os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["GEMINI_API_KEY"] = "..."

# Same interface - just change model string
response = completion(
    model="anthropic/claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Hello!"}]
)

response = completion(
    model="openai/gpt-5.2",
    messages=[{"role": "user", "content": "Hello!"}]
)

response = completion(
    model="gemini/gemini-3-flash-preview",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Provider Configuration

### Model String Format

```
provider/model-name
```

### Provider Prefixes

| Prefix | Provider | Example |
|--------|----------|---------|
| `anthropic/` | Anthropic (direct) | `anthropic/claude-sonnet-4-5-20250929` |
| `openai/` | OpenAI (direct) | `openai/gpt-5.2` |
| `gemini/` | Google Gemini | `gemini/gemini-3-flash-preview` |
| `azure/` | Azure OpenAI | `azure/gpt-4-deployment` |
| `bedrock/` | AWS Bedrock | `bedrock/anthropic.claude-3-sonnet` |
| `vertex_ai/` | Google Vertex AI | `vertex_ai/gemini-pro` |
| `ollama/` | Ollama (local) | `ollama/llama3.1:8b-instruct-q4_K_M` |
| `lm_studio/` | LM Studio (local) | `lm_studio/llama-3-8b` |
| `vllm/` | vLLM (local) | `hosted_vllm/meta-llama/Llama-3.1-70B` |

### Environment Variables

```bash
# Direct providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Cloud providers
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION_NAME=us-east-1

AZURE_API_KEY=...
AZURE_API_BASE=https://my-endpoint.openai.azure.com/
AZURE_API_VERSION=2023-07-01-preview
```

### Azure OpenAI

```python
response = completion(
    model="azure/my-gpt4-deployment",
    api_base="https://my-endpoint.openai.azure.com/",
    api_key=os.environ["AZURE_API_KEY"],
    api_version="2023-07-01-preview",
    messages=[...]
)
```

### AWS Bedrock

```python
response = completion(
    model="bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
    messages=[...]
)
# Uses AWS credentials from environment
```

### Local LLMs

```python
# Ollama
response = completion(
    model="ollama/llama3.1:8b-instruct-q4_K_M",
    api_base="http://localhost:11434",
    messages=[...]
)

# LM Studio
response = completion(
    model="lm_studio/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
    api_base="http://localhost:1234/v1",
    messages=[...]
)

# vLLM
response = completion(
    model="hosted_vllm/meta-llama/Llama-3.1-70B",
    api_base="http://localhost:8000/v1",
    messages=[...]
)
```

---

## Async Support

```python
from litellm import acompletion

async def call_llm():
    response = await acompletion(
        model="anthropic/claude-sonnet-4-5-20250929",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    return response.choices[0].message.content
```

---

## Streaming

```python
from litellm import completion

response = completion(
    model="openai/gpt-5.2",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content or "", end="")
```

### Async Streaming

```python
from litellm import acompletion

async def stream_response():
    response = await acompletion(
        model="openai/gpt-5.2",
        messages=[{"role": "user", "content": "Write a poem"}],
        stream=True
    )
    
    async for chunk in response:
        print(chunk.choices[0].delta.content or "", end="")
```

---

## Tool/Function Calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

response = completion(
    model="anthropic/claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto"
)

# Check for tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        print(f"Function: {tool_call.function.name}")
        print(f"Arguments: {tool_call.function.arguments}")
```

### Check Capabilities

```python
import litellm

# Check if model supports function calling
litellm.supports_function_calling(model="bedrock/anthropic.claude-3-sonnet")  # True

# Check parallel function calling
litellm.supports_parallel_function_calling(model="gpt-4-turbo")  # True
```

---

## Router with Fallbacks

```python
from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "primary",
            "litellm_params": {
                "model": "openai/gpt-5.2"
            }
        },
        {
            "model_name": "fallback-claude",
            "litellm_params": {
                "model": "anthropic/claude-sonnet-4-5-20250929"
            }
        },
        {
            "model_name": "fallback-gemini",
            "litellm_params": {
                "model": "gemini/gemini-3-flash-preview"
            }
        }
    ],
    fallbacks=[
        {"primary": ["fallback-claude", "fallback-gemini"]}
    ],
    num_retries=3,
    allowed_fails=2,
    cooldown_time=30  # seconds
)

# Use router
response = router.completion(
    model="primary",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Async
response = await router.acompletion(
    model="primary",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Context Window Fallbacks

```python
router = Router(
    model_list=[...],
    context_window_fallbacks=[
        {"gpt-3.5-turbo": ["gpt-4-32k"]},  # Upgrade on context overflow
        {"claude-instant": ["claude-2"]}
    ]
)
```

---

## Cost Tracking

```python
from litellm import completion

response = completion(
    model="anthropic/claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Cost is in response headers
print(response._hidden_params.get("response_cost"))

# Or use completion_cost
from litellm import completion_cost
cost = completion_cost(completion_response=response)
print(f"Cost: ${cost}")
```

### Model Costs

LiteLLM maintains a cost database:
- https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json

---

## Native MCP Support

### MCP Client

```python
from litellm import experimental_mcp_client

# Load tools from MCP server
tools = await experimental_mcp_client.load_mcp_tools(
    session=mcp_session,
    format="openai"  # Convert to OpenAI format
)

# Call MCP tool
result = await experimental_mcp_client.call_openai_tool(
    session=mcp_session,
    openai_tool=tool_call
)
```

### MCP Configuration (Proxy Mode)

```yaml
# litellm_config.yaml
mcp_servers:
  filesystem:
    transport: "stdio"
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
  
  postgres:
    transport: "stdio"
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-postgres"]
    env:
      DATABASE_URL: "${DATABASE_URL}"
  
  github:
    url: "https://api.githubcopilot.com/mcp"
    auth_type: oauth2
    client_id: "${GITHUB_OAUTH_CLIENT_ID}"
```

### MCP Permission Management

```yaml
# Per API key permissions
api_keys:
  - key: "sk-user1"
    mcp_servers:
      allowed: ["filesystem", "postgres"]
      disallowed_tools: ["delete_file", "drop_table"]
```

---

## A2A Protocol Support

```python
# Agent-to-Agent communication
# Endpoint: /a2a/{agent_name}/message/send

# Combine with MCP:
# - MCP: Agent ↔ Tool
# - A2A: Agent ↔ Agent
```

---

## Full API Surface

| Endpoint | Description |
|----------|-------------|
| `/chat/completions` | Chat completions |
| `/completions` | Legacy completions |
| `/embeddings` | Text embeddings |
| `/images` | Image generation |
| `/audio/transcriptions` | Speech-to-text |
| `/v1/messages` | Anthropic native format |
| `/mcp` | MCP Gateway |
| `/a2a/{agent}/message/send` | Agent-to-Agent |

---

## Error Handling

LiteLLM maps all provider exceptions to OpenAI-compatible types:

```python
from litellm import (
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
    ContextWindowExceededError
)

try:
    response = completion(model="openai/gpt-5.2", messages=[...])
except RateLimitError as e:
    print(f"Rate limited, retry after: {e.retry_after}")
except ContextWindowExceededError as e:
    print("Context too long, use smaller model")
except AuthenticationError as e:
    print("Invalid API key")
```

---

## Observability

```python
import litellm

# Enable callbacks
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["sentry"]

# Or use set_callbacks
litellm.set_callbacks(
    success=["langfuse", "datadog"],
    failure=["sentry", "slack"]
)
```

### Supported Integrations
- Langfuse
- Datadog
- MLflow
- OpenTelemetry
- Sentry
- Slack
- Custom callbacks

---

## Proxy Server Mode

For centralized deployment:

```bash
# Start proxy
litellm --config config.yaml --port 4000

# Or with Docker
docker run -p 4000:4000 ghcr.io/berriai/litellm:main-latest
```

### Config File

```yaml
model_list:
  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-sonnet-4-5-20250929
      api_key: os.environ/ANTHROPIC_API_KEY
  
  - model_name: gpt-4o
    litellm_params:
      model: azure/gpt-4o-deployment
      api_base: os.environ/AZURE_API_BASE
      api_key: os.environ/AZURE_API_KEY

litellm_settings:
  drop_params: true
  success_callback: ["langfuse"]

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

---

## Performance

- **8ms P95 latency** at 1,000 requests/second (proxy mode)
- In-memory rate limiting
- Connection pooling
- Async-first design

---

## References

- GitHub: https://github.com/BerriAI/litellm
- Docs: https://docs.litellm.ai/
- MCP Docs: https://docs.litellm.ai/docs/mcp
- A2A Docs: https://docs.litellm.ai/docs/a2a
- Model Costs: https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json
