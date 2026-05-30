"""State definitions for EM Agent workflow."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from team_contracts.schemas import (
    UserStory,
    SprintPlan,
    CapacityReport,
    RiskFlag,
    DoDItem,
    DefinitionOfDone,
    SprintStatus,
    Blocker,
)


@dataclass
class EMWorkflowState:
    """Complete state for EM Agent workflow."""

    # Phase 1: Backlog Intake
    input_stories: List[UserStory] = field(default_factory=list)
    validated_stories: List[UserStory] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)

    # Phase 2: Dependency Mapping
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    circular_dependencies: List[tuple] = field(default_factory=list)

    # Phase 3: Capacity Analysis
    team_velocity: float = 0.0
    team_size: int = 0
    leave_calendar: Dict[str, List[str]] = field(default_factory=dict)
    capacity_report: Optional[CapacityReport] = None

    # Phase 4: Risk Assessment
    risk_flags: List[RiskFlag] = field(default_factory=list)
    risk_summary: Dict[str, int] = field(default_factory=dict)  # risk_type -> count

    # Phase 5: Sprint Composition
    draft_sprint: Optional[SprintPlan] = None
    sprint_approved: bool = False
    approval_feedback: str = ""

    # Phase 6: Definition of Done
    dod_checklist: Optional[DefinitionOfDone] = None

    # Phase 7: Human Checkpoint
    checkpoint_reached: bool = False

    # Phase 8: Sprint Creation
    sprint_id: Optional[str] = None
    jira_tickets_created: List[str] = field(default_factory=list)

    # Phase 9-11: Sprint Execution Monitoring
    sprint_status_history: List[SprintStatus] = field(default_factory=list)
    current_sprint_status: Optional[SprintStatus] = None
    blockers: List[Blocker] = field(default_factory=list)
    status_monitoring_active: bool = False
    last_status_check: Optional[datetime] = None

    # Reports
    sprint_report: str = ""
    report_generated: bool = False

    # Metadata
    workflow_start: datetime = field(default_factory=datetime.utcnow)
    current_agent: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_message(self, agent: str, message: str) -> None:
        """Add a message to the workflow log."""
        self.messages.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "message": message,
        })

    def add_error(self, error: str) -> None:
        """Record an error in the workflow."""
        self.errors.append(f"[{datetime.utcnow().isoformat()}] {error}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "input_stories": [s.to_dict() for s in self.input_stories],
            "validated_stories": [s.to_dict() for s in self.validated_stories],
            "validation_errors": self.validation_errors,
            "dependency_graph": self.dependency_graph,
            "circular_dependencies": self.circular_dependencies,
            "team_velocity": self.team_velocity,
            "team_size": self.team_size,
            "leave_calendar": self.leave_calendar,
            "capacity_report": self.capacity_report.to_dict() if self.capacity_report else None,
            "risk_flags": [r.to_dict() for r in self.risk_flags],
            "risk_summary": self.risk_summary,
            "draft_sprint": self.draft_sprint.to_dict() if self.draft_sprint else None,
            "sprint_approved": self.sprint_approved,
            "approval_feedback": self.approval_feedback,
            "dod_checklist": self.dod_checklist.to_dict() if self.dod_checklist else None,
            "checkpoint_reached": self.checkpoint_reached,
            "sprint_id": self.sprint_id,
            "jira_tickets_created": self.jira_tickets_created,
            "sprint_status_history": [s.to_dict() for s in self.sprint_status_history],
            "current_sprint_status": self.current_sprint_status.to_dict() if self.current_sprint_status else None,
            "blockers": [b.to_dict() for b in self.blockers],
            "status_monitoring_active": self.status_monitoring_active,
            "last_status_check": self.last_status_check.isoformat() if self.last_status_check else None,
            "sprint_report": self.sprint_report,
            "report_generated": self.report_generated,
            "workflow_start": self.workflow_start.isoformat(),
            "current_agent": self.current_agent,
            "messages": self.messages,
            "errors": self.errors,
        }
