"""Tests for team orchestrator."""

import importlib
import pytest

# Import using importlib to handle hyphens in directory name
team_orch = importlib.import_module('team-orchestrator')
TeamOrchestrator = team_orch.TeamOrchestrator
Event = team_orch.Event
EventType = team_orch.EventType
EventSeverity = team_orch.EventSeverity


class TestEventBus:
    """Test event bus functionality."""

    def test_publish_event(self):
        """Test publishing an event."""
        orchestrator = TeamOrchestrator()

        event = Event(
            event_type=EventType.USER_STORIES_CREATED,
            workflow="po",
            payload={"stories": [{"id": "US-001"}]},
        )

        orchestrator.publish_event(event)

        assert len(orchestrator.event_bus.event_history) > 0
        assert orchestrator.event_bus.event_history[-1].event_type == EventType.USER_STORIES_CREATED

    def test_event_subscription(self):
        """Test subscribing to events."""
        orchestrator = TeamOrchestrator()

        handled_events = []

        def handler(event: Event):
            handled_events.append(event)

        orchestrator.event_bus.subscribe(
            event_types=[EventType.USER_STORIES_CREATED],
            handler=handler,
            name="test_handler"
        )

        event = Event(
            event_type=EventType.USER_STORIES_CREATED,
            workflow="po",
            payload={},
        )

        orchestrator.publish_event(event)

        assert len(handled_events) > 0

    def test_event_filtering(self):
        """Test filtering events."""
        orchestrator = TeamOrchestrator()

        # Publish events from different workflows
        po_event = Event(
            event_type=EventType.USER_STORIES_CREATED,
            workflow="po",
            payload={},
        )
        em_event = Event(
            event_type=EventType.SPRINT_CREATED,
            workflow="em",
            payload={},
        )

        orchestrator.publish_event(po_event)
        orchestrator.publish_event(em_event)

        # Filter by workflow
        po_events = orchestrator.event_bus.get_history(workflow="po")
        assert len(po_events) > 0
        assert all(e.workflow == "po" for e in po_events)


class TestContextStore:
    """Test context store functionality."""

    def test_write_artifact(self):
        """Test writing an artifact."""
        orchestrator = TeamOrchestrator()

        artifact = {
            "id": "US-001",
            "title": "User login",
            "stories": [{"id": "US-001"}]
        }

        path = orchestrator.context_store.write_artifact(
            key="test_artifact",
            data=artifact,
            workflow="po",
            artifact_type="user_stories"
        )

        assert path is not None
        assert "test_artifact" in path

    def test_read_artifact(self):
        """Test reading an artifact."""
        orchestrator = TeamOrchestrator()

        artifact = {"data": "test"}

        orchestrator.context_store.write_artifact(
            key="test_read",
            data=artifact,
            workflow="po",
            artifact_type="test"
        )

        read_data = orchestrator.context_store.read_artifact("test_read")

        assert read_data is not None
        assert read_data["data"] == "test"

    def test_list_artifacts(self):
        """Test listing artifacts."""
        orchestrator = TeamOrchestrator()

        orchestrator.context_store.write_artifact(
            key="artifact1",
            data={"id": 1},
            workflow="po",
            artifact_type="stories"
        )
        orchestrator.context_store.write_artifact(
            key="artifact2",
            data={"id": 2},
            workflow="em",
            artifact_type="sprint"
        )

        artifacts = orchestrator.context_store.list_artifacts()

        assert len(artifacts) >= 2

    def test_filter_by_workflow(self):
        """Test filtering artifacts by workflow."""
        orchestrator = TeamOrchestrator()

        orchestrator.context_store.write_artifact(
            key="po_artifact",
            data={},
            workflow="po",
            artifact_type="stories"
        )
        orchestrator.context_store.write_artifact(
            key="em_artifact",
            data={},
            workflow="em",
            artifact_type="sprint"
        )

        po_artifacts = orchestrator.context_store.list_artifacts(workflow="po")

        assert all(a["workflow"] == "po" for a in po_artifacts)


class TestWorkflowRouter:
    """Test workflow router functionality."""

    def test_add_route(self):
        """Test adding a route."""
        orchestrator = TeamOrchestrator()

        initial_routes = len(orchestrator.router.routes)

        orchestrator.router.add_route(
            source_workflow="po",
            source_event_type=EventType.USER_STORIES_CREATED,
            target_workflow="ux",
        )

        assert len(orchestrator.router.routes) > initial_routes

    def test_route_event(self):
        """Test routing an event."""
        orchestrator = TeamOrchestrator()

        event = Event(
            event_type=EventType.USER_STORIES_CREATED,
            workflow="po",
            payload={"stories": [{"id": "US-001"}]},
        )

        results = orchestrator.router.route_event(event)

        # Should match the default PO → EM route
        assert any(r["target_workflow"] == "em" for r in results)

    def test_route_with_mapper(self):
        """Test routing with data mapping."""
        orchestrator = TeamOrchestrator()

        def custom_mapper(payload):
            return {"transformed": payload}

        orchestrator.router.add_route(
            source_workflow="test_source",
            source_event_type=EventType.WORKFLOW_STARTED,
            target_workflow="test_target",
            data_mapper=custom_mapper,
        )

        event = Event(
            event_type=EventType.WORKFLOW_STARTED,
            workflow="test_source",
            payload={"key": "value"},
        )

        results = orchestrator.router.route_event(event)

        assert any(r["data"]["transformed"] == {"key": "value"} for r in results)


class TestOrchestrator:
    """Test team orchestrator functionality."""

    def test_start_pipeline(self):
        """Test starting pipeline."""
        orchestrator = TeamOrchestrator()

        orchestrator.start_pipeline()

        assert orchestrator.pipeline_started is not None
        assert not orchestrator.pipeline_failed

    def test_complete_pipeline(self):
        """Test completing pipeline."""
        orchestrator = TeamOrchestrator()

        orchestrator.start_pipeline()
        orchestrator.complete_pipeline()

        assert orchestrator.pipeline_completed is not None
        assert not orchestrator.pipeline_failed

    def test_fail_pipeline(self):
        """Test failing pipeline."""
        orchestrator = TeamOrchestrator()

        orchestrator.start_pipeline()
        orchestrator.fail_pipeline("Test error")

        assert orchestrator.pipeline_failed
        assert orchestrator.pipeline_error == "Test error"

    def test_mark_workflow_complete(self):
        """Test marking workflow as complete."""
        orchestrator = TeamOrchestrator()

        orchestrator.mark_workflow_complete("po")

        assert orchestrator.workflow_states["po"]["completed"]
        assert orchestrator.workflow_states["po"]["status"] == "completed"

    def test_workflow_states(self):
        """Test workflow state tracking."""
        orchestrator = TeamOrchestrator()

        # All workflows should start as pending
        for workflow, state in orchestrator.workflow_states.items():
            assert state["status"] == "pending"
            assert not state["completed"]

    def test_get_pipeline_status(self):
        """Test getting pipeline status."""
        orchestrator = TeamOrchestrator()

        orchestrator.start_pipeline()

        status = orchestrator.get_pipeline_status()

        assert "pipeline_status" in status
        assert "workflow_states" in status
        assert "event_bus_stats" in status
        assert "context_store_stats" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
