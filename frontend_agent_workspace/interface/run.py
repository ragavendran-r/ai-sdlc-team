"""Entry point: uvicorn frontend_agent_workspace.interface.app:app"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "frontend_agent_workspace.interface.app:app",
        host="127.0.0.1",
        port=8004,
        reload=True,
    )
