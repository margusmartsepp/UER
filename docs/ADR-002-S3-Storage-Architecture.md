# ADR-002: S3-Native Storage Architecture

> **Project:** Universal Expert Registry
> **Status:** Proposed
> **Date:** 2026-01-10
> **Author:** Margus Martsepp
> **Supersedes:** Original Phase 2 storage plan (SQLite-based)
> **Related:** [ADR.plan.md](../ADR.plan.md), [CLAUDE.md](../CLAUDE.md)

---

## Executive Summary

**Decision:** Implement S3-native storage layer for UER context and skill storage instead of SQLite + filesystem.

**Rationale:**
- LLMs need permanent cache for code, context, and execution artifacts
- Enterprise users need NetApp/S3-compatible storage integration
- Claude Skills API compliance requires file-based storage
- WORM/compliance features needed for legal, audit, and ML versioning use cases
- Team collaboration requires shared storage backends

**Impact:**
- **Positive:** Enterprise-ready, infinitely scalable, skills-compatible, compliance-ready
- **Negative:** More complex than SQLite, requires MinIO for local development
- **Mitigation:** Start local-only with MinIO, abstract storage interface for future backends

---

## Table of Contents

1. [Context](#1-context)
2. [Decision](#2-decision)
3. [Architecture](#3-architecture)
4. [Implementation Plan](#4-implementation-plan)
5. [Skills API Compliance](#5-skills-api-compliance)
6. [Storage Backends](#6-storage-backends)
7. [Security & Compliance](#7-security--compliance)
8. [Migration Path](#8-migration-path)
9. [Consequences](#9-consequences)
10. [References](#10-references)

---

## 1. Context

### 1.1 Original Plan (Rejected)

Phase 2 originally proposed:
```python
class StorageBackend(Protocol):
    async def put(uri: str, data: dict) -> BlobMetadata
    async def get(uri: str, query: str = None) -> Blob | None
    async def delete(uri: str) -> bool
    async def search(pattern: str) -> list[BlobMetadata]

# Implementation: SQLite metadata + local filesystem
```

**Problems:**
- Not S3-compatible (limits enterprise adoption)
- No NetApp integration path
- Skills API uses file-based storage (incompatible with dict-based API)
- No native versioning or compliance features
- Doesn't scale for team collaboration

### 1.2 Requirements

**Functional:**
- LLMs can store context, code, and artifacts (permanent cache)
- Claude Skills API compliant (SKILL.md + resources)
- Jinja2 template expansion for context injection
- Works with any LLM via LiteLLM (not Claude-only)
- S3-style prefixes for virtual folders
- Support both individual files and collections

**Non-Functional:**
- Full S3 API compliance
- Mappable to enterprise storage (NetApp, AWS S3, Azure Blob)
- Optional WORM/compliance mode (legal, audit, ML versioning)
- No bucket creation requirement (orgs may provide pre-configured buckets)
- Local-first development (MinIO default)

**Out of Scope (for now):**
- Multi-backend simultaneously (pick one per deployment)
- Built-in versioning logic (delegate to S3 bucket config)
- ACLs/permissions (rely on S3 bucket policies)

### 1.3 Use Cases

**1. LLM Context Cache:**
```python
# Store large analysis result
await storage.put_object(
    bucket="uer-context",
    key="analysis/financial-report-2026-q1.json",
    data=json.dumps(analysis_result).encode()
)

# Reference in next LLM call
response = await llm_call(
    model="gemini/gemini-3-flash-preview",
    messages=[{
        "role": "user",
        "content": "Compare with @{expand:s3://uer-context/analysis/financial-report-2026-q1.json}"
    }]
)
```

**2. Claude Skills Storage:**
```python
# Store skill as files
await storage.put_object(bucket="uer-skills", key="financial-analysis/SKILL.md", data=skill_md)
await storage.put_object(bucket="uer-skills", key="financial-analysis/scripts/analyze.py", data=script)

# Retrieve for Claude Skills API
files = await storage.list_objects(bucket="uer-skills", prefix="financial-analysis/")
# → Export to Claude Skills API format
```

**3. Compliance/Audit Logging:**
```python
# Store with WORM retention
await storage.put_object(bucket="uer-audit", key=f"logs/{date}/{request_id}.json", data=log_data)
await storage.set_object_retention(
    bucket="uer-audit",
    key=f"logs/{date}/{request_id}.json",
    retention=Retention(mode=COMPLIANCE, retain_until_date=datetime.now() + timedelta(days=2555))  # 7 years
)
```

---

## 2. Decision

### 2.1 Core Decision

**We will use S3-compatible object storage as the primary storage backend for UER.**

- **Local development:** MinIO (S3-compatible, local, Docker-based)
- **Production:** User-configurable (MinIO, AWS S3, Azure Blob, NetApp, etc.)
- **API:** Full S3 API via `minio-py` Python SDK
- **URIs:** S3-style `s3://bucket-name/prefix/key` or `registry://prefix/key` (aliased to default bucket)

### 2.2 Storage Interface

```python
from typing import Protocol, AsyncIterator
from datetime import datetime
from enum import Enum

class RetentionMode(Enum):
    GOVERNANCE = "GOVERNANCE"  # Can be overridden by privileged users
    COMPLIANCE = "COMPLIANCE"  # Cannot be overridden during retention period

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
    """S3-compatible storage interface."""

    async def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None
    ) -> ObjectMetadata:
        """Store object in S3."""

    async def get_object(self, bucket: str, key: str) -> tuple[bytes, ObjectMetadata]:
        """Retrieve object from S3."""

    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete object from S3."""

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        recursive: bool = True
    ) -> list[ObjectMetadata]:
        """List objects with optional prefix filter."""

    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if object exists."""

    # Optional: WORM/compliance features
    async def set_object_retention(
        self,
        bucket: str,
        key: str,
        retention: Retention
    ) -> None:
        """Set WORM retention on object (MinIO/S3 only)."""

    async def get_object_retention(
        self,
        bucket: str,
        key: str
    ) -> Retention | None:
        """Get retention settings for object."""
```

### 2.3 Template Engine Integration

**Jinja2 for context expansion:**

```python
from jinja2 import Environment, BaseLoader, Template

class S3TemplateLoader(BaseLoader):
    """Load Jinja2 templates from S3 storage."""

    def __init__(self, storage: StorageBackend, bucket: str):
        self.storage = storage
        self.bucket = bucket

    async def get_source(self, template_name: str):
        """Load template from S3."""
        data, metadata = await self.storage.get_object(self.bucket, template_name)
        return data.decode('utf-8'), template_name, lambda: True

class TemplateManager:
    """Manage Jinja2 templates with S3 storage."""

    def __init__(self, storage: StorageBackend, bucket: str = "uer-templates"):
        self.storage = storage
        self.bucket = bucket
        self.env = Environment(loader=S3TemplateLoader(storage, bucket))

        # Custom filters for context expansion
        self.env.filters['expand'] = self._expand_filter
        self.env.filters['s3'] = self._s3_filter

    async def _expand_filter(self, uri: str) -> str:
        """Jinja2 filter: {{ uri | expand }} → content from S3."""
        bucket, key = self._parse_uri(uri)
        data, _ = await self.storage.get_object(bucket, key)
        return data.decode('utf-8')

    async def _s3_filter(self, key: str) -> str:
        """Jinja2 filter: {{ key | s3 }} → content from default bucket."""
        data, _ = await self.storage.get_object(self.bucket, key)
        return data.decode('utf-8')

    async def render(self, template_key: str, context: dict) -> str:
        """Render template with context."""
        template = self.env.get_template(template_key)
        return await template.render_async(**context)
```

**Example usage:**

```jinja2
{# Template stored at s3://uer-templates/meeting-notes.md #}
# Meeting Notes: {{ meeting.title }}

**Date:** {{ meeting.date }}
**Attendees:** {% for attendee in meeting.attendees %}{{ attendee }}{% if not loop.last %}, {% endif %}{% endfor %}

## Context
{{ "context/background.md" | s3 }}

## Previous Action Items
{% for item in previous_items %}
- {{ item.description }} ({{ item.status }})
{% endfor %}

## Discussion
{{ meeting.discussion }}

## Next Steps
{{ "templates/action-items-template.md" | expand }}
```

---

## 3. Architecture

### 3.1 Component Diagram

```mermaid
graph TB
    subgraph uer["UER MCP Server"]
        direction TB

        subgraph tools["MCP Tools"]
            A1["storage_put"]
            A2["storage_get"]
            A3["storage_list"]
            A4["skill_create"]
            A5["skill_get"]
            A6["template_render"]
        end

        subgraph managers["Storage Managers"]
            B1["SkillsManager<br/>Claude Skills API"]
            B2["TemplateManager<br/>Jinja2 Templates"]
            B3["StorageManager<br/>Core S3 Operations"]
        end

        subgraph backends["Storage Backends"]
            C1["MinIOBackend"]
            C2["S3Backend"]
            C3["AzureBlobBackend"]
            C4["NetAppBackend"]
        end
    end

    subgraph external["External Storage"]
        D1["Local MinIO<br/>Docker Container"]
        D2["AWS S3"]
        D3["Azure Blob Storage"]
        D4["NetApp StorageGRID"]
    end

    tools --> managers
    managers --> backends
    C1 --> D1
    C2 --> D2
    C3 --> D3
    C4 --> D4
```

### 3.2 URI Schemes

**S3-native:**
```
s3://bucket-name/prefix/key
s3://uer-context/analysis/report-2026-q1.json
s3://uer-skills/financial-analysis/SKILL.md
s3://uer-templates/meeting-notes.md
```

**Registry alias (convenience):**
```
registry://context/report → s3://uer-context/report
registry://skills/financial-analysis → s3://uer-skills/financial-analysis/
registry://templates/meeting-notes.md → s3://uer-templates/meeting-notes.md
```

**Parsing:**
```python
def parse_uri(uri: str) -> tuple[str, str]:
    """Parse URI into (bucket, key)."""
    if uri.startswith("registry://"):
        # registry://type/key → s3://uer-{type}/key
        path = uri.replace("registry://", "")
        type_name, key = path.split("/", 1)
        return f"uer-{type_name}", key
    elif uri.startswith("s3://"):
        # s3://bucket/key
        path = uri.replace("s3://", "")
        bucket, key = path.split("/", 1)
        return bucket, key
    else:
        raise ValueError(f"Invalid URI: {uri}")
```

### 3.3 Folder Structure (Virtual via Prefixes)

S3 doesn't have true folders, but we use **prefixes** to simulate hierarchy:

```
s3://uer-skills/
├── financial-analysis/
│   ├── SKILL.md
│   ├── scripts/
│   │   └── analyze.py
│   └── examples/
│       └── sample-input.json
│
├── code-review/
│   ├── SKILL.md
│   └── prompts/
│       └── security-checklist.md
│
└── data-pipeline/
    ├── SKILL.md
    └── configs/
        └── pipeline.yaml

s3://uer-context/
├── analysis/
│   ├── financial-report-2026-q1.json
│   └── market-research-summary.md
│
└── code/
    ├── refactor-plan.json
    └── test-results.json

s3://uer-templates/
├── meeting-notes.md
├── action-items.md
└── project-specs/
    └── api-design.md
```

**List by prefix:**
```python
# List all skills
skills = await storage.list_objects(bucket="uer-skills", prefix="", recursive=False)
# Returns: ["financial-analysis/", "code-review/", "data-pipeline/"]

# List skill files
files = await storage.list_objects(bucket="uer-skills", prefix="financial-analysis/", recursive=True)
# Returns: ["financial-analysis/SKILL.md", "financial-analysis/scripts/analyze.py", ...]
```

---

## 4. Implementation Plan

### 4.1 Phase 2a: Core S3 Storage (3 hours)

**Goal:** S3-compatible storage with local MinIO backend

```
□ Storage Backend Interface
  □ Create src/uer/storage/base.py with StorageBackend protocol
  □ Define ObjectMetadata, Retention, RetentionMode models
  □ Document interface with examples

□ MinIO Backend Implementation
  □ Create src/uer/storage/minio_backend.py
  □ Initialize MinIO client from environment (endpoint, access/secret keys)
  □ Implement put_object, get_object, delete_object, list_objects
  □ Implement object_exists helper
  □ Add connection pooling and error handling

□ Storage Manager
  □ Create src/uer/storage/manager.py
  □ Auto-create default buckets (uer-context, uer-skills, uer-templates)
  □ URI parsing (registry:// → s3://)
  □ Convenience methods wrapping backend

□ Environment Configuration
  □ Add MinIO config to .env.example
    - MINIO_ENDPOINT=localhost:9000
    - MINIO_ACCESS_KEY=minioadmin
    - MINIO_SECRET_KEY=minioadmin
    - MINIO_SECURE=false
  □ Add MinIO Docker Compose file
  □ Document MinIO setup in README

□ Testing
  □ Test MinIO connection
  □ Test CRUD operations
  □ Test prefix filtering
  □ Test error handling (bucket not found, object not found)
```

### 4.2 Phase 2b: Skills & Templates (2 hours)

**Goal:** Claude Skills API compliance + Jinja2 templates

```
□ Skills Manager
  □ Create src/uer/storage/skills.py
  □ skill_create(name, display_title, files) → SkillMetadata
  □ skill_get(name) → Skill (all files)
  □ skill_list() → list of skills
  □ skill_export_for_api(name) → Claude Skills API format
  □ Validate SKILL.md exists in files

□ Template Manager
  □ Create src/uer/storage/templates.py
  □ S3TemplateLoader for Jinja2
  □ Custom filters: expand, s3
  □ render(template_key, context) → rendered content
  □ Support async template rendering

□ Testing
  □ Create test skill (SKILL.md + Python script)
  □ Store and retrieve skill
  □ Render template with context
  □ Test expand filter loading from S3
```

### 4.3 Phase 2c: MCP Tools (2 hours)

**Goal:** Expose storage to LLMs via MCP tools

```
□ Storage Tools
  □ Create src/uer/tools/storage_tools.py
  □ storage_put(uri, content, content_type, metadata) → ObjectMetadata
  □ storage_get(uri) → content + metadata
  □ storage_list(prefix, recursive) → list of objects
  □ storage_delete(uri) → success

□ Skills Tools
  □ skill_create(name, display_title, skill_md, files) → SkillMetadata
  □ skill_get(name) → Skill with all files
  □ skill_list() → list of available skills
  □ skill_export(name) → Claude Skills API format

□ Template Tools
  □ template_render(template_uri, context) → rendered content
  □ template_list() → available templates

□ Register in Server
  □ Add all tools to src/uer/server.py
  □ Update tool schemas with examples
  □ Add comprehensive error handling

□ Testing
  □ Test with Claude Desktop
  □ Store/retrieve context via MCP
  □ Create skill via MCP
  □ Render template via MCP
```

### 4.4 Phase 2d: Advanced Features (Optional, 2 hours)

**Goal:** WORM compliance, versioning, multi-backend

```
□ WORM/Compliance Support
  □ Add set_object_retention to MinIO backend
  □ Add get_object_retention
  □ Create retention_set tool (restricted, admin only)
  □ Document compliance use cases

□ Versioning Support
  □ Document how to enable versioning in MinIO bucket config
  □ Add version_id to ObjectMetadata
  □ Add get_object_version method
  □ list_object_versions method

□ Multi-Backend Support (Future)
  □ Create src/uer/storage/s3_backend.py (AWS S3)
  □ Create src/uer/storage/azure_backend.py (Azure Blob)
  □ Add backend selection via env var (STORAGE_BACKEND=minio|s3|azure)
  □ Document configuration for each backend
```

---

## 5. Skills API Compliance

### 5.1 Skills Format

**Claude Skills structure:**
```
skill-name/
├── SKILL.md           # Required: YAML frontmatter + instructions
├── scripts/           # Optional: Python/JS scripts
├── templates/         # Optional: Templates
└── examples/          # Optional: Example inputs/outputs
```

**SKILL.md format:**
```markdown
---
name: financial-analysis
description: Analyze financial reports and generate insights
---

# Financial Analysis Skill

This skill analyzes financial reports using Python pandas and generates insights.

## Usage

Call the `analyze_report` function with a CSV file containing financial data.

## Tools

- `analyze_report(file_path)` - Main analysis function
- `generate_visualizations(data)` - Create charts
```

### 5.2 Storage Mapping

**Store skill in S3:**
```python
await skills_manager.create_skill(
    name="financial-analysis",
    display_title="Financial Analysis",
    files={
        "SKILL.md": skill_md_content.encode(),
        "scripts/analyze.py": analyze_script.encode(),
        "examples/sample.csv": sample_data.encode()
    }
)

# Stored as:
# s3://uer-skills/financial-analysis/SKILL.md
# s3://uer-skills/financial-analysis/scripts/analyze.py
# s3://uer-skills/financial-analysis/examples/sample.csv
```

### 5.3 Claude Skills API Export

**Export for Claude Skills API:**
```python
class SkillsManager:
    async def export_for_api(self, name: str) -> dict:
        """Format skill for Claude Skills API POST /v1/skills."""
        files = await self.storage.list_objects(
            bucket="uer-skills",
            prefix=f"{name}/",
            recursive=True
        )

        # Download all files
        skill_files = []
        for file_meta in files:
            data, _ = await self.storage.get_object("uer-skills", file_meta.key)
            skill_files.append({
                "filename": file_meta.key.replace(f"{name}/", ""),
                "content": data
            })

        return {
            "display_title": await self._get_display_title(name),
            "files": skill_files
        }

# Usage with Claude Skills API
skill_export = await skills_manager.export_for_api("financial-analysis")

# POST to Claude Skills API
import anthropic
client = anthropic.Anthropic()
skill = client.beta.skills.create(
    display_title=skill_export["display_title"],
    files=skill_export["files"],
    betas=["skills-2025-10-02"]
)
```

### 5.4 LLM-Agnostic Usage (GPT, Gemini)

**For non-Claude LLMs, convert skill to system prompt:**

```python
class SkillsManager:
    async def to_system_prompt(self, name: str) -> str:
        """Convert skill to system prompt for non-Claude LLMs."""
        skill_md, _ = await self.storage.get_object(
            bucket="uer-skills",
            key=f"{name}/SKILL.md"
        )

        # Parse SKILL.md
        content = skill_md.decode('utf-8')
        yaml_frontmatter, instructions = self._parse_skill_md(content)

        # Load referenced scripts/files
        scripts = await self._load_skill_scripts(name)

        # Build system prompt
        prompt = f"""# Skill: {yaml_frontmatter['name']}

{instructions}

## Available Functions

{scripts}

You are now using the {yaml_frontmatter['name']} skill.
"""
        return prompt

# Usage with GPT/Gemini
system_prompt = await skills_manager.to_system_prompt("financial-analysis")
response = await llm_call(
    model="openai/gpt-5.2",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Analyze this financial report..."}
    ]
)
```

---

## 6. Storage Backends

### 6.1 MinIO (Default, Local Development)

**Setup:**
```yaml
# docker-compose.yml
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

**Configuration:**
```bash
# .env
STORAGE_BACKEND=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
```

**Python client:**
```python
from minio import Minio
from minio.error import S3Error

class MinIOBackend:
    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )

    async def put_object(self, bucket: str, key: str, data: bytes, **kwargs):
        """Upload object to MinIO."""
        self.client.put_object(
            bucket_name=bucket,
            object_name=key,
            data=io.BytesIO(data),
            length=len(data),
            content_type=kwargs.get("content_type", "application/octet-stream"),
            metadata=kwargs.get("metadata")
        )
```

### 6.2 AWS S3 (Production)

**Configuration:**
```bash
# .env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET_PREFIX=uer  # Creates uer-context, uer-skills, uer-templates
```

**Python client:**
```python
import boto3

class S3Backend:
    def __init__(self):
        self.client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

    async def put_object(self, bucket: str, key: str, data: bytes, **kwargs):
        """Upload object to AWS S3."""
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=kwargs.get("content_type", "application/octet-stream"),
            Metadata=kwargs.get("metadata", {})
        )
```

### 6.3 Azure Blob Storage (Future)

**Configuration:**
```bash
# .env
STORAGE_BACKEND=azure
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

### 6.4 NetApp StorageGRID (Enterprise)

**Configuration:**
```bash
# .env
STORAGE_BACKEND=netapp
NETAPP_ENDPOINT=storagegrid.company.com
NETAPP_ACCESS_KEY=...
NETAPP_SECRET_KEY=...
```

**Same interface as MinIO (S3-compatible).**

---

## 7. Security & Compliance

### 7.1 WORM (Write-Once-Read-Many)

**Use cases:**
- Legal document retention (7+ years)
- Audit logs (immutable history)
- ML training data versioning (reproducibility)

**Configuration:**
```python
from datetime import datetime, timedelta
from minio.commonconfig import COMPLIANCE, GOVERNANCE
from minio.retention import Retention

# Create bucket with object locking
client.make_bucket("uer-audit", object_lock=True)

# Set retention on object
retention = Retention(
    mode=COMPLIANCE,  # Cannot be overridden
    retain_until_date=datetime.utcnow() + timedelta(days=2555)  # 7 years
)
client.set_object_retention("uer-audit", "logs/2026-01-10/request-123.json", retention)
```

**MCP tool:**
```python
@tool
async def storage_set_retention(
    uri: str,
    mode: Literal["GOVERNANCE", "COMPLIANCE"],
    retain_days: int
) -> dict:
    """
    Set WORM retention on object (MinIO/S3 only).

    GOVERNANCE: Can be overridden by privileged users
    COMPLIANCE: Cannot be overridden during retention period

    Requires: Bucket created with object_lock=True
    """
```

### 7.2 Versioning

**Bucket-level configuration (not our responsibility):**

```bash
# Enable versioning on MinIO bucket
mc version enable minio/uer-context

# Enable versioning on S3 bucket
aws s3api put-bucket-versioning --bucket uer-context --versioning-configuration Status=Enabled
```

**Retrieve specific version:**
```python
# Latest version (default)
data, meta = await storage.get_object("uer-context", "report.json")

# Specific version
data, meta = await storage.get_object("uer-context", "report.json", version_id="abc123")

# List all versions
versions = await storage.list_object_versions("uer-context", "report.json")
```

### 7.3 Access Control

**Rely on S3 bucket policies (not implemented in UER):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::123456789012:user/uer-app"},
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::uer-context/*"
    },
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::uer-audit/*"
    }
  ]
}
```

### 7.4 Encryption

**Server-side encryption (SSE-S3):**
```python
# MinIO
client.put_object(
    bucket_name="uer-context",
    object_name="sensitive-data.json",
    data=io.BytesIO(data),
    length=len(data),
    sse=S3EncryptionOptions.SSE_S3()
)

# AWS S3
s3_client.put_object(
    Bucket="uer-context",
    Key="sensitive-data.json",
    Body=data,
    ServerSideEncryption="AES256"
)
```

---

## 8. Migration Path

### 8.1 From Current System (None)

No migration needed - Phase 2 not yet implemented.

### 8.2 Future: Multi-Backend Support

**Abstraction layer allows switching backends:**

```python
# Current: Local MinIO
STORAGE_BACKEND=minio

# Future: AWS S3
STORAGE_BACKEND=s3

# Future: Azure Blob
STORAGE_BACKEND=azure
```

**Same code, different backend:**
```python
# Application code doesn't change
storage = get_storage_backend()  # Factory returns correct backend
await storage.put_object("uer-context", "key", data)
```

### 8.3 Team Collaboration (Multi-User)

**Shared S3 bucket:**
```bash
# Team A and Team B both configure same S3 bucket
STORAGE_BACKEND=s3
S3_BUCKET_PREFIX=team-shared

# Both can read/write to:
# s3://team-shared-context/
# s3://team-shared-skills/
# s3://team-shared-templates/
```

**Namespace isolation (if needed):**
```bash
# Team A
S3_NAMESPACE=team-a
# Creates: s3://uer-context/team-a/*, s3://uer-skills/team-a/*

# Team B
S3_NAMESPACE=team-b
# Creates: s3://uer-context/team-b/*, s3://uer-skills/team-b/*
```

---

## 9. Consequences

### 9.1 Positive

✅ **Enterprise-ready:** S3 compatibility enables NetApp, AWS, Azure integration
✅ **Infinitely scalable:** No local disk limits, pay-as-you-grow
✅ **Skills-compatible:** Natural file storage for Claude Skills API
✅ **Compliance-ready:** WORM/versioning for legal, audit, ML use cases
✅ **Team collaboration:** Shared storage for multi-user workflows
✅ **LLM-agnostic:** Works with Claude, GPT, Gemini via templates
✅ **Future-proof:** Easy to add new backends (Azure, GCP, etc.)

### 9.2 Negative

⚠️ **Complexity:** More complex than SQLite (requires MinIO for local dev)
⚠️ **Dependencies:** Requires MinIO Docker container for local development
⚠️ **Learning curve:** Developers need to understand S3 concepts (buckets, prefixes)
⚠️ **Testing overhead:** Need to mock S3 API in unit tests

### 9.3 Mitigation

**For complexity:**
- Provide Docker Compose file for one-command MinIO setup
- Abstract storage interface hides S3 details from application code
- Comprehensive documentation with examples

**For dependencies:**
- MinIO is lightweight (single Docker container, ~50MB)
- Falls back gracefully if MinIO not available (error message with setup instructions)

**For learning curve:**
- Document common patterns (store, retrieve, list)
- Provide helper functions (parse_uri, create_default_buckets)
- Examples in README and ADR

**For testing:**
- Use `minio-py` mock or in-memory S3 simulator
- Provide test fixtures with sample data

### 9.4 Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MinIO setup fails | Medium | High | Provide troubleshooting guide, fallback to error with clear instructions |
| S3 API incompatibility | Low | Medium | Use well-tested `minio-py` and `boto3` SDKs |
| Performance issues | Low | Medium | Use connection pooling, async I/O, caching |
| Cost (cloud storage) | Medium | Low | Default to local MinIO, document cost-optimized bucket policies |

---

## 10. References

### 10.1 External Documentation

- **MinIO Object Locking:** https://min.io/docs/minio/linux/administration/object-management/object-retention.html
- **MinIO Python SDK:** https://github.com/minio/minio-py
- **Claude Skills API:** https://platform.claude.com/docs/en/api/beta/skills/create
- **Jinja2 Templates:** https://jinja.palletsprojects.com/
- **AWS S3 API:** https://docs.aws.amazon.com/s3/

### 10.2 Internal References

- **ADR.plan.md:** Original architecture decision record
- **CLAUDE.md:** Project coding standards and reference
- **TODO.md:** Implementation checklist (Phase 2 updated)

### 10.3 Research Sources

From earlier research:
- [MinIO Retention Policies (Python)](https://deepwiki.com/minio/minio-py/6.4-retention-policies)
- [MinIO Object Locking Guide](https://blog.min.io/object-locking-versioning-and-holds-in-minio/)
- [Using Agent Skills with API - Claude Docs](https://platform.claude.com/docs/en/build-with-claude/skills-guide)

---

## Appendix A: Code Examples

### A.1 Complete MinIO Backend

```python
# src/uer/storage/minio_backend.py
import io
import os
from datetime import datetime
from typing import Optional

from minio import Minio
from minio.error import S3Error
from minio.commonconfig import GOVERNANCE, COMPLIANCE
from minio.retention import Retention as MinioRetention

from .base import StorageBackend, ObjectMetadata, Retention, RetentionMode

class MinIOBackend(StorageBackend):
    """MinIO S3-compatible storage backend."""

    def __init__(self):
        """Initialize MinIO client from environment."""
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        """Create default buckets if they don't exist."""
        for bucket in ["uer-context", "uer-skills", "uer-templates"]:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    async def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None
    ) -> ObjectMetadata:
        """Store object in MinIO."""
        result = self.client.put_object(
            bucket_name=bucket,
            object_name=key,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
            metadata=metadata or {}
        )

        return ObjectMetadata(
            bucket=bucket,
            key=key,
            size=len(data),
            content_type=content_type,
            last_modified=datetime.utcnow(),
            etag=result.etag,
            version_id=result.version_id,
            metadata=metadata or {}
        )

    async def get_object(self, bucket: str, key: str) -> tuple[bytes, ObjectMetadata]:
        """Retrieve object from MinIO."""
        try:
            response = self.client.get_object(bucket, key)
            data = response.read()

            stat = self.client.stat_object(bucket, key)
            metadata = ObjectMetadata(
                bucket=bucket,
                key=key,
                size=stat.size,
                content_type=stat.content_type,
                last_modified=stat.last_modified,
                etag=stat.etag,
                version_id=stat.version_id,
                metadata=stat.metadata or {}
            )

            return data, metadata
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"Object not found: s3://{bucket}/{key}")
            raise

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        recursive: bool = True
    ) -> list[ObjectMetadata]:
        """List objects with prefix."""
        objects = []
        for obj in self.client.list_objects(bucket, prefix=prefix, recursive=recursive):
            objects.append(ObjectMetadata(
                bucket=bucket,
                key=obj.object_name,
                size=obj.size,
                content_type="",
                last_modified=obj.last_modified,
                etag=obj.etag,
                version_id=obj.version_id,
                metadata={}
            ))
        return objects

    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete object."""
        try:
            self.client.remove_object(bucket, key)
            return True
        except S3Error:
            return False

    async def set_object_retention(
        self,
        bucket: str,
        key: str,
        retention: Retention
    ) -> None:
        """Set WORM retention on object."""
        mode = COMPLIANCE if retention.mode == RetentionMode.COMPLIANCE else GOVERNANCE
        minio_retention = MinioRetention(mode, retention.retain_until_date)
        self.client.set_object_retention(bucket, key, minio_retention)
```

### A.2 Skills Manager Example

```python
# src/uer/storage/skills.py
from typing import Dict
from .manager import StorageManager

class SkillsManager:
    """Manage Claude Skills in S3 storage."""

    def __init__(self, storage: StorageManager):
        self.storage = storage
        self.bucket = "uer-skills"

    async def create_skill(
        self,
        name: str,
        display_title: str,
        files: Dict[str, bytes]
    ) -> dict:
        """
        Create skill in storage.

        Args:
            name: Skill identifier (slug)
            display_title: Human-readable title
            files: {"SKILL.md": content, "scripts/analyze.py": content, ...}

        Returns:
            Skill metadata
        """
        # Validate SKILL.md exists
        if "SKILL.md" not in files:
            raise ValueError("SKILL.md is required")

        # Store all files under skill prefix
        for filename, content in files.items():
            key = f"{name}/{filename}"
            await self.storage.backend.put_object(
                bucket=self.bucket,
                key=key,
                data=content,
                content_type=self._get_content_type(filename)
            )

        # Store metadata
        metadata = {
            "name": name,
            "display_title": display_title,
            "created_at": datetime.utcnow().isoformat(),
            "file_count": len(files)
        }

        await self.storage.backend.put_object(
            bucket=self.bucket,
            key=f"{name}/.metadata.json",
            data=json.dumps(metadata).encode(),
            content_type="application/json"
        )

        return metadata

    async def get_skill(self, name: str) -> dict:
        """Retrieve complete skill with all files."""
        files_meta = await self.storage.backend.list_objects(
            bucket=self.bucket,
            prefix=f"{name}/",
            recursive=True
        )

        files = {}
        for file_meta in files_meta:
            if file_meta.key.endswith(".metadata.json"):
                continue

            data, _ = await self.storage.backend.get_object(
                bucket=self.bucket,
                key=file_meta.key
            )

            filename = file_meta.key.replace(f"{name}/", "")
            files[filename] = data.decode('utf-8')

        return {
            "name": name,
            "files": files
        }

    def _get_content_type(self, filename: str) -> str:
        """Infer content type from filename."""
        if filename.endswith(".md"):
            return "text/markdown"
        elif filename.endswith(".py"):
            return "text/x-python"
        elif filename.endswith(".json"):
            return "application/json"
        else:
            return "application/octet-stream"
```

---

**Last Updated:** 2026-01-10
**Next Review:** After Phase 2 implementation
