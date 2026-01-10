# Universal Expert Registry - Implementation TODO (Revised)

> **Architecture:** LiteLLM-based unified gateway
> **Priority:** LLM calls → MCP integration → Context sharing → Delegation

---

## Phase 1: Core Foundation & Full Setup (Day 1 Morning) ⏱️ 4 hours

**Goal:** Complete, working MCP server that users can install and test with at least one LLM provider.

### Project Setup
- [x] `uv init` in project directory
- [x] Create pyproject.toml with dependencies:
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
- [x] `uv sync`
- [x] Create basic directory structure

### Environment Configuration
- [x] Create `.env.example` file with all supported API keys:
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
- [x] Add note: "Copy to your Claude Desktop config, not used as .env file"

### LiteLLM Integration
- [x] Create `src/llm/__init__.py`
- [x] Create `src/llm/gateway.py`:
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
- [x] Test direct calls with at least one provider:
  - [x] `gemini/gemini-3-flash-preview` (free tier)
  - [x] Verify error handling for missing API keys
  - [x] Test with valid and invalid API keys

### MCP Server Implementation
- [x] Create `src/server.py`:
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
- [x] Implement `llm_call` tool with full schema
- [x] Add error handling for missing API keys
- [x] Add helpful error messages

### Claude Desktop Configuration
- [x] Create `config/claude_desktop_config.json.example`:
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
- [x] Test configuration with Claude Desktop
- [x] Verify MCP tools appear (🔨 icon)

### Documentation
- [x] Complete README Quick Start section:
  - [x] Prerequisites
  - [x] Step 1: Get API Keys (with Gemini free tier link)
  - [x] Step 2: Installation
  - [x] Step 3: Configure Claude Desktop (both minimal and full examples)
  - [x] Step 4: Restart Claude Desktop
  - [x] Step 5: Test Your Setup (with example prompt)
  - [x] Example Usage Scenarios
  - [x] Troubleshooting section
- [x] Add table of API key providers with links and free tier info
- [x] Ensure someone can go from zero to working setup by following README

### End-to-End Testing
- [x] Test with free Gemini API key:
  - [x] Configure Claude Desktop with Gemini key
  - [x] Restart Claude Desktop
  - [x] Ask Claude to use llm_call to call Gemini
  - [x] Verify response is returned correctly
- [x] Test error cases:
  - [x] Missing API key
  - [x] Invalid model name
  - [x] Rate limiting
- [x] Document common issues in Troubleshooting section

---

## Phase 1.5: Advanced Features (Bonus Implementation) ⏱️ 2 hours

**Goal:** Add advanced LLM capabilities beyond original MVP scope

### Structured Output Support
- [x] Add `response_format` parameter to LLMCallRequest
- [x] Support JSON schema validation with `json_schema` type
- [x] Enable dynamic schema generation by calling LLM
- [x] Add validation for response_format structure
- [x] Pass through to LiteLLM (already supported)

### Chain of Thought Support
- [x] Add `thinking_level` parameter for Gemini 3 (minimal/low/medium/high)
- [x] Add `thinking_budget` parameter for Gemini 2.5 (128-32768 tokens, -1 for dynamic)
- [x] Add validation for thinking parameters
- [x] Document usage in tool description
- [x] Pass through to LiteLLM (already supported)

### Tool Use Support
- [x] Add `tools` parameter to LLMCallRequest
- [x] Support Claude built-in tools (web_search_20250305, bash_20250305)
- [x] Support Gemini tools (code_execution, google_search_retrieval)
- [x] Support OpenAI function calling format
- [x] Add comprehensive tool documentation in schema
- [x] Log tool usage in server logs
- [x] Pass through to LiteLLM (already supported)

### Enhanced Error Handling
- [x] Pydantic validation for all request parameters
- [x] Specific error messages for validation failures
- [x] Runtime error handling for missing API keys
- [x] Comprehensive exception handling with logging
- [x] User-friendly error responses in JSON format

### Enhanced Logging
- [x] Configure logging with timestamps and levels
- [x] Log LLM call parameters (model, message count, features)
- [x] Log usage information (tokens, model)
- [x] Log errors with stack traces
- [x] Structured logging for debugging

---

## Phase 1.9: npm Package Distribution (Playwright Model) ⏱️ 1 hour

**Goal:** Enable zero-installation deployment via npm/npx like Playwright MCP

### Package Structure
- [x] Create package.json for uer-mcp npm package
- [x] Create bin/uer-mcp.js entry point script
- [x] Add build process to bundle Python code (scripts/build_python.py)
- [x] Add dependency detection (uv, python)
- [x] Create .npmignore to exclude development files

### Build & Test Scripts
- [x] Set up npm build scripts (prepare, build, prepack)
- [x] Create test script to verify package structure
- [x] Add automated build process for Python bundling

### Documentation
- [x] Update README with npm installation instructions
- [x] Add npx usage examples as primary method
- [x] Document manual installation for development
- [x] Update Claude Desktop config examples

### Publishing (Ready to Deploy)
- [x] Test package locally with npm pack
- [x] Test installation with npx from local tarball
- [x] Publish to npm registry (npm publish) - v1.0.3 live
- [x] Test installation from npm: npx uer-mcp@latest
- [x] Add version management documentation (CI_CD_SETUP.md, PUBLISHING.md)
- [x] Add logo to package and README
- [x] Setup GitHub Actions for automated publishing
- [x] Configure npm package metadata for MCP clients

---

## Phase 2: S3-Native Storage & Context (Day 1 Afternoon) ⏱️ 7 hours

> **Architecture:** S3-compatible storage with MinIO (local), Skills API compliance, Jinja2 templates
> **Reference:** [docs/ADR-002-S3-Storage-Architecture.md](docs/ADR-002-S3-Storage-Architecture.md)

### Phase 2a: Core S3 Storage ✅ COMPLETE

**Goal:** S3-compatible storage with local MinIO backend

#### Storage Backend Interface ✅
- [x] Create `src/uer/storage/__init__.py`
- [x] Create `src/uer/storage/base.py`:
  ```python
  from typing import Protocol
  from datetime import datetime
  from enum import Enum

  class RetentionMode(Enum):
      GOVERNANCE = "GOVERNANCE"
      COMPLIANCE = "COMPLIANCE"

  class Retention:
      mode: RetentionMode
      retain_until_date: datetime

  class ObjectMetadata:
      bucket: str
      key: str
      size: int
      content_type: str
      last_modified: datetime
      etag: str
      version_id: str | None = None
      metadata: dict[str, str] = {}

  class StorageBackend(Protocol):
      async def put_object(bucket, key, data, content_type, metadata) -> ObjectMetadata
      async def get_object(bucket, key) -> tuple[bytes, ObjectMetadata]
      async def delete_object(bucket, key) -> bool
      async def list_objects(bucket, prefix, recursive) -> list[ObjectMetadata]
      async def object_exists(bucket, key) -> bool
      async def set_object_retention(bucket, key, retention) -> None  # Optional
  ```
- [x] Document interface with examples

#### MinIO Backend Implementation ✅
- [x] Create `src/uer/storage/minio_backend.py`
- [x] Initialize MinIO client from environment (MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE)
- [x] Implement `put_object` with content type and metadata support
- [x] Implement `get_object` returning data + metadata
- [x] Implement `delete_object`
- [x] Implement `list_objects` with prefix filtering and recursive option
- [x] Implement `object_exists` helper
- [x] Add connection pooling and error handling
- [x] Auto-create default buckets: `uer-context`, `uer-skills`, `uer-templates` (lazy initialization)
- [x] **BONUS:** Lazy initialization to support optional storage
- [x] **BONUS:** Flexible configuration with 3 deployment modes

#### Storage Manager ✅
- [x] Create `src/uer/storage/manager.py`
- [x] URI parsing: `registry://type/key` → `s3://uer-{type}/key`
- [x] URI parsing: `s3://bucket/key` → `(bucket, key)`
- [x] Convenience methods wrapping backend
- [x] Lazy backend initialization (not on startup)
- [x] **BONUS:** Storage availability checking
- [x] **BONUS:** Support for disabled storage mode

#### Environment Configuration ✅
- [x] Add MinIO config to `.env.example`:
  ```bash
  # Storage Backend (MinIO for local development)
  STORAGE_BACKEND=minio
  MINIO_ENDPOINT=localhost:9000
  MINIO_ACCESS_KEY=minioadmin
  MINIO_SECRET_KEY=minioadmin
  MINIO_SECURE=false
  ```
- [x] Create `docker-compose.yml` for MinIO:
  ```yaml
  services:
    minio:
      image: minio/minio:latest
      command: server /data --console-address ":9001"
      ports:
        - "9000:9000"  # S3 API
        - "9001:9001"  # Web Console
      environment:
        MINIO_ROOT_USER: minioadmin
        MINIO_ROOT_PASSWORD: minioadmin
      volumes:
        - ./data/minio:/data
  ```
- [x] Document MinIO setup in README (one-command: `docker-compose up -d`)
- [x] **BONUS:** Document all 3 storage configuration options in README
- [x] **BONUS:** Add storage config class (`src/uer/storage/config.py`)
- [x] **BONUS:** Conditional tool registration based on storage availability

#### Testing ✅
- [x] Test MinIO connection
- [x] Test bucket creation (lazy initialization)
- [x] Test put/get/delete operations
- [x] Test prefix filtering (list skills, list contexts)
- [x] Test error handling (bucket not found, object not found, connection failed)
- [x] **BONUS:** Test storage disabled mode (STORAGE_ENABLED=false)
- [x] **BONUS:** Test Docker MinIO mode (default)
- [x] **BONUS:** Verify server starts without MinIO running

---

### Phase 2b: Skills & Templates (2 hours)

**Goal:** Claude Skills API compliance + Jinja2 template expansion

#### Skills Manager
- [ ] Create `src/uer/storage/skills.py`
- [ ] `create_skill(name, display_title, files: dict[str, bytes])` → SkillMetadata
  - [ ] Validate SKILL.md exists in files
  - [ ] Store all files under `s3://uer-skills/{name}/`
  - [ ] Store metadata in `s3://uer-skills/{name}/.metadata.json`
- [ ] `get_skill(name)` → Skill with all files
- [ ] `list_skills()` → list of skill names
- [ ] `export_for_api(name)` → Claude Skills API format
  ```python
  return {
      "display_title": "Financial Analysis",
      "files": [
          {"filename": "SKILL.md", "content": b"..."},
          {"filename": "scripts/analyze.py", "content": b"..."}
      ]
  }
  ```
- [ ] `to_system_prompt(name)` → Convert skill to system prompt for GPT/Gemini

#### Template Manager
- [ ] Create `src/uer/storage/templates.py`
- [ ] Create `S3TemplateLoader(BaseLoader)` for Jinja2
  - [ ] Load templates from S3 storage
  - [ ] Cache templates for performance
- [ ] Create `TemplateManager` class
  - [ ] Initialize Jinja2 Environment with S3TemplateLoader
  - [ ] Add custom filter: `expand` - `{{ uri | expand }}` → load content from S3
  - [ ] Add custom filter: `s3` - `{{ key | s3 }}` → load from default bucket
- [ ] `render(template_key, context)` → rendered content
- [ ] Support async template rendering

#### Testing
- [ ] Create test skill with SKILL.md + Python script
- [ ] Store skill via `create_skill`
- [ ] Retrieve skill via `get_skill`
- [ ] Export skill for Claude API
- [ ] Create Jinja2 template with `expand` filter
- [ ] Render template with context from S3

---

### Phase 2c: MCP Tools (2 hours)

**Goal:** Expose S3 storage to LLMs via MCP tools

#### Storage Tools
- [ ] Create `src/uer/tools/storage_tools.py`
- [ ] `storage_put(uri, content, content_type, metadata)` → ObjectMetadata
  ```python
  @tool
  async def storage_put(
      uri: str,  # "s3://bucket/key" or "registry://type/key"
      content: str | bytes,
      content_type: str = "application/octet-stream",
      metadata: dict = None
  ) -> dict:
      """Store content at URI in S3-compatible storage."""
  ```
- [ ] `storage_get(uri)` → content + metadata
  ```python
  @tool
  async def storage_get(uri: str) -> dict:
      """Retrieve content from URI."""
      # Returns: {"content": "...", "metadata": {...}}
  ```
- [ ] `storage_list(prefix, recursive)` → list of objects
  ```python
  @tool
  async def storage_list(
      prefix: str = "",  # "s3://bucket/prefix/" or "registry://skills/"
      recursive: bool = True
  ) -> list[dict]:
      """List objects under prefix."""
  ```
- [ ] `storage_delete(uri)` → success boolean
  ```python
  @tool
  async def storage_delete(uri: str) -> dict:
      """Delete object at URI."""
  ```

#### Skills Tools
- [ ] `skill_create(name, display_title, skill_md, files)` → SkillMetadata
  ```python
  @tool
  async def skill_create(
      name: str,
      display_title: str,
      skill_md: str,
      files: dict = None  # {"scripts/analyze.py": "content", ...}
  ) -> dict:
      """Create Claude Skill in storage."""
  ```
- [ ] `skill_get(name)` → Skill with all files
- [ ] `skill_list()` → list of available skills
- [ ] `skill_export(name)` → Claude Skills API format

#### Template Tools
- [ ] `template_render(template_uri, context)` → rendered content
  ```python
  @tool
  async def template_render(
      template_uri: str,  # "s3://uer-templates/meeting-notes.md"
      context: dict  # {"meeting": {"title": "...", "date": "..."}}
  ) -> dict:
      """Render Jinja2 template with context expansion."""
  ```
- [ ] `template_list()` → available templates

#### Register in Server
- [ ] Add all storage tools to `src/uer/server.py`
- [ ] Update tool schemas with comprehensive examples
- [ ] Add error handling for all tools
- [ ] Document each tool in tool description

#### Testing
- [ ] Test with Claude Desktop
- [ ] Store context via `storage_put` MCP tool
- [ ] Retrieve context via `storage_get` MCP tool
- [ ] List objects via `storage_list` MCP tool
- [ ] Create skill via `skill_create` MCP tool
- [ ] Render template via `template_render` MCP tool
- [ ] Verify Jinja2 `expand` filter works (loads from S3)

---

### Phase 2d: Advanced Features (Optional, 2 hours)

**Goal:** WORM compliance, versioning, multi-backend support

#### WORM/Compliance Support
- [ ] Add `set_object_retention` to MinIO backend
  ```python
  async def set_object_retention(
      bucket: str,
      key: str,
      retention: Retention
  ) -> None:
      """Set WORM retention (requires bucket created with object_lock=True)."""
  ```
- [ ] Add `get_object_retention` to MinIO backend
- [ ] Create `storage_set_retention` MCP tool (admin-only)
  ```python
  @tool
  async def storage_set_retention(
      uri: str,
      mode: Literal["GOVERNANCE", "COMPLIANCE"],
      retain_days: int
  ) -> dict:
      """Set WORM retention on object (MinIO/S3 only)."""
  ```
- [ ] Document compliance use cases (legal docs, audit logs, ML versioning)
- [ ] Test retention settings with MinIO

#### Versioning Support
- [ ] Document how to enable versioning in MinIO bucket config
  ```bash
  # mc version enable minio/uer-context
  ```
- [ ] Add `version_id` to ObjectMetadata (already in base.py)
- [ ] Add `get_object_version(bucket, key, version_id)` method
- [ ] Add `list_object_versions(bucket, key)` method
- [ ] Test versioning with MinIO

#### Multi-Backend Support (Future)
- [ ] Create `src/uer/storage/s3_backend.py` for AWS S3
  ```python
  class S3Backend(StorageBackend):
      """AWS S3 backend using boto3."""
      # Same interface as MinIO, different implementation
  ```
- [ ] Create `src/uer/storage/azure_backend.py` for Azure Blob
- [ ] Add backend factory in `manager.py`
  ```python
  def get_storage_backend() -> StorageBackend:
      backend_type = os.getenv("STORAGE_BACKEND", "minio")
      if backend_type == "minio":
          return MinIOBackend()
      elif backend_type == "s3":
          return S3Backend()
      elif backend_type == "azure":
          return AzureBlobBackend()
  ```
- [ ] Document configuration for each backend in README

---

### Documentation Updates
- [ ] Update README.md with MinIO setup instructions
- [ ] Add S3 URI examples (`s3://bucket/key`, `registry://type/key`)
- [ ] Document Skills API compliance
- [ ] Document Jinja2 template system with examples
- [ ] Add WORM/compliance use cases
- [ ] Reference ADR-002 in README

---

## Phase 3: MCP Client Integration (Day 1 Evening) ✅ COMPLETE

### Core MCP Infrastructure
- [x] Create `src/mcp/__init__.py`
- [x] Create `src/mcp/config.py` with MCPServerConfig and MCPConfig models
- [x] Create `src/mcp/manager.py` with MCPManager for connection handling
- [x] Use native MCP Python SDK (not LiteLLM experimental)
- [x] Implement fresh connections per request (avoid async context issues)

### Transport Support
- [x] **stdio transport** - Local subprocess communication (npx, uvx, python)
- [x] **SSE transport** - Server-Sent Events over HTTP for remote servers
- [x] **HTTP transport** - HTTP POST/GET requests for remote servers
- [x] Add URL field for HTTP/SSE endpoints
- [x] Add headers field for authentication (Bearer tokens, API keys)

### MCP Configuration
- [x] Environment variable support: `UER_MCP_SERVERS`
- [x] Default servers: memory (npm), fetch (Python via uvx)
- [x] Filesystem server disabled by default (requires explicit directory config)
- [x] Support for both npm (npx) and Python (uvx) MCP servers

### MCP Tools (Exposed to LLM)
- [x] **mcp_call** - Call tools on external MCP servers
- [x] **mcp_list_tools** - List available tools from MCP servers
  - [x] List all configured servers (no parameters)
  - [x] Filter servers by prefix (e.g., 'hug' matches 'huggingface')
  - [x] List tools from specific server
- [x] **mcp_servers** - Full CRUD operations for server management
  - [x] list - View all configured servers
  - [x] get - View single server configuration
  - [x] add - Add new MCP servers
  - [x] update - Modify existing servers
  - [x] delete - Remove servers
- [x] **mcp_registry** - Browse and install from official MCP registry
  - [x] search - Find servers by keyword
  - [x] list - Browse all 300+ servers
  - [x] get - View server details
  - [x] install - Add server from registry to config

### Authentication & Security
- [x] Token-based authentication for remote servers
- [x] OAuth guidance for direct MCP clients
- [x] Helpful error messages for authentication failures
- [x] Support for Hugging Face MCP server with Bearer tokens
- [x] Clear guidance when 405 Method Not Allowed occurs

### Server Discovery & Error Handling
- [x] Server discovery without requiring server name
- [x] Prefix filtering for efficient server search
- [x] Show available servers in error messages
- [x] Validation: command required for stdio, url required for sse/http
- [x] Detailed error logging with helpful suggestions

### Testing & Documentation
- [x] Test with memory MCP server (npm)
- [x] Test with fetch MCP server (Python)
- [x] Create MCP_TESTING.md with comprehensive guide
- [x] Document environment variable configuration
- [x] Document CRUD operations with examples
- [x] Document SSE/HTTP transport setup
- [x] Document authentication methods

### Beyond Original Plan
- [x] Full CRUD instead of just read-only access
- [x] Registry integration for easy server discovery
- [x] SSE/HTTP transport (original plan only had stdio)
- [x] Server discovery and filtering
- [x] Dynamic server configuration (not just static config file)
- [x] Support for both npm and Python MCP ecosystems

---

## Phase 4: Subagent Delegation (Future) ⏱️ 3 hours

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
├── pyproject.toml               ✅ CREATED
│
├── src/
│   ├── __init__.py              ✅ CREATED
│   ├── server.py                ✅ CREATED
│   │
│   ├── uer/
│   │   ├── __init__.py          ✅ CREATED
│   │   ├── __main__.py          ✅ CREATED
│   │   ├── server.py            ✅ CREATED
│   │   │
│   │   ├── llm/
│   │   │   ├── __init__.py      ✅ CREATED
│   │   │   └── gateway.py       ✅ CREATED
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py      ✅ CREATED
│   │   │   └── llm.py           ✅ CREATED
│   │   │
│   │   ├── storage/             [ ] NOT STARTED
│   │   ├── tools/               [ ] NOT STARTED
│   │   ├── orchestration/       [ ] NOT STARTED
│   │   └── mcp/                 [ ] NOT STARTED
│   │
├── config/
│   └── claude_desktop_config.json.example [ ] NEEDED
│
└── tests/
    ├── __init__.py              ✅ CREATED
    └── test_llm.py              [ ] NOT STARTED
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
- [x] Call 3+ different LLM providers through single interface
- [ ] Call at least one MCP server (filesystem)
- [ ] Store and retrieve context
- [ ] Delegate to subagent with context URI
- [ ] Show token savings (URI vs full copy)

### Stretch Goals
- [ ] Context7 for documentation queries
- [ ] Plan continuation across messages
- [x] Cost tracking display (via LiteLLM usage logging)
- [ ] Multi-step workflow demo

---

*Track progress by checking boxes. Estimated total: ~14 hours.*
