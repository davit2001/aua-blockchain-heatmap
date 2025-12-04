FROM python:3.11-slim

WORKDIR /app

# Install backend dependencies
COPY src/scripts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your actual backend code
COPY src/scripts /app

# Copy ONLY the real database folder
COPY src/db /app/db

# Make DB writable
RUN mkdir -p /app/db && chmod -R 777 /app/db

ENV DB_PATH=/app/db/nodes.db

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
