# EM Agent web interface image.
# Build from the repo root:  docker build -f em_agent_workspace/Dockerfile -t em-interface .
FROM python:3.11-slim

WORKDIR /app

# Install root + workspace requirements (cached layer).
COPY requirements.txt ./requirements.txt
COPY em_agent_workspace/agents/requirements.txt ./em-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r em-requirements.txt

# Copy the whole repo so team_orchestrator and team_contracts are importable.
COPY . .

WORKDIR /app/em_agent_workspace

ENV PYTHONPATH=/app:/app/em_agent_workspace
ENV CONTEXT_STORE_PATH=/app/team_contracts/context-store
ENV PORT=8000

EXPOSE 8000

# Healthcheck hits the FastAPI /health route.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "interface.app:app", "--host", "0.0.0.0", "--port", "8000"]
