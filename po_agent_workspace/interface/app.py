"""FastAPI web interface for the PO Agent workflow.

A non-technical Product Owner can paste raw requirements, watch the LangGraph
pipeline run, review generated stories, edit/approve/reject them, and publish a
backlog to the shared context store. See interface/README is the workspace
README; this module wires routes to the workflow runner and context store.
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
from .session import PROGRESS_STEPS, SessionState, sessions

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="PO Workspace")
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
    """Read the published backlog artifact, or None if not yet published."""
    return context_store.read_artifact("backlog")


def _backlog_stories(backlog: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not backlog:
        return []
    return backlog.get("stories", []) or []


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
    sprint = context_store.read_artifact("sprint-plan")

    awaiting = [s for s in sessions.values() if s.status == "awaiting_review"]

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "title": "PO Workspace",
            "sessions": sorted(
                sessions.values(), key=lambda s: s.created_at, reverse=True
            ),
            "awaiting": awaiting,
            "backlog": backlog,
            "backlog_count": len(_backlog_stories(backlog)),
            "sprint": sprint,
        },
    )


# ---------------------------------------------------------------------------
# Route 2: New session form
# ---------------------------------------------------------------------------


@app.get("/sessions/new", response_class=HTMLResponse)
def session_new(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "session_new.html",
        {"title": "New requirements session"},
    )


# ---------------------------------------------------------------------------
# Route 3: Run a session
# ---------------------------------------------------------------------------


@app.post("/sessions/run")
def sessions_run(
    session_name: str = Form(...),
    source_type: str = Form(...),
    raw_input: str = Form(...),
) -> Response:
    session_id = str(uuid.uuid4())
    session = SessionState(
        session_id=session_id,
        session_name=session_name[:80],
        source_type=source_type,
        raw_input=raw_input,
    )
    sessions[session_id] = session
    workflow_runner.start_session(session)
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
            "title": f"Running pipeline — {session.session_name}",
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
# Route 6: Review page
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
            "title": f"Review generated stories — {session.session_name}",
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

    body = await request.json()
    approved_stories = body.get("approved_stories", []) or []
    if not approved_stories:
        return JSONResponse(
            {"error": "At least one story must be approved"}, status_code=400
        )

    workflow_runner.approve(session, approved_stories, context_store, event_bus)
    return JSONResponse({"status": "approved", "redirect": "/backlog"})


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
# Route 9: Backlog
# ---------------------------------------------------------------------------


@app.get("/backlog", response_class=HTMLResponse)
def backlog_page(request: Request) -> HTMLResponse:
    backlog = _read_backlog()
    stories = _backlog_stories(backlog)

    # Group stories by theme for display.
    by_theme: Dict[str, List[Dict[str, Any]]] = {}
    total_points = 0
    priority_counts: Dict[str, int] = {}
    for story in stories:
        theme = story.get("theme") or "Uncategorized"
        by_theme.setdefault(theme, []).append(story)
        total_points += int(story.get("story_points") or 0)
        priority = (story.get("priority") or "unset").lower()
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    return templates.TemplateResponse(
        request,
        "backlog.html",
        {
            "title": "Product backlog",
            "has_backlog": backlog is not None,
            "by_theme": by_theme,
            "total_stories": len(stories),
            "total_points": total_points,
            "priority_counts": priority_counts,
        },
    )


# ---------------------------------------------------------------------------
# Route 10: CSV export
# ---------------------------------------------------------------------------


@app.get("/backlog/export/csv")
def backlog_csv() -> Response:
    stories = _backlog_stories(_read_backlog())
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "title",
            "description",
            "given",
            "when",
            "then",
            "priority",
            "story_points",
            "theme",
        ]
    )
    for story in stories:
        given, when, then = _split_acceptance(story)
        writer.writerow(
            [
                story.get("id", ""),
                story.get("title", ""),
                story.get("description", ""),
                given,
                when,
                then,
                story.get("priority", ""),
                story.get("story_points", ""),
                story.get("theme", ""),
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=backlog.csv"},
    )


# ---------------------------------------------------------------------------
# Route 11: Markdown export
# ---------------------------------------------------------------------------


@app.get("/backlog/export/markdown")
def backlog_markdown() -> Response:
    stories = _backlog_stories(_read_backlog())
    by_theme: Dict[str, List[Dict[str, Any]]] = {}
    for story in stories:
        theme = story.get("theme") or "Uncategorized"
        by_theme.setdefault(theme, []).append(story)

    lines: List[str] = ["# Product Backlog", ""]
    for theme, theme_stories in by_theme.items():
        lines.append(f"## {theme}")
        lines.append("")
        for story in theme_stories:
            lines.append(f"### {story.get('id', '')} — {story.get('title', '')}")
            lines.append("")
            if story.get("description"):
                lines.append(story["description"])
                lines.append("")
            given, when, then = _split_acceptance(story)
            lines.append("| Given | When | Then |")
            lines.append("| --- | --- | --- |")
            lines.append(f"| {given} | {when} | {then} |")
            lines.append("")
    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=backlog.md"},
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _split_acceptance(story: Dict[str, Any]) -> tuple:
    """Best-effort split of acceptance criteria into Given/When/Then columns."""
    criteria = story.get("acceptance_criteria") or []
    if isinstance(criteria, list):
        joined = "; ".join(str(c) for c in criteria)
    else:
        joined = str(criteria)
    return joined, "", ""


def _not_found(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "not_found.html",
        {"title": "Not found"},
        status_code=404,
    )
