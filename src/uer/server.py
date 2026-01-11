"""UER MCP Server - Universal Expert Registry."""

import asyncio
import json
import logging
from collections.abc import Sequence
from datetime import UTC
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from uer.llm.gateway import LLMGateway
from uer.mcp.config import MCPConfig
from uer.mcp.manager import MCPManager
from uer.models.llm import LLMCallRequest
from uer.security import ContentValidator
from uer.storage import StorageManager
from uer.tools import (
    behavior_tools,
    sandbagging_tools,
    skills_tools,
    storage_tools,
    template_tools,
)
from uer.tools.delegate import DelegateToolHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("uer.server")

# Initialize MCP server
app = Server("uer")
gateway = LLMGateway()

# Load MCP config from environment or use default
mcp_config = MCPConfig.from_env() or MCPConfig.default()
mcp_manager = MCPManager(mcp_config)

# Initialize S3-compatible storage (optional)
storage_manager = StorageManager()
if storage_manager.is_available():
    storage_tools.init_storage(storage_manager)
    behavior_tools.init_behavior_tools(storage_manager)
    # Initialize skills and templates managers with storage manager
    # Backend will be created lazily on first actual use
    skills_tools.init_skills_manager(storage_manager)
    template_tools.init_templates_manager(storage_manager)
    logger.info("Storage backend enabled with behavior monitoring, skills, and templates")
else:
    logger.info(
        "Storage backend disabled - storage/skills/template/behavior tools will not be available"
    )

# Initialize sandbagging detection tools
sandbagging_tools.init_sandbagging_tools(gateway)

# Initialize delegate tool handler for multi-agent orchestration
delegate_handler = DelegateToolHandler(gateway=gateway, storage=storage_manager)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    available = gateway.get_available_providers()

    mcp_servers = mcp_manager.list_servers()

    tools = [
        Tool(
            name="llm_call",
            description=(
                "Call any LLM via LiteLLM unified interface. "
                f"Available providers: {', '.join(available) or 'none'}. "
                "Supports Anthropic (Claude), OpenAI (GPT), Google (Gemini), and 100+ more. "
                "Features: Structured output (response_format), Chain of Thought (thinking_level/thinking_budget), "
                "Tool use (tools) for web search, code execution, grounding, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "LiteLLM model identifier (e.g., 'gemini/gemini-3-flash-preview')",
                    },
                    "messages": {
                        "type": "array",
                        "description": "List of chat messages",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "enum": ["system", "user", "assistant"],
                                },
                                "content": {"type": "string"},
                            },
                            "required": ["role", "content"],
                        },
                        "minItems": 1,
                    },
                    "temperature": {
                        "type": "number",
                        "default": 0.7,
                        "minimum": 0,
                        "maximum": 2,
                    },
                    "max_tokens": {
                        "type": "integer",
                        "default": 4096,
                        "minimum": 1,
                    },
                    "response_format": {
                        "type": "object",
                        "description": (
                            "Force structured JSON output. The calling LLM can generate schemas dynamically. "
                            "Format: {'type': 'json_schema', 'json_schema': {'name': '...', 'schema': {...}, 'strict': True}}"
                        ),
                    },
                    "thinking_level": {
                        "type": "string",
                        "enum": ["minimal", "low", "medium", "high"],
                        "description": "Gemini 3 reasoning level: 'high' for complex reasoning tasks, 'low' for simple ones",
                    },
                    "thinking_budget": {
                        "type": "integer",
                        "minimum": -1,
                        "maximum": 32768,
                        "description": "Gemini 2.5 thinking tokens (128-32768, or -1 for dynamic allocation)",
                    },
                    "tools": {
                        "type": "array",
                        "description": (
                            "List of tools the model can use. "
                            "Claude: [{'type': 'web_search_20250305'}] for web search, [{'type': 'bash_20250305'}] for code execution. "
                            "Gemini: [{'type': 'code_execution'}] or [{'type': 'google_search_retrieval'}]. "
                            "OpenAI: Standard function calling format."
                        ),
                        "items": {"type": "object"},
                    },
                },
                "required": ["model", "messages"],
            },
        ),
        Tool(
            name="llm_list_models",
            description=(
                "List available LLM providers and models. "
                "For LOCAL servers (LM Studio, Ollama): queries /v1/models endpoint to show actual deployed models. "
                "For CLOUD providers (Cerebras, Anthropic, OpenAI, etc.): shows popular example models. "
                "Response includes 'type' field ('local' or 'cloud') and 'source' field ('live_query' or 'examples'). "
                "Local servers also include 'server_url' showing the endpoint. "
                "Use this to discover what models you can call via llm_call."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="llm_config_get",
            description=(
                "Get LLM provider configuration from registry. "
                "Returns all configured providers with their credentials, instances, and metadata. "
                "Use this to see what providers are configured and their settings. "
                "Helps non-technical users by showing current setup without needing to check environment variables."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Optional: specific provider name to get config for. Omit to get all providers.",
                    },
                },
            },
        ),
        Tool(
            name="llm_config_set",
            description=(
                "Set or update LLM provider configuration in registry. "
                "Allows LLMs to help users configure providers without manual environment variable editing. "
                "Can set API keys, endpoints, and provider-specific settings. "
                "For cloud providers (AWS, Azure), can configure user's specific instances/deployments. "
                "Changes are persisted to ~/.uer/provider_config.json."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name (e.g., 'openai', 'azure', 'bedrock')",
                    },
                    "config": {
                        "type": "object",
                        "description": "Provider configuration (credentials, settings, etc.)",
                    },
                    "merge": {
                        "type": "boolean",
                        "description": "If true, merge with existing config. If false, replace. Default: true",
                        "default": True,
                    },
                },
                "required": ["provider", "config"],
            },
        ),
        Tool(
            name="llm_config_add_instance",
            description=(
                "Add a provider instance (e.g., Azure deployment, AWS endpoint). "
                "For cloud providers where users have their own deployed instances. "
                "Examples: Azure OpenAI deployments, AWS Bedrock endpoints, custom OpenAI-compatible servers. "
                "Each instance can have its own endpoint, model mappings, and settings."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name (e.g., 'azure', 'bedrock', 'openai')",
                    },
                    "instance": {
                        "type": "object",
                        "description": "Instance configuration (name, endpoint, models, etc.)",
                    },
                },
                "required": ["provider", "instance"],
            },
        ),
        Tool(
            name="llm_config_guide",
            description=(
                "Get configuration guide for LLM providers using environment variables. "
                "⚠️ BEST PRACTICE: Use this tool instead of asking users to share API keys in chat. "
                "This tool detects the user's MCP client and provides instructions for "
                "setting environment variables in the client config file. "
                "This approach is more convenient and follows security best practices. "
                "Note: Users are responsible for managing their data sharing preferences with LLM providers."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name to get configuration guide for (e.g., 'openai', 'anthropic')",
                    },
                },
                "required": ["provider"],
            },
        ),
        Tool(
            name="mcp_call",
            description=(
                "Call tools from external MCP servers. "
                f"Available servers: {', '.join(mcp_servers) or 'none'}. "
                "Use mcp_list_tools to discover available tools on each server first."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "description": f"MCP server name. Available: {', '.join(mcp_servers)}",
                    },
                    "tool": {
                        "type": "string",
                        "description": "Tool name to call on the MCP server",
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Arguments to pass to the tool",
                        "default": {},
                    },
                },
                "required": ["server", "tool"],
            },
        ),
        Tool(
            name="mcp_list_tools",
            description=(
                "List available MCP servers and their tools. "
                "Omit 'server' to list all configured servers. "
                "Provide 'server' name to list tools from that specific server. "
                "Use 'prefix' to filter servers by name prefix (e.g., 'hug' matches 'huggingface')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "description": "MCP server name (optional - omit to list all servers)",
                    },
                    "prefix": {
                        "type": "string",
                        "description": "Filter servers by name prefix (optional)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="mcp_registry",
            description=(
                "Browse and install MCP servers from the official registry (registry.modelcontextprotocol.io). "
                "Use 'search' to find servers by keyword, 'get' to view server details, "
                "'install' to add a server from the registry. "
                "Registry has 300+ servers including Slack, GitHub, Salesforce, AWS, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["search", "get", "install", "list"],
                        "description": "Operation: search (find servers), get (view details), install (add to config), list (browse all)",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for 'search' operation (e.g., 'slack', 'database', 'github')",
                    },
                    "server_id": {
                        "type": "string",
                        "description": "Server ID for 'get' or 'install' operations (e.g., 'io.github.modelcontextprotocol.server-slack')",
                    },
                    "config_overrides": {
                        "type": "object",
                        "description": "Optional config overrides for 'install' (e.g., env vars, custom args)",
                        "properties": {
                            "env": {"type": "object"},
                            "args": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "required": ["operation"],
            },
        ),
        Tool(
            name="mcp_servers",
            description=(
                "Manage MCP server configurations (CRUD operations). "
                "Use 'list' to see configured servers, 'get' to view one server, "
                "'add' to manually create servers, 'update' to modify existing ones, "
                "'delete' to remove servers. "
                "For installing from registry, use mcp_registry tool instead. "
                "For OAuth-based servers (like Hugging Face), use headers={'Authorization': 'Bearer <token>'}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["list", "get", "add", "update", "delete"],
                        "description": "CRUD operation to perform",
                    },
                    "servers": {
                        "type": "object",
                        "description": (
                            "Map of server configurations for 'add' or 'update' operations. "
                            "Each key is the server name, value is the config. "
                            "For stdio: {'command': 'npx', 'args': [...], 'transport': 'stdio'}. "
                            "For SSE/HTTP: {'url': 'https://example.com/mcp', 'transport': 'sse', 'headers': {'Authorization': 'Bearer token'}}"
                        ),
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "Command for stdio transport",
                                },
                                "args": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Args for stdio",
                                },
                                "env": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                },
                                "transport": {
                                    "type": "string",
                                    "enum": ["stdio", "sse", "http"],
                                    "default": "stdio",
                                },
                                "url": {
                                    "type": "string",
                                    "description": "Endpoint URL for sse/http transport",
                                },
                                "headers": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                    "description": "HTTP headers for sse/http (e.g., Authorization)",
                                },
                            },
                        },
                    },
                    "server_name": {
                        "type": "string",
                        "description": "Server name for 'get' or 'delete' operations",
                    },
                },
                "required": ["operation"],
            },
        ),
        # Delegate tool for multi-agent orchestration
        delegate_handler.get_tool_definition(),
    ]

    # Conditionally add storage-dependent tools
    if storage_manager.is_available():
        tools.extend(
            [
                # Storage tools
                storage_tools.get_storage_put_tool(),
                storage_tools.get_storage_get_tool(),
                storage_tools.get_storage_list_tool(),
                storage_tools.get_storage_delete_tool(),
                storage_tools.get_storage_exists_tool(),
                # Skills tools
                skills_tools.get_skill_create_tool(),
                skills_tools.get_skill_get_tool(),
                skills_tools.get_skill_list_tool(),
                skills_tools.get_skill_export_tool(),
                skills_tools.get_skill_to_prompt_tool(),
                # Template tools
                template_tools.get_template_render_tool(),
                template_tools.get_template_list_tool(),
                template_tools.get_template_create_tool(),
                template_tools.get_template_delete_tool(),
                # Behavior monitoring tools
                behavior_tools.get_behavior_get_logs_tool(),
                behavior_tools.get_behavior_get_metrics_tool(),
                behavior_tools.get_behavior_analyze_agent_tool(),
                behavior_tools.get_behavior_generate_report_tool(),
                behavior_tools.get_behavior_compare_agents_tool(),
            ]
        )

    # Sandbagging detection tools (always available with LLM gateway)
    tools.extend(
        [
            sandbagging_tools.get_sandbagging_evaluate_tool(),
            sandbagging_tools.get_sandbagging_quick_test_tool(),
        ]
    )

    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool invocation."""
    # LLM and MCP tools
    if name == "llm_call":
        return await handle_llm_call(arguments)
    elif name == "llm_list_models":
        return await handle_llm_list_models(arguments)
    elif name == "llm_config_get":
        return await handle_llm_config_get(arguments)
    elif name == "llm_config_set":
        return await handle_llm_config_set(arguments)
    elif name == "llm_config_add_instance":
        return await handle_llm_config_add_instance(arguments)
    elif name == "llm_config_guide":
        return await handle_llm_config_guide(arguments)
    elif name == "mcp_call":
        return await handle_mcp_call(arguments)
    elif name == "mcp_list_tools":
        return await handle_mcp_list_tools(arguments)
    elif name == "mcp_registry":
        return await handle_mcp_registry(arguments)
    elif name == "mcp_servers":
        return await handle_mcp_servers(arguments)
    # Delegate tool for multi-agent orchestration
    elif name == "delegate":
        return await delegate_handler.handle(arguments)
    # Storage tools
    elif name == "storage_put":
        return await storage_tools.storage_put(arguments)
    elif name == "storage_get":
        return await storage_tools.storage_get(arguments)
    elif name == "storage_list":
        return await storage_tools.storage_list(arguments)
    elif name == "storage_delete":
        return await storage_tools.storage_delete(arguments)
    elif name == "storage_exists":
        return await storage_tools.storage_exists(arguments)
    # Skills tools
    elif name == "skill_create":
        return await skills_tools.skill_create(arguments)
    elif name == "skill_get":
        return await skills_tools.skill_get(arguments)
    elif name == "skill_list":
        return await skills_tools.skill_list(arguments)
    elif name == "skill_export":
        return await skills_tools.skill_export(arguments)
    elif name == "skill_to_prompt":
        return await skills_tools.skill_to_prompt(arguments)
    # Template tools
    elif name == "template_render":
        return await template_tools.template_render(arguments)
    elif name == "template_list":
        return await template_tools.template_list(arguments)
    elif name == "template_create":
        return await template_tools.template_create(arguments)
    elif name == "template_delete":
        return await template_tools.template_delete(arguments)
    # Behavior monitoring tools
    elif name == "behavior_get_logs":
        return await behavior_tools.behavior_get_logs(arguments)
    elif name == "behavior_get_metrics":
        return await behavior_tools.behavior_get_metrics(arguments)
    elif name == "behavior_analyze_agent":
        return await behavior_tools.behavior_analyze_agent(arguments)
    elif name == "behavior_generate_report":
        return await behavior_tools.behavior_generate_report(arguments)
    elif name == "behavior_compare_agents":
        return await behavior_tools.behavior_compare_agents(arguments)
    # Sandbagging detection tools
    elif name == "sandbagging_evaluate":
        return await sandbagging_tools.sandbagging_evaluate(arguments)
    elif name == "sandbagging_quick_test":
        return await sandbagging_tools.sandbagging_quick_test(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_llm_call(arguments: Any) -> Sequence[TextContent]:
    """Handle llm_call tool invocation."""
    try:
        # Validate input using Pydantic
        request = LLMCallRequest(**arguments)

        logger.info(
            f"Calling LLM: model={request.model}, messages={len(request.messages)}, "
            f"structured_output={request.response_format is not None}, "
            f"thinking={request.thinking_level or request.thinking_budget}, "
            f"tools={len(request.tools) if request.tools else 0}"
        )

        # Call LLM via gateway with all parameters
        response = await gateway.call(
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
            thinking_level=request.thinking_level,
            thinking_budget=request.thinking_budget,
            tools=request.tools,
        )

        # Log result
        usage = response.get("usage", {})
        logger.info(
            f"LLM call successful: tokens={usage.get('total_tokens', 'unknown')}, "
            f"model={response.get('model', 'unknown')}"
        )

        # Return response as text content
        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except ValueError as e:
        # Validation error from Pydantic
        logger.error(f"Invalid input: {str(e)}")
        return [
            TextContent(type="text", text=json.dumps({"error": "Invalid input", "message": str(e)}))
        ]

    except RuntimeError as e:
        # Error from LLMGateway
        logger.error(f"LLM call failed: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "LLM call failed", "message": str(e)})
            )
        ]

    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Internal error", "message": str(e)})
            )
        ]


async def handle_llm_list_models(arguments: Any) -> Sequence[TextContent]:
    """Handle llm_list_models tool invocation."""
    try:
        from datetime import datetime

        # Get provider information from gateway (queries live models for local servers)
        provider_info = await gateway.get_provider_info()

        current_time = datetime.now(UTC).isoformat()

        # Format response with timestamps for freshness assessment
        result = {
            "current_time": current_time,
            "queried_at": current_time,
            "important_note_for_llms": (
                "Your knowledge cutoff may be older than this data. "
                "Compare current_time with your training data cutoff to assess freshness. "
                "For providers with source='live_query', this is real-time data from APIs. "
                "For source='examples', this is cached fallback data (see generated_at in examples). "
                "Use these exact model names - do not assume models based on your training data."
            ),
            "providers": provider_info,
            "total_providers": len(provider_info),
            "usage_instructions": {
                "format": "provider/model-name",
                "example": "openai/o3-mini or openai/gpt-4o",
                "verification": "Use check_model_exists tool to verify a model before using it",
                "local_vs_cloud": "Local servers (type=local) show actual deployed models from live query. Cloud providers (type=cloud) may show live query or cached examples - check 'source' field.",
            },
        }

        logger.info(f"Listed {len(provider_info)} available providers")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.exception(f"Error listing models: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Failed to list models", "message": str(e)})
            )
        ]


async def handle_llm_config_get(arguments: Any) -> Sequence[TextContent]:
    """Handle llm_config_get tool invocation."""
    try:
        provider = arguments.get("provider") if arguments else None

        if provider:
            # Get specific provider config
            config = gateway.config_registry.get_provider(provider)
            if config:
                result = {
                    "provider": provider,
                    "config": config,
                }
            else:
                result = {
                    "provider": provider,
                    "config": None,
                    "message": f"No configuration found for provider '{provider}'",
                }
        else:
            # Get all providers
            result = gateway.config_registry.get_all_providers()

        logger.info(f"Retrieved config for provider: {provider or 'all'}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.exception(f"Error getting config: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Failed to get config", "message": str(e)})
            )
        ]


async def handle_llm_config_set(arguments: Any) -> Sequence[TextContent]:
    """Handle llm_config_set tool invocation."""
    try:
        provider = arguments.get("provider")
        config = arguments.get("config")
        merge = arguments.get("merge", True)

        if not provider:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": "Missing required parameter: provider"})
                )
            ]

        if not config:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": "Missing required parameter: config"})
                )
            ]

        # Update config
        updated_config = gateway.config_registry.set_provider(provider, config, merge=merge)

        # Refresh available providers
        gateway.available_providers = gateway._detect_providers()

        result = {
            "success": True,
            "provider": provider,
            "config": updated_config,
            "message": f"Configuration updated for provider '{provider}'",
        }

        logger.info(f"Updated config for provider: {provider}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.exception(f"Error setting config: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Failed to set config", "message": str(e)})
            )
        ]


async def handle_llm_config_add_instance(arguments: Any) -> Sequence[TextContent]:
    """Handle llm_config_add_instance tool invocation."""
    try:
        provider = arguments.get("provider")
        instance = arguments.get("instance")

        if not provider:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": "Missing required parameter: provider"})
                )
            ]

        if not instance:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": "Missing required parameter: instance"})
                )
            ]

        # Add instance
        updated_config = gateway.config_registry.add_provider_instance(provider, instance)

        result = {
            "success": True,
            "provider": provider,
            "instance": instance,
            "total_instances": len(updated_config.get("instances", [])),
            "message": f"Instance added to provider '{provider}'",
        }

        logger.info(f"Added instance to provider: {provider}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.exception(f"Error adding instance: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Failed to add instance", "message": str(e)})
            )
        ]


async def handle_llm_config_guide(arguments: Any) -> Sequence[TextContent]:
    """Handle llm_config_guide tool invocation."""
    try:
        from uer.llm.config_guide import ConfigGuide

        provider = arguments.get("provider")

        if not provider:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": "Missing required parameter: provider"})
                )
            ]

        # Get full configuration guide
        guide = ConfigGuide.get_full_guide(provider)

        logger.info(f"Generated config guide for provider: {provider}")
        return [TextContent(type="text", text=json.dumps(guide, indent=2))]

    except Exception as e:
        logger.exception(f"Error generating config guide: {str(e)}")
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": "Failed to generate config guide", "message": str(e)}),
            )
        ]


async def handle_mcp_list_tools(arguments: Any) -> Sequence[TextContent]:
    """Handle mcp_list_tools tool invocation."""
    try:
        server = arguments.get("server")
        prefix = arguments.get("prefix")

        # List all servers or filter by prefix
        if not server:
            available_servers = mcp_manager.list_servers()

            # Apply prefix filter if provided
            if prefix:
                available_servers = [
                    s for s in available_servers if s.lower().startswith(prefix.lower())
                ]
                logger.info(f"Filtered {len(available_servers)} servers with prefix '{prefix}'")
            else:
                logger.info(f"Listing all {len(available_servers)} configured MCP servers")

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "operation": "list_servers",
                            "servers": available_servers,
                            "count": len(available_servers),
                        },
                        indent=2,
                    ),
                )
            ]

        # List tools from specific server
        logger.info(f"Listing tools from MCP server: {server}")
        tools = await mcp_manager.list_tools(server)

        logger.info(f"Found {len(tools)} tools on server {server}")
        return [
            TextContent(type="text", text=json.dumps({"server": server, "tools": tools}, indent=2))
        ]

    except ValueError as e:
        # Server not found - show available servers
        available_servers = mcp_manager.list_servers()
        error_msg = str(e)
        if available_servers:
            error_msg += f". Available servers: {', '.join(available_servers)}"
        else:
            error_msg += ". No MCP servers configured. Use mcp_servers tool to add servers."
        logger.error(f"MCP list_tools failed: {error_msg}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "Server not found",
                        "message": error_msg,
                        "available_servers": available_servers,
                    }
                ),
            )
        ]
    except RuntimeError as e:
        logger.error(f"MCP list_tools failed: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "MCP operation failed", "message": str(e)})
            )
        ]

    except Exception as e:
        logger.exception(f"Unexpected error in mcp_list_tools: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Internal error", "message": str(e)})
            )
        ]


async def handle_mcp_call(arguments: Any) -> Sequence[TextContent]:
    """Handle mcp_call tool invocation."""
    try:
        server = arguments.get("server")
        tool = arguments.get("tool")
        tool_arguments = arguments.get("arguments", {})

        if not server or not tool:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": "Missing required parameters",
                            "message": "server and tool are required",
                        }
                    ),
                )
            ]

        logger.info(f"Calling tool {tool} on MCP server {server}")
        result = await mcp_manager.call_tool(server, tool, tool_arguments)

        logger.info(f"MCP tool call successful: {server}.{tool}")
        return [
            TextContent(
                type="text",
                text=json.dumps({"server": server, "tool": tool, "result": result}, indent=2),
            )
        ]

    except RuntimeError as e:
        logger.error(f"MCP call_tool failed: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "MCP operation failed", "message": str(e)})
            )
        ]

    except Exception as e:
        logger.exception(f"Unexpected error in mcp_call: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Internal error", "message": str(e)})
            )
        ]


async def handle_mcp_registry(arguments: Any) -> Sequence[TextContent]:
    """Handle mcp_registry operations - browse and install from official registry."""
    try:
        import httpx

        operation = arguments.get("operation")

        if not operation:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Missing parameter", "message": "operation is required"}
                    ),
                )
            ]

        registry_url = "https://registry.modelcontextprotocol.io"

        # LIST operation - browse all servers
        if operation == "list":
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{registry_url}/servers", timeout=10.0)
                    response.raise_for_status()
                    servers = response.json()

                    logger.info(f"Listed {len(servers)} servers from registry")
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "operation": "list",
                                    "count": len(servers),
                                    "servers": servers[:50],  # Limit to first 50
                                    "note": "Showing first 50 servers. Use 'search' to find specific servers.",
                                },
                                indent=2,
                            ),
                        )
                    ]
            except Exception as e:
                logger.error(f"Failed to list registry servers: {e}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": "Registry error", "message": str(e)}),
                    )
                ]

        # SEARCH operation
        elif operation == "search":
            query = arguments.get("query")
            if not query:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": "Missing parameter", "message": "query required for search"}
                        ),
                    )
                ]

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{registry_url}/servers", params={"q": query}, timeout=10.0
                    )
                    response.raise_for_status()
                    results = response.json()

                    logger.info(f"Found {len(results)} servers matching '{query}'")
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "operation": "search",
                                    "query": query,
                                    "count": len(results),
                                    "results": results,
                                },
                                indent=2,
                            ),
                        )
                    ]
            except Exception as e:
                logger.error(f"Failed to search registry: {e}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": "Registry error", "message": str(e)}),
                    )
                ]

        # GET operation - view server details
        elif operation == "get":
            server_id = arguments.get("server_id")
            if not server_id:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": "Missing parameter", "message": "server_id required for get"}
                        ),
                    )
                ]

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{registry_url}/servers/{server_id}", timeout=10.0)
                    response.raise_for_status()
                    server_info = response.json()

                    logger.info(f"Retrieved server details: {server_id}")
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "operation": "get",
                                    "server_id": server_id,
                                    "details": server_info,
                                },
                                indent=2,
                            ),
                        )
                    ]
            except Exception as e:
                logger.error(f"Failed to get server details: {e}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": "Registry error", "message": str(e)}),
                    )
                ]

        # INSTALL operation - add server from registry to config
        elif operation == "install":
            server_id = arguments.get("server_id")
            if not server_id:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": "Missing parameter",
                                "message": "server_id required for install",
                            }
                        ),
                    )
                ]

            try:
                # Fetch server details from registry
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{registry_url}/servers/{server_id}", timeout=10.0)
                    response.raise_for_status()
                    server_info = response.json()

                # Extract installation info
                config_overrides = arguments.get("config_overrides", {})

                # Determine server name (use last part of server_id or custom name)
                server_name = server_id.split(".")[-1].replace("server-", "")

                # Build configuration from registry info
                from uer.mcp.config import MCPServerConfig

                # Get command and args from registry metadata
                command = server_info.get("command", "npx")
                args = config_overrides.get("args") or server_info.get("args", ["-y", server_id])
                env = config_overrides.get("env") or server_info.get("env", {})

                new_server = MCPServerConfig(
                    name=server_name,
                    command=command,
                    args=args,
                    env=env,
                    transport="stdio",
                )

                mcp_manager.config.servers[server_name] = new_server

                logger.info(f"Installed server from registry: {server_id} as '{server_name}'")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "operation": "install",
                                "server_id": server_id,
                                "installed_as": server_name,
                                "config": {
                                    "command": command,
                                    "args": args,
                                    "env": env,
                                },
                                "message": f"Server '{server_name}' installed successfully",
                            },
                            indent=2,
                        ),
                    )
                ]
            except Exception as e:
                logger.error(f"Failed to install server: {e}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": "Installation failed", "message": str(e)}),
                    )
                ]

        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Invalid operation", "message": f"Unknown operation: {operation}"}
                    ),
                )
            ]

    except Exception as e:
        logger.exception(f"Unexpected error in mcp_registry: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Internal error", "message": str(e)})
            )
        ]


async def handle_mcp_servers(arguments: Any) -> Sequence[TextContent]:
    """Handle mcp_servers CRUD operations."""
    try:
        operation = arguments.get("operation")

        if not operation:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Missing required parameter", "message": "operation is required"}
                    ),
                )
            ]

        # LIST operation
        if operation == "list":
            servers_info = {}
            for name, config in mcp_manager.config.servers.items():
                servers_info[name] = {
                    "command": config.command,
                    "args": config.args,
                    "env": config.env,
                    "transport": config.transport,
                    "url": config.url,
                    "headers": config.headers,
                }

            logger.info(f"Listed {len(servers_info)} MCP servers")
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"operation": "list", "servers": servers_info}, indent=2),
                )
            ]

        # GET operation
        elif operation == "get":
            server_name = arguments.get("server_name")
            if not server_name:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": "Missing parameter",
                                "message": "server_name required for get",
                            }
                        ),
                    )
                ]

            if server_name not in mcp_manager.config.servers:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": "Not found", "message": f"Server '{server_name}' not found"}
                        ),
                    )
                ]

            config = mcp_manager.config.servers[server_name]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "operation": "get",
                            "server_name": server_name,
                            "config": {
                                "command": config.command,
                                "args": config.args,
                                "env": config.env,
                                "transport": config.transport,
                                "url": config.url,
                                "headers": config.headers,
                            },
                        },
                        indent=2,
                    ),
                )
            ]

        # ADD operation
        elif operation == "add":
            servers = arguments.get("servers", {})
            if not servers:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": "Missing parameter", "message": "servers required for add"}
                        ),
                    )
                ]

            from uer.mcp.config import MCPServerConfig

            added = []
            errors = []

            for name, config in servers.items():
                if name in mcp_manager.config.servers:
                    errors.append(f"Server '{name}' already exists (use 'update' to modify)")
                    continue

                try:
                    new_server = MCPServerConfig(
                        name=name,
                        command=config.get("command", ""),
                        args=config.get("args", []),
                        env=config.get("env", {}),
                        transport=config.get("transport", "stdio"),
                        url=config.get("url", ""),
                        headers=config.get("headers", {}),
                    )
                    mcp_manager.config.servers[name] = new_server
                    added.append(name)
                    logger.info(f"Added MCP server: {name}")
                except Exception as e:
                    errors.append(f"Failed to add '{name}': {str(e)}")

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "operation": "add",
                            "added": added,
                            "errors": errors if errors else None,
                        },
                        indent=2,
                    ),
                )
            ]

        # UPDATE operation
        elif operation == "update":
            servers = arguments.get("servers", {})
            if not servers:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": "Missing parameter", "message": "servers required for update"}
                        ),
                    )
                ]

            from uer.mcp.config import MCPServerConfig

            updated = []
            errors = []

            for name, config in servers.items():
                if name not in mcp_manager.config.servers:
                    errors.append(f"Server '{name}' not found (use 'add' to create)")
                    continue

                try:
                    new_server = MCPServerConfig(
                        name=name,
                        command=config.get("command", ""),
                        args=config.get("args", []),
                        env=config.get("env", {}),
                        transport=config.get("transport", "stdio"),
                        url=config.get("url", ""),
                        headers=config.get("headers", {}),
                    )
                    mcp_manager.config.servers[name] = new_server
                    updated.append(name)
                    logger.info(f"Updated MCP server: {name}")
                except Exception as e:
                    errors.append(f"Failed to update '{name}': {str(e)}")

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "operation": "update",
                            "updated": updated,
                            "errors": errors if errors else None,
                        },
                        indent=2,
                    ),
                )
            ]

        # DELETE operation
        elif operation == "delete":
            server_name = arguments.get("server_name")
            if not server_name:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": "Missing parameter",
                                "message": "server_name required for delete",
                            }
                        ),
                    )
                ]

            if server_name not in mcp_manager.config.servers:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": "Not found", "message": f"Server '{server_name}' not found"}
                        ),
                    )
                ]

            del mcp_manager.config.servers[server_name]
            logger.info(f"Deleted MCP server: {server_name}")

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "operation": "delete",
                            "deleted": server_name,
                            "message": f"Server '{server_name}' deleted successfully",
                        },
                        indent=2,
                    ),
                )
            ]

        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Invalid operation", "message": f"Unknown operation: {operation}"}
                    ),
                )
            ]

    except Exception as e:
        logger.exception(f"Unexpected error in mcp_servers: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Internal error", "message": str(e)})
            )
        ]


async def main() -> None:
    """Run the MCP server via stdio transport."""
    logger.info("Starting UER MCP server...")
    logger.info(f"Available LLM providers: {gateway.get_available_providers()}")
    logger.info(f"Available MCP servers: {mcp_manager.list_servers()}")

    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        # Cleanup MCP connections
        logger.info("Shutting down MCP connections...")
        await mcp_manager.disconnect_all()


if __name__ == "__main__":
    asyncio.run(main())
