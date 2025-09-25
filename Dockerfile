# Use the official Python image as a base for our application.
FROM python:3.12-slim

# Set the working directory in the container.
WORKDIR /app

# Install the MCP server package.
RUN pip install --no-cache-dir "awslabs.openapi-mcp-server"

# Expose the port the app runs on.
EXPOSE 8000

# Use the "shell form" of CMD to allow environment variable substitution.
# This command runs the MCP server directly, using environment variables
# for configuration.
CMD ["awslabs.openapi-mcp-server", "--api-name", "$API_NAME", "--api-url", "$API_BASE_URL", "-spec-url", "$API_SPEC_URL"]
