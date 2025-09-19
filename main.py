from fastapi import FastAPI
from typing import Dict
import os

# Create the FastAPI application object that FastMCP can run.
app = FastAPI(
    title=os.environ.get("API_NAME", "My API Adapter"),
    description="A server to adapt an API for an MCP agent.",
    version="1.0.0",
)

@app.get("/")
def read_root() -> Dict[str, str]:
    """
    A simple endpoint to confirm the server is running.
    """
    return {"message": "Hello from the FastAPI server!"}

# You can now add your other API endpoints and logic here.
# For example:
# @app.post("/my-data-endpoint")
# async def process_data(data: dict):
#     # ... your logic here
#     return {"status": "success"}