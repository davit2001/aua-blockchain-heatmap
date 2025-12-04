FROM python:3.11-slim

WORKDIR /app

# Install system updates (optional but recommended)
RUN apt-get update && apt-get install -y build-essential

# Create a virtual environment INSIDE the container
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy requirements first (load dependency cache)
COPY src/scripts/requirements.txt .

# Install Python dependencies inside the container venv
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY src/scripts/*.py /app/
COPY src/db /app/db

RUN mkdir -p /app/db && chmod -R 777 /app/db

# IMPORTANT: Run uvicorn from the venv inside Docker
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
