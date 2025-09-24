import httpx
from fastmcp import FastMCP

# Create an HTTP client for your API
client = httpx.AsyncClient(base_url="[https://myserverbymycoco.onrender.com](https://myserverbymycoco.onrender.com)")

# Load your OpenAPI spec
# FIX: Explicitly set the encoding to UTF-8 to prevent decoding errors
try:
    response = httpx.get("[https://myserverbymycoco.onrender.com/openapi.json](https://myserverbymycoco.onrender.com/openapi.json)")
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