import httpx
from fastmcp import FastMCP

# Create an HTTP client for your API
client = httpx.AsyncClient(base_url="https://myserverbymycoco.onrender.com")

# Load your OpenAPI spec 
openapi_spec = httpx.get("https://myserverbymycoco.onrender.com/openapi.yaml").json()

# Create the MCP server
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="My API Server"
)

if __name__ == "__main__":
    mcp.run()