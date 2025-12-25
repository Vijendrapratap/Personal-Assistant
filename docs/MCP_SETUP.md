# Model Context Protocol (MCP) Setup

Alfred uses MCP to connect to external tools like the Filesystem and Web Search.

## Prerequisite
- Python 3.11+
- Node.js & npm (for running MCP servers like filesystem and brave-search)

## Configuration
The MCP servers are defined in [mcp_config.json](../mcp_config.json).

```json
{
  "mcpServers": {
    "filesystem": { ... },
    "brave-search": { ... },
    "memory": { ... }
  }
}
```

## Servers

### Filesystem MCP
Allows Alfred to read and write files in the `user_data` directory.
- **Provider**: `@modelcontextprotocol/server-filesystem`
- **Arguments**: Path to the allowed directory (e.g., `/home/pratap/work/Personal-Assistant/user_data`)

### Brave Search MCP
Allows Alfred to search the web using Brave Search.
- **Provider**: `@modelcontextprotocol/server-brave-search`
- **Environment Variable**: `BRAVE_API_KEY` (Must be set in your shell or `.env`)

### Memory MCP
Connects to the Postgres database to provide structured memory access.
- **Provider**: `mcp_server_postgres`
- **Connection**: `postgresql://user:password@localhost/alfred_memory`

## Running
When initializing the Agent or the MCP client, ensure that `npx` is in your PATH and the necessary NPM packages are accessible or will be installed on demand (using `npx -y` as configured).
