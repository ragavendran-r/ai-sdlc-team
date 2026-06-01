# UX Agent web interface image.
# Build from the repo root:  docker build -f ux_agent_workspace/Dockerfile -t ux-interface .
FROM python:3.11-slim

WORKDIR /app

# Install root + workspace requirements (cached layer).
COPY requirements.txt ./requirements.txt
COPY ux_agent_workspace/agents/requirements.txt ./ux-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r ux-requirements.txt

# Copy the whole repo so team_orchestrator and team_contracts are importable.
COPY . .

WORKDIR /app

ENV PYTHONPATH=/app
ENV CONTEXT_STORE_PATH=/app/team_contracts/context-store
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "ux_agent_workspace.interface.app:app", "--host", "0.0.0.0", "--port", "8000"]
