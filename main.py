import os
from awslabs.openapi_mcp_server.server import Server

# The deployment platform will look for this 'app' variable.
# The class is named 'Server', not 'OpenApiMcpServer'.
app = Server(
    # These values are read from the environment variables you set in the FastMCP UI.
    api_name=os.environ.get("API_NAME", "my-api"),
    api_url=os.environ.get("API_BASE_URL", "https://myserverbymycoco.onrender.com"),
    spec_url=os.environ.get("API_SPEC_URL", "https://myserverbymycoco.onrender.com/openapi.yaml"),
)