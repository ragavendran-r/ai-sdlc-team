"""Entry point: launch the PO interface with uvicorn.

Host/port come from the environment so Docker and local runs share one command.
Run from the workspace directory: `python interface/run.py`.
"""

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "interface.app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
