# main.py
import os
import asyncio
import logging
from typing import Any

import httpx
import yaml  # pyyaml
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mcp-runner")

API_BASE_URL = os.getenv("API_BASE_URL", "https://myserverbymycoco.onrender.com")
SPEC_URL = os.getenv("SPEC_URL", f"{API_BASE_URL}/openapi.yaml")
MCP_NAME = os.getenv("MCP_NAME", "brixta-api")
PORT = int(os.getenv("PORT", 8000))
API_AUTH_HEADER = os.getenv("API_AUTH_HEADER")  # optional

async def fetch_spec(client: httpx.AsyncClient, url: str, retries: int = 3) -> Any:
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            log.info("Fetching OpenAPI spec (attempt %d): %s", attempt, url)
            resp = await client.get(url, timeout=30.0)
            log.info("Spec fetch HTTP %d", resp.status_code)
            resp.raise_for_status()
            text = resp.text.strip()
            if not text:
                raise ValueError("Spec body is empty")

            # Try JSON first (in case it's JSON)
            try:
                return resp.json()
            except Exception:
                # Attempt YAML parse
                try:
                    return yaml.safe_load(text)
                except Exception as e_yaml:
                    raise ValueError(f"Failed to parse spec as JSON or YAML: {e_yaml}") from e_yaml

        except Exception as exc:
            last_exc = exc
            log.warning("Failed to fetch/parse spec on attempt %d: %s", attempt, exc)
            await asyncio.sleep(1 * attempt)

    # all retries failed
    raise RuntimeError(f"Unable to fetch/parse spec {url}") from last_exc

async def build_and_run():
    headers = {}
    if API_AUTH_HEADER:
        headers["Authorization"] = API_AUTH_HEADER

    async with httpx.AsyncClient(base_url=API_BASE_URL, headers=headers, timeout=30.0) as client:
        openapi_spec = await fetch_spec(client, SPEC_URL)
        if not isinstance(openapi_spec, dict):
            log.info("OpenAPI spec loaded but is not a dict — checking content: type=%s", type(openapi_spec))
        log.info("OpenAPI spec loaded successfully; building FastMCP")
        mcp = FastMCP.from_openapi(openapi_spec=openapi_spec, client=client, name=MCP_NAME)
        log.info("Starting MCP server on 0.0.0.0:%d", PORT)
        mcp.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    try:
        asyncio.run(build_and_run())
    except Exception as e:
        log.exception("Fatal error while starting MCP: %s", e)
        raise
