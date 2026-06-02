"""FastAPI web interface for the Frontend Agent workflow.

A developer takes the UX handoff published by the UX workspace, runs the LangGraph
Frontend pipeline, reviews scaffolded components / accessibility / tests / state plan
across tabs in the browser, and on approval completes the PR description and code review.
"""

import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from team_orchestrator import ContextStore, EventBus

from . import workflow_runner
from .session import PROGRESS_STEPS, FrontendSessionState, sessions

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Frontend Workspace")
app.mount("/static", StaticFiles(directory=str(_BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(_BASE_DIR / "templates"))

# Single context store + event bus for this process.
context_store = ContextStore(
    base_path=os.getenv("CONTEXT_STORE_PATH", "team_contracts/context-store")
)
event_bus = EventBus()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_ux_handoff() -> Optional[Dict[str, Any]]:
    """Read the UX-published handoff artifact, or None if not yet published."""
    return context_store.read_artifact("ux-handoff")


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
    handoff = _read_ux_handoff()
    awaiting = [s for s in sessions.values() if s.status == "awaiting_review"]

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "title": "Frontend Workspace",
            "sessions": sorted(
                sessions.values(), key=lambda s: s.created_at, reverse=True
            ),
            "awaiting": awaiting,
            "handoff_ready": handoff is not None,
        },
    )


# ---------------------------------------------------------------------------
# Route 2: New session form
# ---------------------------------------------------------------------------


@app.get("/sessions/new", response_class=HTMLResponse)
def session_new(request: Request) -> HTMLResponse:
    handoff = _read_ux_handoff()
    handoff_data = handoff or {}

    persona_count = len(handoff_data.get("personas") or [])
    screen_count = len(handoff_data.get("wireframe_briefs") or [])
    flow_count = len(handoff_data.get("user_flows") or [])

    return templates.TemplateResponse(
        request,
        "session_new.html",
        {
            "title": "New implementation session",
            "handoff_ready": handoff is not None,
            "persona_count": persona_count,
            "screen_count": screen_count,
            "flow_count": flow_count,
            "session_name_hint": handoff_data.get("session_name", ""),
        },
    )


# ---------------------------------------------------------------------------
# Route 3: Run a session
# ---------------------------------------------------------------------------


@app.post("/sessions/run")
def sessions_run(session_name: str = Form(...)) -> Response:
    handoff = _read_ux_handoff()
    session_id = str(uuid.uuid4())
    session = FrontendSessionState(
        session_id=session_id,
        session_name=session_name[:80],
    )
    sessions[session_id] = session
    workflow_runner.start_session(session, handoff or {})
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
            "title": f"Running Frontend pipeline — {session.session_name}",
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
            "title": f"Review implementation — {session.session_name}",
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
    try:
        await run_in_threadpool(workflow_runner.approve, session, context_store, event_bus)
    except Exception as exc:
        session.status = "error"
        session.error = str(exc)
        return JSONResponse({"error": str(exc)}, status_code=500)
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
            "title": f"Frontend output — {session.session_name}",
            "session": session,
            "published": session.status == "approved",
        },
    )
