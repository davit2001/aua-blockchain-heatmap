# ---------- Dockerfile.backend ----------
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY src/scripts/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY src/scripts/app.py ./app.py

# Create internal DB folder (Cloud Run does not allow bind mounts)
RUN mkdir -p /app/db

# Environment variables (Cloud Run will override these)
ENV DB_PATH=/app/db/nodes.db
ENV CORS_ORIGINS=http://localhost:3000,http://localhost:3001
ENV PORT=8000

# Expose port (for local use)
EXPOSE 8000

# Start backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "$PORT"]

