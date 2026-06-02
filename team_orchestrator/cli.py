"""Team CLI for running the full pipeline."""

import os
import signal
import subprocess
import sys
import json
import time
from typing import List, Optional
import argparse

from .orchestrator import TeamOrchestrator
from .events import Event, EventType, EventSeverity


class TeamPipelineCLI:
    """Command-line interface for team pipeline."""

    def __init__(self):
        """Initialize CLI."""
        self.orchestrator = TeamOrchestrator()
        self.parser = self._setup_parser()

    def _setup_parser(self) -> argparse.ArgumentParser:
        """Setup argument parser."""
        parser = argparse.ArgumentParser(
            description="Team AI SDLC Pipeline Orchestrator",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python -m team_orchestrator run --all              # Run full pipeline
  python -m team_orchestrator run --workflows po em  # Run PO and EM only
  python -m team_orchestrator status                 # Show pipeline status
  python -m team_orchestrator routes                 # Show workflow routes
  python -m team_orchestrator export --file state.json  # Export state
            """,
        )

        subparsers = parser.add_subparsers(dest="command", help="Command to run")

        # Run command
        run_parser = subparsers.add_parser("run", help="Run workflows")
        run_parser.add_argument(
            "--all",
            action="store_true",
            help="Run all workflows (po → em → ux/backend/frontend)",
        )
        run_parser.add_argument(
            "--workflows",
            nargs="+",
            choices=["po", "em", "ux", "backend", "frontend"],
            help="Specific workflows to run",
        )
        run_parser.add_argument(
            "--demo",
            action="store_true",
            help="Run demo with simulated workflows",
        )
        run_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output",
        )

        # Status command
        status_parser = subparsers.add_parser("status", help="Show pipeline status")
        status_parser.add_argument(
            "--json",
            action="store_true",
            help="Output as JSON",
        )

        # Routes command
        routes_parser = subparsers.add_parser("routes", help="Show workflow routes")
        routes_parser.add_argument(
            "--json",
            action="store_true",
            help="Output as JSON",
        )

        # Events command
        events_parser = subparsers.add_parser("events", help="Show recent events")
        events_parser.add_argument(
            "--workflow",
            help="Filter by workflow",
        )
        events_parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Number of events to show",
        )

        # Context command
        context_parser = subparsers.add_parser("context", help="Manage context store")
        context_parser.add_argument(
            "--list",
            action="store_true",
            help="List all artifacts",
        )
        context_parser.add_argument(
            "--timeline",
            action="store_true",
            help="Show artifact timeline",
        )
        context_parser.add_argument(
            "--workflow",
            help="Filter by source workflow",
        )
        context_parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all artifacts (use with caution)",
        )

        # Export command
        export_parser = subparsers.add_parser("export", help="Export state")
        export_parser.add_argument(
            "--file",
            default="orchestrator_state.json",
            help="Output file path",
        )

        # Config command
        subparsers.add_parser("config", help="Show configuration")

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI.

        Args:
            args: Command-line arguments

        Returns:
            Exit code
        """
        parsed_args = self.parser.parse_args(args)

        if not parsed_args.command:
            self.parser.print_help()
            return 0

        try:
            if parsed_args.command == "run":
                return self._run_workflows(parsed_args)
            elif parsed_args.command == "status":
                return self._show_status(parsed_args)
            elif parsed_args.command == "routes":
                return self._show_routes(parsed_args)
            elif parsed_args.command == "events":
                return self._show_events(parsed_args)
            elif parsed_args.command == "context":
                return self._manage_context(parsed_args)
            elif parsed_args.command == "export":
                return self._export_state(parsed_args)
            elif parsed_args.command == "config":
                return self._show_config(parsed_args)
            else:
                self.parser.print_help()
                return 1

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            if parsed_args.__dict__.get("verbose"):
                import traceback
                traceback.print_exc()
            return 1

    def _run_workflows(self, args: argparse.Namespace) -> int:
        """Run workflows."""
        self.orchestrator.start_pipeline()

        if args.demo:
            return self._run_demo(args.verbose)

        if args.all:
            workflows = ["po", "em", "ux", "backend", "frontend"]
        else:
            workflows = args.workflows or []

        if not workflows:
            print("❌ Must specify --all or --workflows")
            return 1

        # Simulate workflow execution
        for workflow in workflows:
            self._simulate_workflow(workflow, args.verbose)
            self.orchestrator.mark_workflow_complete(workflow)

        self.orchestrator.complete_pipeline()
        self._show_status(args)
        return 0

    def _start_web_servers(self) -> List[subprocess.Popen]:
        """Start PO/EM/UX web interfaces as background processes."""
        python = sys.executable
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = {**os.environ, "PYTHONPATH": repo_root, "PYTHONWARNINGS": "ignore"}

        servers = [
            ("PO", "po_agent_workspace.interface.app:app", 8001),
            ("EM", "em_agent_workspace.interface.app:app", 8002),
            ("UX", "ux_agent_workspace.interface.app:app", 8003),
            ("Frontend", "frontend_agent_workspace.interface.app:app", 8004),
        ]

        procs = []
        for name, app_module, port in servers:
            proc = subprocess.Popen(
                [
                    python, "-m", "uvicorn", app_module,
                    "--host", "127.0.0.1",
                    "--port", str(port),
                    "--log-level", "warning",
                ],
                env=env,
                cwd=repo_root,
            )
            procs.append(proc)
            print(f"  Starting {name} interface (port {port})... PID {proc.pid}")

        # Give servers a moment to bind their ports.
        time.sleep(2)
        return procs

    def _run_demo(self, verbose: bool = False) -> int:
        """Run demonstration with simulated workflows and live web interfaces."""
        print("\n" + "=" * 80)
        print(" DEMO MODE: Running simulated team workflows")
        print("=" * 80)

        print("\n🌐 Starting web interfaces...")
        server_procs = self._start_web_servers()

        print("\n" + "=" * 80)
        print(" WEB INTERFACES READY")
        print("=" * 80)
        print("  PO Workspace      →  http://localhost:8001")
        print("  EM Workspace      →  http://localhost:8002")
        print("  UX Workspace      →  http://localhost:8003")
        print("  Frontend Workspace →  http://localhost:8004")
        print("\n  Lifecycle: paste requirements in PO → approve backlog → EM plans")
        print("  sprint → UX reviews design → Frontend consumes UX handoff")
        print("=" * 80)

        # Simulate PO workflow
        print("\n1️⃣  PO Workflow: Creating user stories...")
        po_event = Event(
            event_type=EventType.USER_STORIES_CREATED,
            workflow="po",
            severity=EventSeverity.INFO,
            payload={
                "stories": [
                    {"id": "US-001", "title": "User login", "priority": "high"},
                    {"id": "US-002", "title": "User profile", "priority": "medium"},
                ],
                "context": {"project": "demo", "created_by": "demo_mode"},
            },
            source_agent="po-agent",
        )
        self.orchestrator.publish_event(po_event)
        self.orchestrator.mark_workflow_complete("po")

        # Simulate EM workflow
        print("\n2️⃣  EM Workflow: Creating sprint plan...")
        em_event = Event(
            event_type=EventType.SPRINT_CREATED,
            workflow="em",
            severity=EventSeverity.INFO,
            payload={
                "sprint": {
                    "id": "S-001",
                    "name": "Sprint 1",
                    "duration_days": 14,
                },
                "stories": ["US-001", "US-002"],
                "tasks": [
                    {"id": "T-001", "title": "Design login flow"},
                    {"id": "T-002", "title": "Implement login API"},
                ],
            },
            source_agent="em-agent",
        )
        self.orchestrator.publish_event(em_event)
        self.orchestrator.mark_workflow_complete("em")

        # Simulate UX workflow
        print("\n3️⃣  UX Workflow: Creating design handoff...")
        ux_event = Event(
            event_type=EventType.HANDOFF_CREATED,
            workflow="ux",
            severity=EventSeverity.INFO,
            payload={
                "handoff": {
                    "id": "UX-001",
                    "feature": "User authentication",
                    "components": [
                        {"name": "LoginForm", "type": "input"},
                        {"name": "ErrorMessage", "type": "feedback"},
                    ],
                },
                "tokens": {
                    "color-primary": "#007bff",
                    "color-danger": "#dc3545",
                },
            },
            source_agent="ux-agent",
        )
        self.orchestrator.publish_event(ux_event)
        self.orchestrator.mark_workflow_complete("ux")

        # Simulate Backend workflow
        print("\n4️⃣  Backend Workflow: Generating API contract...")
        backend_event = Event(
            event_type=EventType.API_CONTRACT_PUBLISHED,
            workflow="backend",
            severity=EventSeverity.INFO,
            payload={
                "contract": {
                    "id": "API-001",
                    "feature": "User authentication",
                    "endpoints": [
                        {"method": "POST", "path": "/auth/login"},
                        {"method": "GET", "path": "/auth/user"},
                    ],
                    "base_url": "https://api.example.com/v1",
                },
            },
            source_agent="backend-agent",
        )
        self.orchestrator.publish_event(backend_event)
        self.orchestrator.mark_workflow_complete("backend")

        # Simulate Frontend workflow
        print("\n5️⃣  Frontend Workflow: Scaffolding components...")
        frontend_event = Event(
            event_type=EventType.COMPONENTS_SCAFFOLDED,
            workflow="frontend",
            severity=EventSeverity.INFO,
            payload={
                "components": [
                    {"id": "C-001", "name": "LoginForm"},
                    {"id": "C-002", "name": "ErrorMessage"},
                ],
                "test_files": 2,
                "state_plan": "context_api",
            },
            source_agent="frontend-agent",
        )
        self.orchestrator.publish_event(frontend_event)
        self.orchestrator.mark_workflow_complete("frontend")

        self.orchestrator.complete_pipeline()
        self._show_status(argparse.Namespace(json=False))

        print("\n" + "=" * 80)
        print(" SERVERS RUNNING — Press Ctrl+C to stop")
        print("=" * 80)
        print("  PO Workspace      →  http://localhost:8001")
        print("  EM Workspace      →  http://localhost:8002")
        print("  UX Workspace      →  http://localhost:8003")
        print("  Frontend Workspace →  http://localhost:8004")

        def _shutdown(signum, frame):
            print("\n\nShutting down web interfaces...")
            for proc in server_procs:
                proc.terminate()
            for proc in server_procs:
                proc.wait()
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        while True:
            time.sleep(1)

        return 0

    def _simulate_workflow(self, workflow: str, verbose: bool = False) -> None:
        """Simulate a workflow execution."""
        print(f"\n▶️  {workflow.upper()} workflow...")

        # Stub: workflows would be executed here
        event = Event(
            event_type=EventType.WORKFLOW_STARTED,
            workflow=workflow,
            severity=EventSeverity.INFO,
            payload={},
            source_agent=f"{workflow}-agent",
        )
        self.orchestrator.publish_event(event)

    def _show_status(self, args: argparse.Namespace) -> int:
        """Show pipeline status."""
        if args.json:
            status = self.orchestrator.get_pipeline_status()
            print(json.dumps(status, indent=2, default=str))
        else:
            self.orchestrator.print_status_report()
        return 0

    def _show_routes(self, args: argparse.Namespace) -> int:
        """Show workflow routes."""
        if args.json:
            stats = self.orchestrator.router.get_stats()
            print(json.dumps(stats, indent=2, default=str))
        else:
            self.orchestrator.print_route_diagram()
        return 0

    def _show_events(self, args: argparse.Namespace) -> int:
        """Show event log."""
        events = self.orchestrator.event_bus.get_history(
            workflow=args.workflow,
            limit=args.limit
        )

        print("\n" + "=" * 80)
        print(" EVENT LOG")
        print("=" * 80)

        if not events:
            print("No events.")
            return 0

        for event in events:
            print(
                f"{event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
                f"[{event.workflow:8}] {event.event_type.value:30} "
                f"({event.severity.value})"
            )

        return 0

    def _manage_context(self, args: argparse.Namespace) -> int:
        """Manage context store."""
        if args.list:
            artifacts = self.orchestrator.context_store.list_artifacts(
                workflow=args.workflow
            )
            print(f"\nArtifacts: {len(artifacts)}")
            for artifact in artifacts:
                print(
                    f"  {artifact['key']:30} "
                    f"{artifact['artifact_type']:20} "
                    f"({artifact['size_bytes']} bytes)"
                )
        elif args.timeline:
            print("\n" + self.orchestrator.context_store.export_timeline())
        elif args.clear:
            response = input("Are you sure? This will delete all artifacts. (y/N): ")
            if response.lower() == "y":
                self.orchestrator.context_store.clear()
                print("✅ Context store cleared")
        else:
            stats = self.orchestrator.context_store.get_stats()
            print(json.dumps(stats, indent=2))

        return 0

    def _export_state(self, args: argparse.Namespace) -> int:
        """Export orchestrator state."""
        self.orchestrator.export_state(args.file)
        return 0

    def _show_config(self, args: argparse.Namespace) -> int:
        """Show configuration."""
        print("\n" + "=" * 80)
        print(" TEAM ORCHESTRATOR CONFIGURATION")
        print("=" * 80)
        print("\nContext Store: team_contracts/context-store")
        print(f"Workflows: {', '.join(self.orchestrator.workflow_states.keys())}")
        print(f"Routes: {len(self.orchestrator.router.routes)}")
        print("\nDefault Routes:")
        for route in self.orchestrator.router.routes:
            print(
                f"  {route.source_workflow} "
                f"[{route.source_event_type.value}] → "
                f"{route.target_workflow}"
            )
        return 0


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point."""
    cli = TeamPipelineCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
