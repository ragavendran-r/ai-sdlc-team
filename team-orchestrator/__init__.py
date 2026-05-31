"""Team Orchestrator - Coordinates all AI SDLC Team workflows."""

try:
    # Try relative imports first (normal package import)
    from .events import Event, EventType, EventBus, EventSeverity
    from .context_store import ContextStore
    from .router import WorkflowRouter
    from .orchestrator import TeamOrchestrator
    from .cli import TeamPipelineCLI, main
except ImportError:
    # Fallback for when imported via importlib with hyphenated name
    import sys
    import importlib
    mod = sys.modules[__name__]

    # Import submodules
    events_mod = importlib.import_module(f'{__name__}.events')
    context_mod = importlib.import_module(f'{__name__}.context_store')
    router_mod = importlib.import_module(f'{__name__}.router')
    orch_mod = importlib.import_module(f'{__name__}.orchestrator')
    cli_mod = importlib.import_module(f'{__name__}.cli')

    # Assign to module
    Event = events_mod.Event
    EventType = events_mod.EventType
    EventBus = events_mod.EventBus
    EventSeverity = events_mod.EventSeverity
    ContextStore = context_mod.ContextStore
    WorkflowRouter = router_mod.WorkflowRouter
    TeamOrchestrator = orch_mod.TeamOrchestrator
    TeamPipelineCLI = cli_mod.TeamPipelineCLI
    main = cli_mod.main

__all__ = [
    "Event",
    "EventType",
    "EventBus",
    "EventSeverity",
    "ContextStore",
    "WorkflowRouter",
    "TeamOrchestrator",
    "TeamPipelineCLI",
    "main",
]
