# Use the official Python image as a base for a multi-stage build.
FROM python:3.12-slim AS builder

# Set the working directory in the container.
WORKDIR /app

# Install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container.
COPY . .

# Create a clean, final image.
FROM python:3.12-slim

# Set the working directory.
WORKDIR /app

# Copy the installed packages from the builder stage.
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app

# Expose the port the app runs on.
EXPOSE 8000

# Run the uvicorn command to start the application.
CMD ["python", "main.py"]
