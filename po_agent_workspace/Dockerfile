FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (root deps cover langchain/langgraph/web stack).
COPY requirements.txt ./root-requirements.txt
COPY po_agent_workspace/agents/requirements.txt ./po-requirements.txt
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r root-requirements.txt && \
    pip install -r po-requirements.txt

# Copy the whole repo so team_orchestrator and team_contracts are importable.
COPY . .

# Run from the PO workspace so `interface.app:app` and `agents.*` resolve.
WORKDIR /app/po_agent_workspace

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "interface.app:app", "--host", "0.0.0.0", "--port", "8000"]
