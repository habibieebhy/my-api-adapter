# Dockerfile (Corrected)
FROM python:3.12-slim

WORKDIR /app

RUN pip install "awslabs.openapi-mcp-server"

EXPOSE 8000

# FIX: Use the "shell form" of CMD to allow environment variable substitution
CMD awslabs.openapi-mcp-server --api-name "$API_NAME" --api-url "$API_URL" --spec-url "$API_SPEC_URL"