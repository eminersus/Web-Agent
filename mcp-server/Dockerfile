FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY server.py .

# Expose port for HTTP transport (if needed)
EXPOSE 8001

# Run the MCP server
CMD ["python", "-u", "server.py"]

