🚨 Development has moved to https://github.com/milatechtransfer/paperpal

# paperpal

MCP Extension to aid you in searching and writing literature reviews

> Check out this [conversation with Claude](https://claude.ai/share/0572fbd9-3ba2-4143-9f7f-5cae205c6d0d) to see what it can do

## How it works

`paperpal` gives your LLMs access to [arxiv](https://www.arxiv.org) and [Hugging Face papers](https://huggingface.co/papers).
You can then have a natural conversation with your favourite LLMs (e.g. Claude) and have it guide you.

You can:

* Discuss papers
* Look for new papers
* Organize ideas for liteature reviews
* etc.

Of course, this tool is as good as the sum of its parts. LLMs can still hallucinate, and semantic search is never perfect.

## Quickstart

There are many different ways with which you can interact with an MCP server.

### Claude Desktop App

> If this is your first time using an MCP server for Claude Desktop App, see https://modelcontextprotocol.io/quickstart/user

First, clone this repository locally:

    git clone https://github.com/jerpint/paperpal

Next, add the extension to your app. Open your configuration file (on macOS this should be `~/Library/Application Support/Claude/claude_desktop_config.json`) and and add the following to the extension:

For example on MacOS:

```python
{
  "mcpServers": {
    "paperpal": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/<username>/paperpal",
        "run",
        "paperpal.py"
      ]
    }
  }
}
```

Restart your Claude Desktop App and you should see it appear.


### Cursor

> If this is your first time using an MCP server for Cursor, see https://docs.cursor.com/context/model-context-protocol#remote-development

First, clone this repository locally:

    git clone https://github.com/jerpint/paperpal


Add this to the root of the project in a `.cursor/mcp.json` file:

```
{
  "mcpServers": {
    "paperpal": {
      "command": "/Users/jeremypinto/.cargo/bin/uv",
      "args": [
        "--directory",
        "/Users/jeremypinto/paperpal",
        "run",
        "paperpal.py"
      ]
    }
  }
}
```
