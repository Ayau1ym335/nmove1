# backend/docker/celery.Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install psycopg2 system deps (needed for sync Celery DB access)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "celery_app", "worker", \
     "--loglevel=info", \
     "--queues=gait_processing", \
     "--concurrency=2", \
     "--hostname=nmove-worker@%h"]
