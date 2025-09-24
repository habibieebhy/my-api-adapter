import httpx
from fastmcp import FastMCP

# FIX 1: Remove Markdown from the base_url
client = httpx.AsyncClient(base_url="https://myserverbymycoco.onrender.com")

# Load your OpenAPI spec
try:
    # FIX 2: Remove Markdown from the get request URL
    response = httpx.get("https://myserverbymycoco.onrender.com/openapi.json")
    response.encoding = 'utf-8' # Force the response to be decoded as UTF-8
    openapi_spec = response.json()
    print("✅ Successfully fetched and decoded OpenAPI spec.")
except httpx.HTTPStatusError as e:
    print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
    exit()
except Exception as e:
    print(f"❌ An error occurred while fetching or parsing the OpenAPI spec: {e}")
    exit()

# Create the MCP server
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="My API Server"
)

if __name__ == "__main__":
    mcp.run()