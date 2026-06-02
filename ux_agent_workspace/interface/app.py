"""FastAPI web interface for the UX Agent workflow.

A designer takes the Engineering Manager's published sprint plan, runs the
LangGraph UX pipeline, reviews personas / user flows / wireframe briefs across
three tabs in the browser, and on approval publishes a UX handoff to the shared
context store for the downstream Frontend workspace.
"""

import base64
import csv
import io
import json
import os
import subprocess
import sys
import textwrap
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from team_orchestrator import ContextStore, EventBus

from . import workflow_runner
from .session import (
    PROGRESS_STEPS,
    UXSessionState,
    configure_persistence,
    get_session,
    load_all_from_disk,
    persist,
    sessions,
)

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

# Enable disk persistence so sessions survive server restarts.
configure_persistence(str(_BASE_DIR / "_sessions"))
load_all_from_disk()


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
    persist(session)
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
    session = get_session(session_id)
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
    session = get_session(session_id)
    if session is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(session.to_status_dict())


@app.get("/sessions/{session_id}/debug")
def session_debug(session_id: str) -> JSONResponse:
    session = get_session(session_id)
    if session is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    import json
    payload = {
        "status": session.status,
        "personas_count": len(session.personas),
        "flows_count": len(session.user_flows),
        "wireframes_count": len(session.wireframe_briefs),
        "persona_keys": list(session.personas[0].keys()) if session.personas else [],
        "flow_keys": list(session.user_flows[0].keys()) if session.user_flows else [],
        "wireframe_keys": list(session.wireframe_briefs[0].keys()) if session.wireframe_briefs else [],
        "flow_sample": session.user_flows[0] if session.user_flows else None,
        "wireframe_sample": session.wireframe_briefs[0] if session.wireframe_briefs else None,
    }
    return Response(content=json.dumps(payload, default=str), media_type="application/json")


# ---------------------------------------------------------------------------
# Route 6: Review page (3 tabs)
# ---------------------------------------------------------------------------


@app.get("/sessions/{session_id}/review", response_class=HTMLResponse)
def session_review(request: Request, session_id: str) -> HTMLResponse:
    session = get_session(session_id)
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
    session = get_session(session_id)
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
    session = get_session(session_id)
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
    session = get_session(session_id)
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
    session = get_session(session_id)
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
    session = get_session(session_id)
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


# ---------------------------------------------------------------------------
# Route 12: PNG export — screenshot of the rendered design preview screens
# ---------------------------------------------------------------------------


def _playwright_python() -> str:
    """Return a Python interpreter that has playwright installed.

    Checks the project .venv first (the canonical location after
    `pip install playwright`), then falls back to sys.executable.
    Raises RuntimeError with setup instructions if neither has it.
    """
    repo_root = _BASE_DIR.parent.parent
    candidates = [
        repo_root / ".venv" / "bin" / "python",
        repo_root / "venv" / "bin" / "python",
        Path(sys.executable),
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        result = subprocess.run(
            [str(candidate), "-c", "import playwright"],
            capture_output=True,
        )
        if result.returncode == 0:
            return str(candidate)
    raise RuntimeError(
        "playwright not found. Install it with:\n"
        "  .venv/bin/pip install playwright\n"
        "  .venv/bin/python -m playwright install chromium"
    )


def _capture_screens_png(summary_url: str) -> bytes:
    """Screenshot every .preview-canvas on the summary page and stitch them
    into one tall PNG.  Runs playwright in the venv Python via subprocess so
    the correct packages are available regardless of which interpreter started
    the server."""
    py_bin = _playwright_python()

    # The subprocess screenshots each canvas, encodes as base64 JSON, and
    # writes to stdout so we can stitch in the main process.
    script = textwrap.dedent(f"""
        import sys, base64, json
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={{"width": 1200, "height": 900}})
            page.goto({repr(summary_url)})
            page.wait_for_load_state("networkidle")
            canvases = page.query_selector_all(".preview-canvas")
            if not canvases:
                browser.close()
                sys.stderr.write("No .preview-canvas elements found")
                sys.exit(1)
            bufs = [base64.b64encode(el.screenshot()).decode() for el in canvases]
            browser.close()
        print(json.dumps(bufs))
    """)

    result = subprocess.run(
        [py_bin, "-c", script],
        capture_output=True,
        timeout=60,
    )
    if result.returncode != 0:
        err = result.stderr.decode(errors="replace")[:500]
        raise RuntimeError(err)

    buffers = [base64.b64decode(b) for b in json.loads(result.stdout)]

    if len(buffers) == 1:
        return buffers[0]

    # Stitch vertically with Pillow (installed alongside playwright in the venv).
    try:
        from PIL import Image

        gap = 24
        images = [Image.open(io.BytesIO(b)) for b in buffers]
        total_h = sum(img.height for img in images) + gap * (len(images) - 1)
        max_w = max(img.width for img in images)
        canvas = Image.new("RGB", (max_w, total_h), (242, 244, 246))
        y = 0
        for img in images:
            canvas.paste(img, (0, y))
            y += img.height + gap
        out = io.BytesIO()
        canvas.save(out, format="PNG")
        return out.getvalue()
    except ImportError:
        return buffers[0]


@app.post("/sessions/{session_id}/export/screens-png")
async def export_screens_png(session_id: str, request: Request) -> Response:
    session = get_session(session_id)
    if session is None:
        return Response(content="Not found", status_code=404)
    if not session.wireframe_briefs:
        return Response(content="No wireframe briefs", status_code=400)

    base_url = str(request.base_url).rstrip("/")
    summary_url = f"{base_url}/sessions/{session_id}/summary"

    try:
        png_bytes = await run_in_threadpool(_capture_screens_png, summary_url)
    except Exception as exc:
        return Response(content=f"Screenshot error: {exc}", status_code=500)

    filename = (session.session_name or "ux-screens").replace(" ", "-").lower() + ".png"
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
