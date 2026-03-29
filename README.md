# MCP for FirecREST

## Run as local instance

To run the local instance first install `uv` command

```info
This is a local instance, we aim to produce an MCP that runs in a public environment as a plugin (ie, `https://mcp.firecrest.cscs.ch`).
```

```bash
$ curl -LsSf https://astral.sh/uv/install.sh | sh
$ cd /path/this/repo
$ # create a virtual environment
$ uv venv
$ source .venv/bin/activate
$ (firecrest) uv add "mcp[cli]" httpx
$ cp .env.tmp .env
$ # Change the variables as fitting in your FirecREST deployment in .env file
$ uv run src/server.py
[03/20/26 15:00:10] INFO     Starting MCP server on port 8888 

```

### Test local instance on Claude Desktop

On Claude Desktop, you can configure the MCP to be used in your chat as a new Connection.

First, modify your Claude Desktop configuration file. In MacOS and Linux add to this file:

```bash
$ vi ~/Library/Application\ Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/this/folder",
        "run",
        "src/server.py"
      ]
    }
  }
}
```

Then close Claude Desktop and open a new instance, you should see in Connections (+) the FirecREST MCP ready to use.

## Running Docker Compose

WIP