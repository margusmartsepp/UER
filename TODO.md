# Universal Expert Registry - Implementation TODO (Revised)

> **Architecture:** LiteLLM-based unified gateway  
> **Priority:** LLM calls → MCP integration → Context sharing → Delegation

---

## Phase 1: Core Foundation & Full Setup (Day 1 Morning) ⏱️ 4 hours

**Goal:** Complete, working MCP server that users can install and test with at least one LLM provider.

### Project Setup
- [ ] `uv init` in project directory
- [ ] Create pyproject.toml with dependencies:
  ```toml
  [project]
  name = "uer"
  version = "0.1.0"
  requires-python = ">=3.11"
  dependencies = [
      "mcp>=1.0.0",
      "litellm>=1.77.0",
      "pydantic>=2.0.0",
      "httpx>=0.25.0",
  ]
  ```
- [ ] `uv sync`
- [ ] Create basic directory structure

### Environment Configuration
- [ ] Create `.env.example` file with all supported API keys:
  ```bash
  # Required: At least one LLM API key
  GEMINI_API_KEY=AIza_your_key_here  # Free tier: https://aistudio.google.com/apikey

  # Optional: Other providers
  ANTHROPIC_API_KEY=sk-ant-...
  OPENAI_API_KEY=sk-...

  # Optional: Cloud providers
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_REGION_NAME=us-east-1

  AZURE_API_KEY=...
  AZURE_API_BASE=https://....openai.azure.com/
  ```
- [ ] Add note: "Copy to your Claude Desktop config, not used as .env file"

### LiteLLM Integration
- [ ] Create `src/llm/__init__.py`
- [ ] Create `src/llm/gateway.py`:
  ```python
  import litellm
  from litellm import Router
  import os

  class LLMGateway:
      """Unified gateway to all LLM providers via LiteLLM."""

      def __init__(self):
          # Configure from environment variables
          self.available_providers = self._detect_providers()

      def _detect_providers(self) -> list[str]:
          """Detect which providers have API keys configured."""
          providers = []
          if os.getenv("GEMINI_API_KEY"): providers.append("gemini")
          if os.getenv("ANTHROPIC_API_KEY"): providers.append("anthropic")
          if os.getenv("OPENAI_API_KEY"): providers.append("openai")
          # ... etc
          return providers

      async def call(self, model: str, messages: list, tools: list = None) -> dict
      async def call_with_fallback(self, models: list, messages: list) -> dict
      def get_cost(self, response) -> float
  ```
- [ ] Test direct calls with at least one provider:
  - [ ] `gemini/gemini-3-flash-preview` (free tier)
  - [ ] Verify error handling for missing API keys
  - [ ] Test with valid and invalid API keys

### MCP Server Implementation
- [ ] Create `src/server.py`:
  ```python
  from mcp.server import Server
  from mcp.server.stdio import stdio_server
  from src.llm.gateway import LLMGateway

  app = Server("uer")
  gateway = LLMGateway()

  @app.list_tools()
  async def list_tools() -> list[Tool]:
      """List available tools."""
      return [
          Tool(
              name="llm_call",
              description="Call any LLM via LiteLLM unified interface",
              inputSchema={...}
          )
      ]

  @app.call_tool()
  async def call_tool(name: str, arguments: dict) -> list[TextContent]:
      if name == "llm_call":
          result = await gateway.call(
              model=arguments["model"],
              messages=arguments["messages"]
          )
          return [TextContent(type="text", text=str(result))]
  ```
- [ ] Implement `llm_call` tool with full schema
- [ ] Add error handling for missing API keys
- [ ] Add helpful error messages

### Claude Desktop Configuration
- [ ] Create `config/claude_desktop_config.json.example`:
  ```json
  {
    "mcpServers": {
      "uer": {
        "command": "uv",
        "args": ["--directory", "/absolute/path/to/UER", "run", "python", "-m", "src.server"],
        "env": {
          "GEMINI_API_KEY": "AIza_your_key_here"
        }
      }
    }
  }
  ```
- [ ] Test configuration with Claude Desktop
- [ ] Verify MCP tools appear (🔨 icon)

### Documentation
- [ ] Complete README Quick Start section:
  - [ ] Prerequisites
  - [ ] Step 1: Get API Keys (with Gemini free tier link)
  - [ ] Step 2: Installation
  - [ ] Step 3: Configure Claude Desktop (both minimal and full examples)
  - [ ] Step 4: Restart Claude Desktop
  - [ ] Step 5: Test Your Setup (with example prompt)
  - [ ] Example Usage Scenarios
  - [ ] Troubleshooting section
- [ ] Add table of API key providers with links and free tier info
- [ ] Ensure someone can go from zero to working setup by following README

### End-to-End Testing
- [ ] Test with free Gemini API key:
  - [ ] Configure Claude Desktop with Gemini key
  - [ ] Restart Claude Desktop
  - [ ] Ask Claude to use llm_call to call Gemini
  - [ ] Verify response is returned correctly
- [ ] Test error cases:
  - [ ] Missing API key
  - [ ] Invalid model name
  - [ ] Rate limiting
- [ ] Document common issues in Troubleshooting section

---

## Phase 2: Storage & Context (Day 1 Afternoon) ⏱️ 3 hours

### Storage Backend
- [ ] Create `src/storage/__init__.py`
- [ ] Create `src/storage/base.py`:
  ```python
  from typing import Protocol
  
  class StorageBackend(Protocol):
      async def put(self, uri: str, data: dict) -> BlobMetadata
      async def get(self, uri: str, query: str = None) -> Blob | None
      async def delete(self, uri: str) -> bool
      async def search(self, pattern: str) -> list[BlobMetadata]
  ```
- [ ] Create `src/storage/local.py`:
  - [ ] SQLite for metadata: `blobs(uri, type, created_at, updated_at, metadata_json)`
  - [ ] Filesystem for large content: `~/.universal-registry/blobs/{hash}`
  - [ ] Implement all methods

### Data Models
- [ ] Create `src/models/__init__.py`
- [ ] Create `src/models/blob.py`:
  ```python
  class BlobType(Enum):
      DATA = "data"
      PLAN = "plan"
      RESULT = "result"
      HISTORY = "history"
  
  class Blob(BaseModel):
      uri: str
      type: BlobType
      data: dict
      created_at: datetime
      version: int
  ```

### MCP Tools: CRUD
- [ ] Create `src/tools/__init__.py`
- [ ] Create `src/tools/crud.py`:
  - [ ] `put(uri, data, ttl_hours=None)` → Store blob
  - [ ] `get(uri, query=None)` → Retrieve blob (JSONPath optional)
  - [ ] `search(pattern, type="all")` → Find blobs
- [ ] Register tools in server.py
- [ ] Test with Claude Desktop

---

## Phase 3: MCP Client Integration (Day 1 Evening) ⏱️ 3 hours

### LiteLLM MCP Client Setup
- [ ] Create `src/mcp/__init__.py`
- [ ] Create `src/mcp/client.py`:
  ```python
  from litellm import experimental_mcp_client
  
  class MCPClient:
      async def connect(self, server_config: dict)
      async def list_tools(self, server: str) -> list
      async def call_tool(self, server: str, tool: str, args: dict) -> dict
  ```

### MCP Configuration
- [ ] Create `config/litellm_config.yaml`:
  ```yaml
  mcp_servers:
    filesystem:
      transport: "stdio"
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
  ```
- [ ] Load config in gateway

### mcp_call Tool
- [ ] Create `src/tools/mcp_call.py`:
  ```python
  @tool
  async def mcp_call(server: str, tool: str, args: dict = None) -> MCPResult
  ```
- [ ] Register in server.py
- [ ] Test:
  - [ ] List tools from filesystem MCP
  - [ ] Call `read_file`
  - [ ] Call `list_directory`

### Optional: Context7 Integration
- [ ] Add context7 to config (if available)
- [ ] Test documentation queries

---

## Phase 4: Subagent Delegation (Day 2 Morning) ⏱️ 3 hours

### Chat History Builder
- [ ] Create `src/orchestration/__init__.py`
- [ ] Create `src/orchestration/history.py`:
  ```python
  class ChatHistoryBuilder:
      def add_system(self, content: str)
      def add_user(self, content: str)
      def add_assistant(self, content: str, tool_calls: list = None)
      def add_tool_result(self, tool_call_id: str, result: str)
      def add_context_ref(self, uri: str)
      def build(self) -> dict
  ```

### Message Models
- [ ] Create `src/models/message.py`:
  ```python
  class Message(BaseModel):
      role: Literal["system", "user", "assistant", "tool"]
      content: str
      tool_calls: list | None = None
      tool_call_id: str | None = None
  ```

### Subagent Orchestrator
- [ ] Create `src/tools/delegate.py`:
  ```python
  class SubagentOrchestrator:
      async def delegate(
          self,
          model: str,
          messages: list,
          tools: list = None,
          context_refs: list = None,
          store_result: str = None
      ) -> DelegationResult
  ```
  - [ ] Resolve context_refs from registry
  - [ ] Inject context into messages
  - [ ] Call LLM via LiteLLM
  - [ ] Handle tool calls (agentic loop)
  - [ ] Store result if URI provided

### delegate Tool
- [ ] Register `delegate` tool:
  ```python
  @tool
  async def delegate(
      model: str,
      task: str,
      messages: list = None,
      tools: list = None,
      context_refs: list = None,
      store_result: str = None
  ) -> DelegationResult
  ```
- [ ] Test:
  - [ ] Simple delegation to different model
  - [ ] Delegation with context_refs
  - [ ] Delegation with tool access

---

## Phase 5: Plans & Continuation (Day 2 Afternoon) ⏱️ 3 hours

### Plan Schema
- [ ] Create `src/models/plan.py`:
  ```python
  class PlanStep(BaseModel):
      id: str
      description: str
      model: str | None = None
      tools: list | None = None
      context_refs: list | None = None
      status: Literal["pending", "running", "completed", "failed"]
      result_uri: str | None = None
  
  class Plan(BaseModel):
      uri: str
      task: str
      steps: list[PlanStep]
      current_step: int
      status: str
      created_at: datetime
  ```

### Plan Manager
- [ ] Create `src/tools/plans.py`:
  ```python
  class PlanManager:
      async def create(self, task: str, steps: list) -> str  # Returns URI
      async def continue_plan(self, uri: str) -> ContinuationResult
      async def get_status(self, uri: str) -> PlanStatus
  ```

### Continuation Logic
- [ ] Create `src/orchestration/continuation.py`:
  - [ ] Track token budget
  - [ ] Yield when budget exceeded
  - [ ] Generate continuation tag
  - [ ] Resume from checkpoint

### plan_create / plan_continue Tools
- [ ] Register `plan_create` tool
- [ ] Register `plan_continue` tool
- [ ] Test:
  - [ ] Create multi-step plan
  - [ ] Execute until yield
  - [ ] Continue and complete

---

## Phase 6: Demo & Polish (Day 2 Evening) ⏱️ 2 hours

### Demo Scenarios
- [ ] **Multi-LLM Comparison:**
  - Ask same question to Claude, GPT, Gemini
  - Compare responses
- [ ] **Context Sharing:**
  - Store large document
  - Delegate analysis to subagent with URI ref
  - Show token savings
- [ ] **MCP Tool Chain:**
  - Read file via filesystem MCP
  - Analyze with LLM
  - Write result back

### Documentation
- [ ] Complete README.md
- [ ] Add usage examples
- [ ] Claude Desktop config example
- [ ] Demo walkthrough

### Polish
- [ ] Consistent error messages
- [ ] Logging with levels
- [ ] Cleanup on shutdown
- [ ] Handle keyboard interrupt

---

## File Checklist

```
UER/
├── README.md                    ✅ CREATED
├── ADR.plan.md                  ✅ UPDATED
├── TODO.md                      ✅ UPDATED
├── pyproject.toml               [ ]
│
├── src/
│   ├── __init__.py              [ ]
│   ├── server.py                [ ]
│   │
│   ├── llm/
│   │   ├── __init__.py          [ ]
│   │   └── gateway.py           [ ]
│   │
│   ├── mcp/
│   │   ├── __init__.py          [ ]
│   │   └── client.py            [ ]
│   │
│   ├── storage/
│   │   ├── __init__.py          [ ]
│   │   ├── base.py              [ ]
│   │   └── local.py             [ ]
│   │
│   ├── tools/
│   │   ├── __init__.py          [ ]
│   │   ├── llm_call.py          [ ]
│   │   ├── mcp_call.py          [ ]
│   │   ├── crud.py              [ ]
│   │   ├── delegate.py          [ ]
│   │   └── plans.py             [ ]
│   │
│   ├── orchestration/
│   │   ├── __init__.py          [ ]
│   │   ├── history.py           [ ]
│   │   └── continuation.py      [ ]
│   │
│   └── models/
│       ├── __init__.py          [ ]
│       ├── blob.py              [ ]
│       ├── message.py           [ ]
│       └── plan.py              [ ]
│
├── config/
│   ├── litellm_config.yaml      [ ]
│   └── claude_desktop_config.json.example [ ]
│
└── tests/
    ├── test_llm.py              [ ]
    ├── test_storage.py          [ ]
    └── test_delegate.py         [ ]
```

---

## Quick Commands

```bash
# Initialize
cd UER
uv init
uv add mcp litellm pydantic httpx

# Run server
uv run python -m src.server

# Test with MCP inspector
npx @modelcontextprotocol/inspector uv run python -m src.server

# Install filesystem MCP (for testing)
npx -y @modelcontextprotocol/server-filesystem .
```

---

## Environment Variables

```bash
# Required for LLM calls
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Optional for cloud providers
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION_NAME=us-east-1
AZURE_API_KEY=...
AZURE_API_BASE=https://....openai.azure.com/
```

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM Gateway | LiteLLM | 100+ providers, native MCP, saves 60% effort |
| Storage | SQLite + files | No external deps, works offline |
| MCP Client | LiteLLM's | Already integrated, tested |
| Language | Python | Matches Hilaryous-Auditor, good MCP SDK |
| Package Manager | uv | Fast, modern, reliable |

---

## What We DON'T Build

Thanks to LiteLLM:
- ❌ Provider-specific API code (Anthropic, OpenAI, Google, etc.)
- ❌ Rate limiting logic
- ❌ Cost tracking infrastructure
- ❌ Fallback/retry logic
- ❌ MCP client from scratch

This lets us focus on:
- ✅ Context storage and sharing
- ✅ Chat history building
- ✅ Subagent orchestration
- ✅ Plan/continuation management

---

## Success Metrics

### Hackathon Demo Must-Have
- [ ] Call 3+ different LLM providers through single interface
- [ ] Call at least one MCP server (filesystem)
- [ ] Store and retrieve context
- [ ] Delegate to subagent with context URI
- [ ] Show token savings (URI vs full copy)

### Stretch Goals
- [ ] Context7 for documentation queries
- [ ] Plan continuation across messages
- [ ] Cost tracking display
- [ ] Multi-step workflow demo

---

*Track progress by checking boxes. Estimated total: ~14 hours.*
