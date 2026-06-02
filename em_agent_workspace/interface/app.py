"""FastAPI web interface for the EM Agent workflow.

An Engineering Manager takes the Product Owner's published backlog, runs the
LangGraph sprint-planning pipeline, reviews the draft sprint (tasks, capacity,
risks) in the browser, and on approval publishes a sprint plan to the shared
context store for the downstream Frontend/Backend/UX workspaces.
"""

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from team_orchestrator import ContextStore, EventBus

from . import workflow_runner
from .session import PROGRESS_STEPS, EMSessionState, sessions

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="EM Workspace")
app.mount("/static", StaticFiles(directory=str(_BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(_BASE_DIR / "templates"))

# Single context store + event bus for this process. The context store path is
# the shared on-disk location used for cross-workspace handoff.
context_store = ContextStore(
    base_path=os.getenv("CONTEXT_STORE_PATH", "team_contracts/context-store")
)
event_bus = EventBus()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_backlog() -> Optional[Dict[str, Any]]:
    """Read the PO-published backlog artifact, or None if not yet published."""
    return context_store.read_artifact("backlog")


def _backlog_stories(backlog: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not backlog:
        return []
    return backlog.get("stories", []) or []


def _sprint_tasks(sprint_plan: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not sprint_plan:
        return []
    return (sprint_plan.get("sprint") or {}).get("tasks", []) or []


def _not_found(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "not_found.html",
        {"title": "Not found"},
        status_code=404,
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Route 1: Home
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    backlog = _read_backlog()
    sprint_plan = context_store.read_artifact("sprint-plan")

    awaiting = [s for s in sessions.values() if s.status == "awaiting_review"]

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "title": "EM Workspace",
            "sessions": sorted(
                sessions.values(), key=lambda s: s.created_at, reverse=True
            ),
            "awaiting": awaiting,
            "backlog_ready": backlog is not None,
            "backlog_count": len(_backlog_stories(backlog)),
            "sprint_plan": sprint_plan,
            "sprint_task_count": len(_sprint_tasks(sprint_plan)),
        },
    )


# ---------------------------------------------------------------------------
# Route 2: New sprint form
# ---------------------------------------------------------------------------


@app.get("/sprint/plan", response_class=HTMLResponse)
def sprint_plan_form(request: Request) -> HTMLResponse:
    backlog = _read_backlog()
    return templates.TemplateResponse(
        request,
        "sprint_plan.html",
        {
            "title": "Plan a sprint",
            "backlog_ready": backlog is not None,
            "backlog_count": len(_backlog_stories(backlog)),
        },
    )


# ---------------------------------------------------------------------------
# Route 3: Run a sprint-planning session
# ---------------------------------------------------------------------------


@app.post("/sprint/run")
def sprint_run(
    session_name: str = Form(...),
    sprint_goal: str = Form(""),
) -> Response:
    stories = _backlog_stories(_read_backlog())
    session_id = str(uuid.uuid4())
    session = EMSessionState(
        session_id=session_id,
        session_name=session_name[:80],
        sprint_goal=sprint_goal,
    )
    sessions[session_id] = session
    workflow_runner.start_session(session, stories)
    return Response(
        status_code=303,
        headers={"Location": f"/sprint/{session_id}/progress"},
    )


# ---------------------------------------------------------------------------
# Route 4: Progress page
# ---------------------------------------------------------------------------


@app.get("/sprint/{session_id}/progress", response_class=HTMLResponse)
def sprint_progress(request: Request, session_id: str) -> HTMLResponse:
    session = sessions.get(session_id)
    if session is None:
        return _not_found(request)
    return templates.TemplateResponse(
        request,
        "sprint_progress.html",
        {
            "title": f"Planning sprint — {session.session_name}",
            "session": session,
            "steps": PROGRESS_STEPS,
        },
    )


# ---------------------------------------------------------------------------
# Route 5: Status JSON
# ---------------------------------------------------------------------------


@app.get("/sprint/{session_id}/status")
def sprint_status(session_id: str) -> JSONResponse:
    session = sessions.get(session_id)
    if session is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(session.to_status_dict())


# ---------------------------------------------------------------------------
# Route 6: Review page
# ---------------------------------------------------------------------------


@app.get("/sprint/{session_id}/review", response_class=HTMLResponse)
def sprint_review(request: Request, session_id: str) -> HTMLResponse:
    session = sessions.get(session_id)
    if session is None:
        return _not_found(request)
    return templates.TemplateResponse(
        request,
        "sprint_review.html",
        {
            "title": f"Review draft sprint — {session.session_name}",
            "session": session,
            "ready": session.status == "awaiting_review",
            "tasks": _sprint_tasks(session.draft_sprint),
        },
    )


# ---------------------------------------------------------------------------
# Route 7: Approve
# ---------------------------------------------------------------------------


@app.post("/sprint/{session_id}/approve")
async def sprint_approve(session_id: str, request: Request) -> JSONResponse:
    session = sessions.get(session_id)
    if session is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    if session.status != "awaiting_review":
        return JSONResponse({"error": "Sprint is not awaiting review"}, status_code=400)

    try:
        workflow_runner.approve(session, context_store, event_bus)
    except Exception as exc:
        session.status = "error"
        session.error = str(exc)
        return JSONResponse({"error": str(exc)}, status_code=500)
    return JSONResponse({"status": "approved", "redirect": "/sprint/dashboard"})


# ---------------------------------------------------------------------------
# Route 8: Reject
# ---------------------------------------------------------------------------


@app.post("/sprint/{session_id}/reject")
async def sprint_reject(session_id: str, request: Request) -> JSONResponse:
    session = sessions.get(session_id)
    if session is None:
        return JSONResponse({"error": "not found"}, status_code=404)

    body = await request.json()
    feedback = body.get("feedback", "") or ""
    workflow_runner.reject(session, feedback)
    return JSONResponse(
        {
            "status": "rejected",
            "redirect": f"/sprint/{session_id}/progress",
        }
    )


# ---------------------------------------------------------------------------
# Route 9: Dashboard
# ---------------------------------------------------------------------------


@app.get("/sprint/dashboard", response_class=HTMLResponse)
def sprint_dashboard(request: Request) -> HTMLResponse:
    sprint_plan = context_store.read_artifact("sprint-plan")
    tasks = _sprint_tasks(sprint_plan)
    report = context_store.read_artifact("sprint-report")

    total_hours = sum(int(t.get("estimated_hours") or 0) for t in tasks)
    by_type: Dict[str, int] = {}
    for task in tasks:
        ttype = task.get("task_type") or "other"
        by_type[ttype] = by_type.get(ttype, 0) + 1

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "title": "Sprint dashboard",
            "has_sprint": sprint_plan is not None,
            "sprint": (sprint_plan or {}).get("sprint") or {},
            "tasks": tasks,
            "total_hours": total_hours,
            "by_type": by_type,
            "report": (report or {}).get("report", ""),
        },
    )


# ---------------------------------------------------------------------------
# Route 10: Regenerate report
# ---------------------------------------------------------------------------


@app.post("/sprint/report/regenerate")
def sprint_report_regenerate() -> JSONResponse:
    if context_store.read_artifact("sprint-plan") is None:
        return JSONResponse({"error": "No sprint plan published"}, status_code=400)
    workflow_runner.regenerate_report(context_store)
    return JSONResponse({"status": "regenerated", "redirect": "/sprint/dashboard"})


# ---------------------------------------------------------------------------
# Route 11: Download report
# ---------------------------------------------------------------------------


@app.get("/sprint/report/download")
def sprint_report_download() -> Response:
    report = context_store.read_artifact("sprint-report") or {}
    content = report.get("report", "# Sprint Report\n\nNo report generated yet.")
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=sprint-report.md"},
    )
