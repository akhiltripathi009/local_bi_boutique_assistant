# ==============================================================================
# Mishika Fashion Luxury Boutique - Production Cloud Container
# Target Platform: Google Cloud Run / Container Hosting
# ==============================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal OS dependencies for ReportLab PDF compilation and SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and assets
COPY . .

# Cloud Run injects $PORT (default 8080 or 8000)
ENV PORT=8000
EXPOSE 8000

# Launch production SaaS server
CMD ["python", "run_saas.py"]
