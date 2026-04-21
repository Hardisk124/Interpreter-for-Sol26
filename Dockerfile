# syntax=docker/dockerfile:1
# Dockerfile for SOL26 interpreter and tester project
# Stages: check, build, build-test, runtime, test

# ============================================================================
# Stage: check
# Purpose: Quality control environment for code checking (linting, type checking)
# - Combines Python and Node.js environments
# - Entry point: bash for running quality control tools
# - Bind mounts: /src/int (interpreter), /src/tester (TS tester)
# ============================================================================
FROM python:3.14-slim AS check

# Install Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Python runtime + dev tools (mypy plugins depend on runtime packages like pydantic)
COPY int/requirements.txt /tmp/python-requirements.txt
COPY int/requirements-dev.txt /tmp/python-dev-requirements.txt
RUN pip install --no-cache-dir -r /tmp/python-requirements.txt -r /tmp/python-dev-requirements.txt

# Install Node.js dev tools globally
RUN npm install -g eslint prettier typescript

# Set working directory
WORKDIR /src

# Default entry point for interactive shell
ENTRYPOINT ["/bin/bash"]


# ============================================================================
# Stage: build
# Purpose: Prepare Python interpreter for runtime
# - For Python, this stage primarily sets up the environment
# - Installs runtime dependencies that will be copied to runtime stage
# ============================================================================
FROM python:3.14-slim AS build

# Install runtime dependencies
COPY int/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --target /app/dist-packages -r /tmp/requirements.txt

# Copy interpreter project tree 
COPY int /app/int

# Ensure package root is part of Python path
ENV PYTHONPATH="/app:/app/dist-packages"

WORKDIR /app


# ============================================================================
# Stage: build-test
# Purpose: Build TypeScript tester
# - Installs dependencies with npm
# - Compiles TypeScript to JavaScript (to dist/)
# - Only this compiled output will be copied to runtime
# ============================================================================
FROM node:24.12.0-alpine AS build-test

WORKDIR /app

# Copy TypeScript tester source
COPY tester .

# Install dependencies (including devDependencies)
RUN npm ci

# Build TypeScript to JavaScript
RUN npm run build

# Remove dev dependencies, keeping only production dependencies
RUN npm prune --production


# ============================================================================
# Stage: runtime
# Purpose: Minimal production image for running the interpreter
# - Contains only the interpreter code and runtime dependencies
# - No development tools, compilers, or source code from build stage
# - Runs the Python interpreter entry point
# ============================================================================
FROM python:3.14-slim AS runtime

WORKDIR /app

# Copy runtime dependencies and source from build stage
COPY --from=build /app/dist-packages /app/dist-packages
COPY --from=build /app/int /app/int

# Set Python path to include installed packages
ENV PYTHONPATH="/app:/app/dist-packages"

# Ensure text output is not buffered
ENV PYTHONUNBUFFERED=1

# Entry point: run the Python interpreter; docker run args are forwarded to solint.py
ENTRYPOINT ["python3", "/app/int/src/solint.py"]


# ============================================================================
# Stage: test
# Purpose: Integration testing stage
# - Extends from runtime stage (includes interpreter)
# - Adds compiled TypeScript tester from build-test stage
# - Provides tools for running integration tests
# ============================================================================
FROM runtime AS test

# Install Node.js runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install system dependencies needed to build lxml on Python 3.14
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    diffutils \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Install parser runtime dependencies (for parser scripts executed by tester)
RUN pip install --no-cache-dir \
    lark==1.2.2 \
    lxml~=5.3.2

# Create directory for tester
WORKDIR /app/tester

# Copy compiled TypeScript files from build-test stage
COPY --from=build-test /app/dist ./
# Copy node_modules with only production dependencies (dev dependencies removed by npm prune)
COPY --from=build-test /app/node_modules node_modules/
# Copy parser script and expose it as `sol2xml` command for tester runner
COPY --from=build-test /app/sol2xml/sol_to_xml.py /usr/local/bin/sol2xml

# Provide expected executable names used by tester's default config
RUN chmod +x /usr/local/bin/sol2xml && \
    printf '%s\n' '#!/bin/sh' 'exec python3 /app/int/src/solint.py "$@"' > /usr/local/bin/interpreter && \
    chmod +x /usr/local/bin/interpreter

# Ensure interpreter is still accessible
ENV PYTHONPATH="/app:/app/dist-packages"
ENV SOL2XML_PATH="/usr/local/bin/sol2xml"
ENV INTERPRETER_PATH="/usr/local/bin/interpreter"

# Entry point: run the TypeScript tester; docker run args are forwarded to tester.js
ENTRYPOINT ["node", "./tester.js"]
