"""agent-browser CLI backend.

An alternative page-fetching backend that drives the external `agent-browser`
CLI (Chrome over CDP) instead of the in-process Playwright + Crawl4AI stack.

It shells out to `agent-browser`, so the binary must be installed and on PATH:

    npm i -g agent-browser && agent-browser install

The public entrypoint, `fetch_markdown_via_agent_browser`, returns the same
dict shape as `ContentDistiller.distill` so callers can swap backends freely:

    {"markdown": str, "title": str, "url": str, "method": str}
"""
import asyncio
import os
import shutil
import uuid
from typing import Optional, Dict, Any

from common import logger

# Binary name; overridable via env for non-standard installs.
AGENT_BROWSER_BIN = os.getenv("AGENT_BROWSER_BIN", "agent-browser")


def is_available() -> bool:
    """Return True when the agent-browser CLI is found on PATH."""
    return shutil.which(AGENT_BROWSER_BIN) is not None


async def _run(args: list[str], timeout_s: float) -> tuple[int, str, str]:
    """Run an agent-browser subcommand, returning (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        AGENT_BROWSER_BIN,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        raise
    return (
        proc.returncode if proc.returncode is not None else -1,
        out.decode("utf-8", "replace") if out else "",
        err.decode("utf-8", "replace") if err else "",
    )


async def fetch_markdown_via_agent_browser(
    url: str,
    timeout: int = 60000,
    query: Optional[str] = None,
    render: bool = True,
) -> Dict[str, Any]:
    """Fetch a page as Markdown using the agent-browser CLI.

    Args:
        url: Target page URL.
        timeout: Overall budget in milliseconds.
        query: Optional intent string; used as a `read --filter` hint.
        render: When True, launch Chrome (open + read) so JavaScript runs.
            When False, use the lighter HTTP-only `read <url>` path.

    Returns:
        {"markdown", "title", "url", "method"}. On failure, markdown is "" and
        an "error" key describes the reason.
    """
    if not is_available():
        return {
            "markdown": "",
            "title": "",
            "url": url,
            "method": "agent-browser",
            "error": f"{AGENT_BROWSER_BIN} not found on PATH",
        }

    timeout_s = max(5.0, timeout / 1000.0)
    # Isolate each call in its own session so concurrent crawls don't collide.
    session = f"mcpws-{uuid.uuid4().hex[:12]}"
    # Give the CLI's internal waits the same budget as our subprocess.
    env_timeout = str(int(timeout))

    read_args = ["--session", session, "read"]
    if query:
        read_args += ["--filter", query]

    # Point agent-browser's default wait timeout at our budget.
    os.environ["AGENT_BROWSER_DEFAULT_TIMEOUT"] = env_timeout

    try:
        if render:
            rc, out, err = await _run(
                ["--session", session, "open", url], timeout_s
            )
            if rc != 0:
                return {
                    "markdown": "",
                    "title": "",
                    "url": url,
                    "method": "agent-browser",
                    "error": f"open failed: {err.strip() or out.strip()}",
                }
            rc, out, err = await _run(read_args, timeout_s)
        else:
            # HTTP-only path: read fetches the URL directly, no Chrome.
            rc, out, err = await _run(read_args + [url], timeout_s)

        if rc != 0:
            return {
                "markdown": "",
                "title": "",
                "url": url,
                "method": "agent-browser",
                "error": f"read failed: {err.strip() or out.strip()}",
            }

        markdown = out.strip()

        # Best-effort title; non-fatal if it fails.
        title = ""
        try:
            t_rc, t_out, _ = await _run(
                ["--session", session, "get", "title"], min(timeout_s, 15.0)
            )
            if t_rc == 0:
                title = t_out.strip()
        except Exception:
            pass

        return {
            "markdown": markdown,
            "title": title,
            "url": url,
            "method": "agent-browser",
        }
    except asyncio.TimeoutError:
        return {
            "markdown": "",
            "title": "",
            "url": url,
            "method": "agent-browser",
            "error": "timeout",
        }
    finally:
        # Only rendered mode opens a browser session worth closing.
        if render:
            try:
                await _run(["--session", session, "close"], 15.0)
            except Exception:
                pass
