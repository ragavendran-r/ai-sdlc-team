FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt .
COPY po-agent-workspace/agents/requirements.txt ./po-requirements.txt
COPY em-agent-workspace/agents/requirements.txt ./em-requirements.txt
COPY ux-agent-workspace/agents/requirements.txt ./ux-requirements.txt
COPY backend-agent-workspace/agents/requirements.txt ./backend-requirements.txt
COPY frontend-agent-workspace/agents/requirements.txt ./frontend-requirements.txt
COPY team_orchestrator/requirements.txt ./orchestrator-requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -r po-requirements.txt && \
    pip install -r em-requirements.txt && \
    pip install -r ux-requirements.txt && \
    pip install -r backend-requirements.txt && \
    pip install -r frontend-requirements.txt && \
    pip install -r orchestrator-requirements.txt && \
    pip install uvicorn fastapi psycopg2-binary redis

# Copy project code
COPY . .

# Create directories for artifacts
RUN mkdir -p ai_sdlc_work team-contracts/context-store

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "team_orchestrator"]
