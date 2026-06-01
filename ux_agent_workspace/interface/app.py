"""FastAPI web interface for the UX Agent workflow.

A designer takes the Engineering Manager's published sprint plan, runs the
LangGraph UX pipeline, reviews personas / user flows / wireframe briefs across
three tabs in the browser, and on approval publishes a UX handoff to the shared
context store for the downstream Frontend workspace.
"""

import csv
import io
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
from .session import PROGRESS_STEPS, UXSessionState, sessions

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="UX Workspace")
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


def _read_sprint_plan() -> Optional[Dict[str, Any]]:
    """Read the EM-published sprint plan artifact, or None if not yet published."""
    return context_store.read_artifact("sprint-plan")


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
    sprint_plan = _read_sprint_plan()
    handoff = context_store.read_artifact("ux-handoff")

    awaiting = [s for s in sessions.values() if s.status == "awaiting_review"]

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "title": "UX Workspace",
            "sessions": sorted(
                sessions.values(), key=lambda s: s.created_at, reverse=True
            ),
            "awaiting": awaiting,
            "sprint_ready": sprint_plan is not None,
            "handoff_published": handoff is not None,
        },
    )


# ---------------------------------------------------------------------------
# Route 2: New session form
# ---------------------------------------------------------------------------


@app.get("/sessions/new", response_class=HTMLResponse)
def session_new(request: Request) -> HTMLResponse:
    sprint_plan = _read_sprint_plan()
    return templates.TemplateResponse(
        request,
        "session_new.html",
        {
            "title": "New design session",
            "sprint_ready": sprint_plan is not None,
        },
    )


# ---------------------------------------------------------------------------
# Route 3: Run a session
# ---------------------------------------------------------------------------


@app.post("/sessions/run")
def sessions_run(session_name: str = Form(...)) -> Response:
    stories = workflow_runner.sprint_plan_stories(_read_sprint_plan())
    session_id = str(uuid.uuid4())
    session = UXSessionState(
        session_id=session_id,
        session_name=session_name[:80],
    )
    sessions[session_id] = session
    workflow_runner.start_session(session, stories)
    return Response(
        status_code=303,
        headers={"Location": f"/sessions/{session_id}/progress"},
    )


# ---------------------------------------------------------------------------
# Route 4: Progress page
# ---------------------------------------------------------------------------


@app.get("/sessions/{session_id}/progress", response_class=HTMLResponse)
def session_progress(request: Request, session_id: str) -> HTMLResponse:
    session = sessions.get(session_id)
    if session is None:
        return _not_found(request)
    return templates.TemplateResponse(
        request,
        "session_progress.html",
        {
            "title": f"Running UX pipeline — {session.session_name}",
            "session": session,
            "steps": PROGRESS_STEPS,
        },
    )


# ---------------------------------------------------------------------------
# Route 5: Status JSON
# ---------------------------------------------------------------------------


@app.get("/sessions/{session_id}/status")
def session_status(session_id: str) -> JSONResponse:
    session = sessions.get(session_id)
    if session is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(session.to_status_dict())


# ---------------------------------------------------------------------------
# Route 6: Review page (3 tabs)
# ---------------------------------------------------------------------------


@app.get("/sessions/{session_id}/review", response_class=HTMLResponse)
def session_review(request: Request, session_id: str) -> HTMLResponse:
    session = sessions.get(session_id)
    if session is None:
        return _not_found(request)
    return templates.TemplateResponse(
        request,
        "session_review.html",
        {
            "title": f"Review UX specs — {session.session_name}",
            "session": session,
            "ready": session.status == "awaiting_review",
        },
    )


# ---------------------------------------------------------------------------
# Route 7: Approve
# ---------------------------------------------------------------------------


@app.post("/sessions/{session_id}/approve")
async def session_approve(session_id: str, request: Request) -> JSONResponse:
    session = sessions.get(session_id)
    if session is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    if session.status != "awaiting_review":
        return JSONResponse(
            {"error": "Session is not awaiting review"}, status_code=400
        )

    workflow_runner.approve(session, context_store, event_bus)
    return JSONResponse(
        {"status": "approved", "redirect": f"/sessions/{session_id}/summary"}
    )


# ---------------------------------------------------------------------------
# Route 8: Reject
# ---------------------------------------------------------------------------


@app.post("/sessions/{session_id}/reject")
async def session_reject(session_id: str, request: Request) -> JSONResponse:
    session = sessions.get(session_id)
    if session is None:
        return JSONResponse({"error": "not found"}, status_code=404)

    body = await request.json()
    feedback = body.get("feedback", "") or ""
    workflow_runner.reject(session, feedback)
    return JSONResponse(
        {
            "status": "rejected",
            "redirect": f"/sessions/{session_id}/progress",
        }
    )


# ---------------------------------------------------------------------------
# Route 9: Summary
# ---------------------------------------------------------------------------


@app.get("/sessions/{session_id}/summary", response_class=HTMLResponse)
def session_summary(request: Request, session_id: str) -> HTMLResponse:
    session = sessions.get(session_id)
    if session is None:
        return _not_found(request)
    return templates.TemplateResponse(
        request,
        "summary.html",
        {
            "title": f"UX handoff — {session.session_name}",
            "session": session,
            "published": session.status == "approved",
        },
    )


# ---------------------------------------------------------------------------
# Route 10: Markdown export
# ---------------------------------------------------------------------------


@app.get("/sessions/{session_id}/export/markdown")
def export_markdown(session_id: str) -> Response:
    session = sessions.get(session_id)
    if session is None:
        return Response(content="Not found", status_code=404)

    lines: List[str] = [f"# UX Handoff — {session.session_name}", ""]
    lines.append("## Personas")
    for p in session.personas:
        lines.append(f"### {p.get('name', '')} ({p.get('role', '')})")
        for goal in p.get("goals", []) or []:
            lines.append(f"- Goal: {goal}")
        lines.append("")
    lines.append("## User flows")
    for f in session.user_flows:
        lines.append(f"### {f.get('title') or f.get('name', '')}")
        lines.append(f.get("description", ""))
        for step in f.get("steps", []) or []:
            if isinstance(step, dict):
                lines.append(f"- {step.get('action', '')}")
            else:
                lines.append(f"- {step}")
        lines.append("")
    lines.append("## Wireframe briefs")
    for w in session.wireframe_briefs:
        lines.append(f"### {w.get('screen_name') or w.get('name', '')}")
        if w.get("purpose"):
            lines.append(f"_{w.get('purpose')}_")
        lines.append(w.get("description") or w.get("layout_description", ""))
        for c in w.get("components", []) or []:
            if isinstance(c, dict):
                lines.append(f"- {c.get('component_name', '')}")
            else:
                lines.append(f"- {c}")
        lines.append("")

    return Response(
        content="\n".join(lines),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=ux-handoff.md"},
    )


# ---------------------------------------------------------------------------
# Route 11: CSV export (wireframe briefs)
# ---------------------------------------------------------------------------


@app.get("/sessions/{session_id}/export/csv")
def export_csv(session_id: str) -> Response:
    session = sessions.get(session_id)
    if session is None:
        return Response(content="Not found", status_code=404)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "screen_name", "layout_type", "user_flow_id", "purpose"])
    for w in session.wireframe_briefs:
        writer.writerow(
            [
                w.get("id", ""),
                w.get("screen_name") or w.get("name", ""),
                w.get("layout_type") or w.get("screen_type", ""),
                w.get("user_flow_id") or w.get("story_id", ""),
                w.get("purpose") or w.get("layout_description", ""),
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=wireframe-briefs.csv"},
    )
