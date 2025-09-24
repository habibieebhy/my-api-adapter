import httpx
from fastmcp import FastMCP
import os
import sys

API_BASE_URL = os.getenv("API_BASE_URL", "https://myserverbymycoco.onrender.com")
API_SPEC_URL = os.getenv("API_SPEC_URL", f"{API_BASE_URL}/openapi.json")

# Create an HTTP client for your API
client = httpx.AsyncClient(base_url=API_BASE_URL)

# Load your OpenAPI spec 
openapi_spec = httpx.get(API_SPEC_URL).json()

# Create the MCP server
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="My API Server"
)

if __name__ == "__main__":
    mcp.run()