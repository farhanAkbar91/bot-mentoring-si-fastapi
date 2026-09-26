FROM python:3.11-slim

WORKDIR /app

# Install build dependencies to prevent any build failures
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose default port (Render will override this with its own PORT env var, which our config reads)
EXPOSE 8080

# Run the FastAPI application
CMD ["python", "-m", "app.main"]
