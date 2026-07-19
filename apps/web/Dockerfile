FROM node:20-slim

WORKDIR /workspace

# Install build utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy monorepo workspace configurations
COPY package.json package-lock.json tsconfig.json /workspace/
COPY apps/web/package.json /workspace/apps/web/

# Install workspace npm modules
RUN npm ci

# Copy frontend source files
COPY apps/web /workspace/apps/web

WORKDIR /workspace/apps/web

ENV HOST=0.0.0.0
ENV PORT=8080
EXPOSE 8080

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8080"]
