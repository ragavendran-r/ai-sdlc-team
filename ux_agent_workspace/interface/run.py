"""Launcher for the UX web interface.

Run from the repository root: python -m ux_agent_workspace.interface.run
Reads HOST/PORT from the environment so Docker/compose can override them.
"""

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "ux_agent_workspace.interface.app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=bool(os.getenv("RELOAD")),
    )
