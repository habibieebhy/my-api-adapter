import os
import sys
import subprocess

def main():
    """
    This script is the main entrypoint for the deployment.
    It reads configuration from environment variables and then launches
    the awslabs.openapi-mcp-server application.
    """
    print("--- Launching MCP Server from main.py entrypoint ---")

    # Read the required configuration from environment variables
    # These MUST be set in your FastMCP Cloud dashboard
    api_name = os.environ.get("API_NAME")
    api_base_url = os.environ.get("API_BASE_URL")
    api_spec_url = os.environ.get("API_SPEC_URL")

    # Check if the required variables are present
    if not all([api_name, api_base_url, api_spec_url]):
        print(
            "FATAL ERROR: Missing required environment variables (API_NAME, API_BASE_URL, API_SPEC_URL).",
            file=sys.stderr
        )
        sys.exit(1) # Exit with an error code

    # This is the command that will be executed.
    # It's the same one you ran locally, but built from environment variables.
    command = [
        "awslabs.openapi-mcp-server",
        "--api-name", api_name,
        "--api-url", api_base_url,
        "--spec-url", api_spec_url,
        "--log-level", os.environ.get("LOG_LEVEL", "INFO")
    ]

    print(f"Executing command: {' '.join(command)}")

    # Use subprocess.run to execute the real server command
    try:
        # This starts the server and waits for it to finish
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print(f"FATAL ERROR: The command 'awslabs.openapi-mcp-server' was not found.", file=sys.stderr)
        print("This means the package is not installed correctly in the deployment environment.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"The MCP server exited with an error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()