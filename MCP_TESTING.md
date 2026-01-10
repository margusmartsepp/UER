# MCP Tool Orchestration Testing Guide

This guide shows how to test UER's MCP orchestration capabilities with various MCP servers.

## Available MCP Servers

UER comes pre-configured with 3 MCP servers for testing:

1. **filesystem** - File operations (read, write, list, search)
2. **memory** - Key-value storage (store, retrieve, list)
3. **fetch** - Web scraping and HTTP requests

## Quick Start Testing

### 1. Start UER MCP Server

```bash
npx uer-mcp@latest
```

Or from source:
```bash
python -m uer.server
```

### 2. Test with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

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

### 3. Test MCP Tools in Claude

#### List Available MCP Servers
```
Can you list what MCP servers are available?
```

Expected: filesystem, memory, fetch

#### Test Filesystem MCP
```
Use mcp_list_tools to see what tools are available on the filesystem server
```

Then:
```
Use mcp_call to read the README.md file from the filesystem server
```

#### Test Memory MCP
```
Use mcp_call on the memory server to store a key-value pair:
- tool: store_memory
- arguments: {"key": "test", "value": "Hello from UER!"}
```

Then:
```
Use mcp_call to retrieve the value for key "test" from memory server
```

#### Test Fetch MCP
```
Use mcp_call on the fetch server to fetch the npm package info:
- tool: fetch
- arguments: {"url": "https://registry.npmjs.org/uer-mcp"}
```

## Testing from Command Line

You can also test using the MCP inspector:

```bash
# Install MCP inspector
npm install -g @modelcontextprotocol/inspector

# Test UER server
mcp-inspector npx uer-mcp@latest
```

This opens a web UI where you can:
1. See all available tools (llm_call, mcp_call, mcp_list_tools)
2. Call tools interactively
3. View responses

## Example Test Scenarios

### Scenario 1: File Analysis with LLM

1. Use `mcp_call` to read a code file via filesystem server
2. Use `llm_call` to analyze the code with Claude/GPT
3. Use `mcp_call` to write the analysis to a new file

### Scenario 2: Web Research with Memory

1. Use `mcp_call` with fetch server to get web content
2. Use `llm_call` to summarize the content
3. Use `mcp_call` with memory server to store the summary

### Scenario 3: Multi-Server Orchestration

1. Use `mcp_list_tools` to discover tools on all servers
2. Use `llm_call` to decide which tools to use
3. Use `mcp_call` to execute tools across multiple servers
4. Use `llm_call` to synthesize results

## Adding More MCP Servers

To add more MCP servers, you can:

1. **Via Environment Variable** (future feature):
   ```bash
   export UER_MCP_CONFIG='{"github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}}'
   ```

2. **Via Config File** (future feature):
   Create `~/.uer/mcp_config.json`:
   ```json
   {
     "servers": {
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token"
         }
       }
     }
   }
   ```

## Popular MCP Servers to Try

### Official MCP Servers
- `@modelcontextprotocol/server-filesystem` - File operations ✅ (included)
- `@modelcontextprotocol/server-memory` - Key-value storage ✅ (included)
- `@modelcontextprotocol/server-fetch` - HTTP requests ✅ (included)
- `@modelcontextprotocol/server-sqlite` - SQLite database
- `@modelcontextprotocol/server-github` - GitHub API
- `@modelcontextprotocol/server-postgres` - PostgreSQL database
- `@modelcontextprotocol/server-puppeteer` - Browser automation
- `@modelcontextprotocol/server-brave-search` - Web search
- `@modelcontextprotocol/server-google-maps` - Maps API

### Community MCP Servers
- `@executeautomation/playwright-mcp-server` - Playwright browser automation
- `@modelcontextprotocol/server-slack` - Slack integration
- `@modelcontextprotocol/server-aws-kb-retrieval` - AWS Knowledge Base

See full list: https://github.com/modelcontextprotocol/servers

## Troubleshooting

### MCP Server Won't Connect
- Ensure `npx` is installed: `npm install -g npx`
- Check that the MCP server package exists on npm
- Verify environment variables are set correctly

### Tool Call Fails
- Use `mcp_list_tools` first to see available tools
- Check tool input schema matches your arguments
- Look at UER server logs for detailed error messages

### Performance Issues
- MCP servers are spawned on first use (lazy loading)
- Connections are reused for subsequent calls
- Consider using fewer MCP servers if memory is limited

## Next Steps

Once basic testing works:
1. Test with more complex MCP servers (SQLite, GitHub, Puppeteer)
2. Chain multiple MCP calls together
3. Use LLM to orchestrate MCP tools dynamically
4. Build workflows combining LLM reasoning + MCP actions
