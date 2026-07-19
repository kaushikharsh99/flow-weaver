FROM python:3.12-slim

WORKDIR /workspace

# Install compiler building utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy local packages and backend workspace code
COPY packages/flowweaver_sdk /workspace/packages/flowweaver_sdk
COPY apps/api /workspace/apps/api

# Install SDK and api packages
RUN pip install --no-cache-dir -e /workspace/packages/flowweaver_sdk
RUN pip install --no-cache-dir -r /workspace/apps/api/requirements.txt

WORKDIR /workspace/apps/api

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["python", "main.py"]
