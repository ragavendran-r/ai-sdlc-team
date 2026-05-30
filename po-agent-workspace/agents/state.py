"""State definitions for PO Agent workflow."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawRequirement:
    """Raw requirement from stakeholder interview."""
    id: str
    text: str
    source: str
    timestamp: datetime


@dataclass
class StructuredRequirement:
    """Structured requirement with metadata."""
    id: str
    title: str
    description: str
    category: str
    priority_signal: Optional[str]
    effort_signal: Optional[str]
    ambiguities: List[str] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AmbiguityFlag:
    """Flag for ambiguous or unmeasurable requirement."""
    requirement_id: str
    issue: str
    severity: str  # low, medium, high
    suggested_clarification: str


@dataclass
class ConflictFlag:
    """Flag for conflicting requirements."""
    requirement_ids: List[str]
    conflict_type: str  # contradiction, duplicate, incompatible
    description: str
    resolution: Optional[str]


@dataclass
class PoWorkflowState:
    """Complete state for PO Agent workflow."""

    # Interview phase
    interview_notes: str = ""
    raw_requirements: List[RawRequirement] = field(default_factory=list)
    interview_complete: bool = False

    # Structuring phase
    structured_requirements: List[StructuredRequirement] = field(default_factory=list)

    # Quality assurance
    ambiguity_flags: List[AmbiguityFlag] = field(default_factory=list)
    conflict_flags: List[ConflictFlag] = field(default_factory=list)

    # Story generation phase
    generated_stories: List[Dict[str, Any]] = field(default_factory=list)
    stories_approved: bool = False
    approval_notes: str = ""

    # Acceptance criteria phase
    enriched_stories: List[Dict[str, Any]] = field(default_factory=list)

    # Prioritization phase
    prioritized_stories: List[Dict[str, Any]] = field(default_factory=list)

    # Backlog grooming phase
    groomed_backlog: List[Dict[str, Any]] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    backlog_approved: bool = False
    backlog_approval_notes: str = ""

    # JIRA population
    jira_tickets_created: List[str] = field(default_factory=list)
    jira_sync_complete: bool = False

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
            "interview_notes": self.interview_notes,
            "raw_requirements": [
                {
                    "id": r.id,
                    "text": r.text,
                    "source": r.source,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.raw_requirements
            ],
            "interview_complete": self.interview_complete,
            "structured_requirements": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "category": r.category,
                    "priority_signal": r.priority_signal,
                    "effort_signal": r.effort_signal,
                    "ambiguities": r.ambiguities,
                    "conflicts": r.conflicts,
                }
                for r in self.structured_requirements
            ],
            "ambiguity_flags": [
                {
                    "requirement_id": f.requirement_id,
                    "issue": f.issue,
                    "severity": f.severity,
                    "suggested_clarification": f.suggested_clarification,
                }
                for f in self.ambiguity_flags
            ],
            "conflict_flags": [
                {
                    "requirement_ids": f.requirement_ids,
                    "conflict_type": f.conflict_type,
                    "description": f.description,
                    "resolution": f.resolution,
                }
                for f in self.conflict_flags
            ],
            "generated_stories": self.generated_stories,
            "stories_approved": self.stories_approved,
            "approval_notes": self.approval_notes,
            "enriched_stories": self.enriched_stories,
            "prioritized_stories": self.prioritized_stories,
            "groomed_backlog": self.groomed_backlog,
            "themes": self.themes,
            "backlog_approved": self.backlog_approved,
            "backlog_approval_notes": self.backlog_approval_notes,
            "jira_tickets_created": self.jira_tickets_created,
            "jira_sync_complete": self.jira_sync_complete,
            "workflow_start": self.workflow_start.isoformat(),
            "current_agent": self.current_agent,
            "messages": self.messages,
            "errors": self.errors,
        }
