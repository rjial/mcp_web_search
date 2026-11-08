# Google Search Tool

A Playwright-based Python tool that bypasses search engine anti-scraping mechanisms to execute Google searches and extract results. It can be used directly as a command-line tool or as a Model Context Protocol (MCP) server to provide real-time search capabilities to AI assistants like Claude.


[中文文档](README.zh-CN.md)

## Key Features

- **Local SERP API Alternative**: No need to rely on paid search engine results API services, all searches are executed locally
- **Advanced Anti-Bot Detection Bypass Techniques**:
  - Intelligent browser fingerprint management that simulates real user behavior
  - Automatic saving and restoration of browser state to reduce verification frequency
  - Smart headless/headed mode switching, automatically switching to headed mode when verification is needed
  - Randomization of device and locale settings to reduce detection risk
- **Raw HTML Retrieval**: Ability to fetch the raw HTML of search result pages (with CSS and JavaScript removed) for analysis and debugging when Google's page structure changes
- **Page Screenshot**: Automatically captures and saves a full-page screenshot when saving HTML content
- **MCP Server Integration**: Provides real-time search capabilities to AI assistants like Claude without requiring additional API keys
- **Completely Open Source and Free**: All code is open source with no usage restrictions, freely customizable and extensible
- **Python Native**: Built with Python for better performance and easier deployment

## Technical Features

- **Developed with Python 3.12+**, providing excellent performance and wide compatibility (see `Dockerfile.ubuntu`)
- Browser automation based on **Playwright**, supporting multiple browser engines
- Command-line parameter support for search keywords
- **MCP server support** for AI assistant integration
- Returns search results with title, link, and snippet
- Option to retrieve raw HTML of search result pages for analysis
- JSON format output
- Support for both headless and headed modes (for debugging)
- Detailed logging output
- Robust error handling
- Browser state saving and restoration to effectively avoid anti-bot detection
- **Anti-bot protection mechanisms** at multiple levels

## Installation

### With uv (recommended)

The project ships a `pyproject.toml`, so [uv](https://docs.astral.sh/uv/) can
manage the environment and expose console scripts.

```bash
git clone https://github.com/iwanghc/mcp_web_search.git
cd mcp_web_search

uv sync                              # create .venv and install dependencies
uv run playwright install chromium   # install the browser (one time)

uv run mcp-web-search-cli "search keywords"   # run the CLI
uv run mcp-web-search                          # run the MCP server (stdio)
```

#### Run without cloning

Because the package is installable from Git, you can run it without cloning the
repository first. uv fetches and builds it into its own cache:

```bash
# Ephemeral run
uvx --from git+https://github.com/iwanghc/mcp_web_search.git@main mcp-web-search-cli "search keywords"

# Or install persistently so the console scripts land on your PATH
uv tool install git+https://github.com/iwanghc/mcp_web_search.git@main
mcp-web-search-cli "search keywords"
```

Playwright browsers are shared via the default cache (`~/.cache/ms-playwright`),
so a `playwright install chromium` run once on the machine is reused by every
environment.

### With pip

```bash
# Install from source
git clone https://github.com/iwanghc/mcp_web_search.git
cd mcp_web_search

# Install Python dependencies
pip install -r requirements.txt     # or: pip install .

# Install Playwright browsers
playwright install chromium
```

> Requires **mcp >= 2** (the server targets the MCP Python SDK v2 API). The
> package itself requires Python 3.11+.

## Usage

### Command Line Tool

```bash
# Direct command line usage
python cli.py "search keywords"

# Using command line options
python cli.py --limit 5 --timeout 30000 "search keywords"

# Get raw HTML of search result page
python cli.py --get-html "search keywords"

# Get HTML and save to file
python cli.py --get-html --save-html "search keywords"
```

### MCP Server

```bash
# Configure model API KEY and other information in dotenv.env
# Run MCP client (example)
python -m mcp_integration.client
```

#### Command Line Options

- `-l, --limit <number>`: Result count limit (default: 10)
- `-t, --timeout <number>`: Timeout time in milliseconds (default: 30000)
- `--no-headless`: Show browser interface (for debugging)
- `--state-file <path>`: Browser state file path (default: ./browser-state.json)
- `--no-save-state`: Don't save browser state
- `-b, --basic-view, --gbv`: Use Google Basic Variant (gbv=1)
- `--manual-captcha`: Allow interactive manual CAPTCHA solving
- `--get-html`: Get raw HTML of search result page instead of parsed results
- `--save-html`: Save HTML to file (use with --get-html)
- `--html-output <path>`: Specify HTML output file path (use with --get-html and --save-html)
- `-V, --version`: Show version number
- `-h, --help`: Show help information

#### Output Example

```json
{
  "query": "deepseek",
  "results": [
    {
      "title": "DeepSeek",
      "link": "https://www.deepseek.com/",
      "snippet": "DeepSeek-R1 is now live and open source, rivaling OpenAI's Model o1. Available on web, app, and API. Click for details. Into ..."
    },
    {
      "title": "DeepSeek",
      "link": "https://www.deepseek.com/",
      "snippet": "DeepSeek-R1 is now live and open source, rivaling OpenAI's Model o1. Available on web, app, and API. Click for details. Into ..."
    },
    {
      "title": "deepseek-ai/DeepSeek-V3",
      "link": "https://github.com/deepseek-ai/DeepSeek-V3",
      "snippet": "We present DeepSeek-V3, a strong Mixture-of-Experts (MoE) language model with 671B total parameters with 37B activated for each token."
    }
    // More results...
  ]
}
```

#### HTML Output Example

When using the `--get-html` option, the function returns an `HtmlResponse`-like object. Example JSON fields (snake_case to match code):

```json
{
  "query": "playwright automation",
  "url": "https://www.google.com/",
  "original_html_length": 1291733,
  "html": "<!DOCTYPE html><html itemscope=\"\" itemtype=\"http://schema.org/SearchResultsPage\" lang=\"zh-CN\">...",
  "saved_path": null,
  "screenshot_path": null
}
```

If you use the `--save-html` option, the output will include `saved_path` and possibly `screenshot_path`:

```json
{
  "query": "playwright automation",
  "url": "https://www.google.com/",
  "original_html_length": 1292241,
  "html": "<!DOCTYPE html>...",
  "saved_path": "./google-search-html/playwright_automation-2025-04-06T03-30-06-852Z.html",
  "screenshot_path": "./google-search-html/playwright_automation-2025-04-06T03-30-06-852Z.png"
}
```

### MCP Server

This project provides Model Context Protocol (MCP) server functionality, allowing AI assistants like Claude to directly use Google search capabilities. MCP is an open protocol that enables AI assistants to securely access external tools and data.

The server runs over **stdio by default** — the MCP client launches the process
on demand and talks to it over stdin/stdout, so there is no standing HTTP server
to manage. (An optional HTTP/SSE mode is available; see
[Recent Changes](#recent-changes).)

#### Available tools

| Tool | Description |
| --- | --- |
| `google-search` | Run a Google search and return structured results (title, link, snippet). |
| `get-webpage-html` | Perform a search and return the cleaned HTML of the results page, with an optional screenshot. |
| `get-webpage-markdown` | Visit a URL and distill it to Markdown. Supports a `backend` option (see below). |
| `google-search-and-browse` | Search, then visit the top N result pages and return distilled Markdown for each. |

##### `get-webpage-markdown` backends

`get-webpage-markdown` accepts a `backend` argument:

- `"playwright"` (default) — the built-in stealth Playwright + Crawl4AI distiller.
- `"agent-browser"` — shells out to the external
  [agent-browser](https://www.npmjs.com/package/agent-browser) CLI (Chrome over
  CDP). Set `renderJs: false` for a lighter HTTP-only fetch. This backend
  requires the Node CLI on `PATH`:

  ```bash
  npm i -g agent-browser && agent-browser install
  ```

  Override the binary location with the `AGENT_BROWSER_BIN` environment variable.

#### Integration with Claude Desktop / Claude Code

Edit the Claude Desktop configuration file:
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add a server entry and restart Claude. Pick whichever launcher matches your
installation:

**Run from a local checkout with uv** (`--directory` sets the working directory
so `logs/`, `user_data/`, and `browser-state.json` land in the project):

```json
{
  "mcpServers": {
    "google-search": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/mcp_web_search", "--no-sync", "mcp-web-search"]
    }
  }
}
```

**Run without cloning, straight from Git:**

```json
{
  "mcpServers": {
    "google-search": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/iwanghc/mcp_web_search.git@main", "mcp-web-search"]
    }
  }
}
```

**After `uv tool install` (or `pip install .`)**, the console script is on PATH:

```json
{
  "mcpServers": {
    "google-search": {
      "command": "mcp-web-search"
    }
  }
}
```

**Plain module invocation** (no packaging; run from the project directory):

```json
{
  "mcpServers": {
    "google-search": {
      "command": "python",
      "args": ["-m", "mcp_integration.server"]
    }
  }
}
```

For Claude Code, the same can be registered in one command:

```bash
claude mcp add google-search -- uvx --from git+https://github.com/iwanghc/mcp_web_search.git@main mcp-web-search
```

On start the client sends `initialize` and then `list_tools`, which returns the
four tools above. After integration, you can directly use search functionality
in Claude, such as "Search for the latest AI research".

## Project Structure

```
google_search/
├── Core Functions/
│   ├── google_search/
│   │   ├── engine.py              # Search engine implementation
│   │   ├── browser_manager.py     # Browser management and automation
│   │   ├── search_executor.py     # Search execution logic
│   │   ├── html_extractor.py      # HTML parsing and extraction
│   │   ├── fingerprint.py         # Browser fingerprint management
│   │   ├── distiller.py           # Content distillation to Markdown
│   │   ├── agent_browser_backend.py # Optional agent-browser CLI backend
│   │   ├── utils.py               # Utility functions
│   │   └── __init__.py            # Package initialization
│   └── cli.py                     # Command line interface
├── MCP Integration/
│   ├── mcp_integration/
│   │   ├── server.py              # MCP server implementation
│   │   ├── client.py              # MCP client implementation
│   │   └── __init__.py            # Package initialization
├── Common Utilities/
│   ├── common/
│   │   ├── logger.py              # Logging system
│   │   ├── types.py               # Common data types
│   │   └── __init__.py            # Package initialization
├── Configuration & Runtime/
│   ├── pyproject.toml              # Packaging, dependencies, console scripts
│   ├── requirements.txt            # Python dependencies (pip/Docker workflows)
│   ├── dotenv.env                  # Environment variables
│   ├── browser-state.json          # Browser state persistence
│   ├── browser-state-fingerprint.json # Browser fingerprint data
│   └── .gitignore                  # Git ignore rules
├── Documentation/
│   ├── README.md                   # English documentation
│   ├── README.zh-CN.md             # Chinese documentation
│   └── google_search/REFACTOR_README.md # Refactoring notes
├── Development/
│   ├── .vscode/                    # VS Code configuration
│   └── logs/                       # Application logs
└── Other/
  └── __pycache__/                # Python cache files
```

## Technology Stack

- **Python 3.11+**: Development language, providing excellent performance and compatibility
- **Playwright**: For browser automation, supporting multiple browsers
- **MCP SDK v2** (`mcp >= 2`): For implementing MCP server development tools
- **agent-browser (optional)**: External Node CLI used as an alternative page-fetching backend
- **asyncio**: Python's standard library for asynchronous I/O
- **aiofiles**: Asynchronous file operations

## Development Guide

All commands can be run in the project root directory. With uv:

```bash
# Install dependencies into .venv
uv sync

# Install Playwright browsers (when running locally)
uv run playwright install chromium

# Run CLI tool
uv run mcp-web-search-cli "search keywords"

# Start MCP server (stdio by default; SSE/HTTP when MCP_SSE=1)
uv run mcp-web-search

# Test MCP client
uv run python -m mcp_integration.client
```

The equivalent plain-Python / pip commands also work:

```bash
pip install -r requirements.txt
playwright install chromium
python cli.py "search keywords"
python -m mcp_integration.server
python -m mcp_integration.client
```

## Error Handling

The tool has built-in robust error handling mechanisms:

- Provides friendly error information when browser startup fails
- Automatically returns error status when network connection issues occur
- Provides detailed logs when search result parsing fails
- Gracefully exits and returns useful information in timeout situations

## Notes

### General Notes

- This tool is for learning and research purposes only
- Please comply with Google's terms of service and policies
- Don't send requests too frequently to avoid being blocked by Google
- Some regions may require proxies to access Google
- Playwright requires browser installation, which will be automatically downloaded on first use

### State Files

- State files contain browser cookies and storage data, please keep them safe
- Using state files can effectively avoid Google's anti-bot detection and improve search success rate

### MCP Server

- When using MCP server, please ensure Claude Desktop is updated to the latest version
- When configuring Claude Desktop, please use absolute paths pointing to MCP server files

### Windows Environment Special Notes

- In Windows environment, first run may require administrator privileges to install Playwright browsers
- If you encounter permission issues, try running Command Prompt or PowerShell as administrator
- Windows Firewall may block Playwright browser network connections, please allow access when prompted
- Browser state files are saved by default in the user's home directory under `.google-search-browser-state.json`
- Log files are saved in the system temporary directory under `google-search-logs` folder

## Comparison with Commercial SERP APIs

Compared to paid search engine results API services (such as SerpAPI), this project provides the following advantages:

- **Completely Free**: No API call fees required
- **Local Execution**: All searches are executed locally, no dependency on third-party services
- **Privacy Protection**: Search queries are not recorded by third parties
- **Customizability**: Completely open source, can be modified and extended as needed
- **No Usage Restrictions**: Not subject to API call count or frequency limitations
- **MCP Integration**: Native support for integration with AI assistants like Claude

## Anti-Bot Protection

This project implements multiple layers of anti-bot protection:

### Client Level Protection
- Request interval control with random delays
- Timeout protection for tool calls
- Intelligent error handling

### Server Level Protection
- Request frequency limiting
- Random delays between requests 
- Global request counting and management

### Search Level Protection
- Browser fingerprint randomization
- Device and locale randomization
- Browser state management
- Automatic CAPTCHA detection and handling

## Anti-Bot & Stealth Modes

This project provides multiple operational modes to improve reliability when searching against Google while reducing the chance of triggering anti-bot defenses.

- **Persistent Contexts (default)**: the tool uses Playwright's persistent Chromium context (stored under `./user_data` and `./browser-state.json`). Persisting state preserves cookies, localStorage, and other session artifacts so Google learns that requests come from an established browser profile. Over time this significantly reduces captcha frequency and improves the tool's reputation with Google's systems.

- **Basic View (`--basic-view`, alias `-b` / `--gbv`)**: when enabled the tool appends `&gbv=1` to the search URL (Google Basic Variant). This forces a legacy, mostly static HTML page that does not execute client-side JavaScript. Because modern fingerprinting and behavioral scripts rely on JavaScript, the Basic View bypasses a large portion of JS-based bot detection. Use this mode when modern searches yield CAPTCHAs or when you need a faster, more stable extraction surface.

- **Auto‑Retry Logic**: the engine will automatically attempt to recover from a CAPTCHA in Modern View by retrying the search once using Basic View. The fallback is performed transparently when a CAPTCHA is detected, so callers don't need to manually switch modes in many cases.

When to use each mode:

- Start with the default (persistent context, modern UI) — it provides the most natural results and preserves session behavior.
- If you encounter recurrent CAPTCHAs or need deterministic HTML structure, use `--basic-view` (or `-b` / `--gbv`).

Security & Compliance:

- Respect Google's terms of service. This project is intended for research and debugging; avoid large-scale automated scraping without proper authorization.


## Performance

- **Response Time**: Typically 5-15 seconds
- **Success Rate**: 95%+ (with state files)
- **Concurrency**: Supports asynchronous operations
- **Memory Usage**: Optimized with cleanup after each call
- **Stability**: Robust error recovery and timeout handling

## Recent Changes

- Added a `pyproject.toml` so the project is installable with uv or pip, exposing
  the `mcp-web-search` (server) and `mcp-web-search-cli` (CLI) console scripts.
  This enables running the MCP server directly in an `mcpServers` config over
  stdio, and even without cloning via `uvx`/`uv tool install` from Git.
- Migrated the MCP server to the **MCP Python SDK v2** API (`mcp >= 2`). Tool
  handlers are now wired via `Server(..., on_list_tools=, on_call_tool=)` and
  return `ListToolsResult` / `CallToolResult` instead of the removed v1
  decorators.
- Added an `agent-browser` backend for the `get-webpage-markdown` tool as an
  alternative to the built-in Playwright/Crawl4AI distiller. Select it with
  `backend: "agent-browser"` (optionally `renderJs: false`). It requires the
  external agent-browser Node CLI on `PATH`.
- Removed the top-level `Dockerfile`; use `Dockerfile.ubuntu` for building the Ubuntu-based image.
- MCP server now supports HTTP/SSE mode (Starlette + `SseServerTransport`). To run in SSE mode:

  ```bash
  MCP_SSE=1 MCP_SSE_HOST=0.0.0.0 MCP_SSE_PORT=8000 python -m mcp_integration.server
  ```

- A `/health` endpoint is available at `http://<host>:<port>/health` (returns `ok`) for container healthchecks.
- The MCP `google-search` tool now returns structured JSON (dict) as the tool result to avoid double-encoding JSON strings — clients receive a single valid JSON object.
- Process locale defaults are set to `en_US.UTF-8` inside the server process to avoid unexpected locale-dependent behavior in Playwright and logs.
- Minor lint fixes applied to `mcp_integration/server.py`.
