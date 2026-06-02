"""Frontend Agent workflow state."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from team_contracts.schemas import UXHandoff, APIContract


@dataclass
class FrontendWorkflowState:
    """
    Complete state for Frontend Agent workflow.

    Tracks all data flowing through the frontend implementation workflow,
    from UX handoff intake through component scaffolding, state management,
    accessibility enrichment, test generation, and finally PR creation.
    """

    # ========================================================================
    # INPUT PHASE
    # ========================================================================

    # Input handoffs
    ux_handoff: Optional[UXHandoff] = None
    api_contract: Optional[APIContract] = None
    sprint_plan_context: Optional[Dict[str, Any]] = None

    # ========================================================================
    # UX INTAKE PHASE
    # ========================================================================

    validated_handoff: Optional[UXHandoff] = None
    intake_gaps: List[str] = field(default_factory=list)
    handoff_validation_complete: bool = False

    # ========================================================================
    # COMPONENT BREAKDOWN PHASE
    # ========================================================================

    component_plan: List[Dict[str, Any]] = field(default_factory=list)
    component_breakdown_complete: bool = False

    # ========================================================================
    # DESIGN TOKEN MAPPING PHASE
    # ========================================================================

    token_mappings: Dict[str, List[str]] = field(default_factory=dict)
    token_gaps: List[str] = field(default_factory=list)
    token_mapping_complete: bool = False

    # ========================================================================
    # API INTEGRATION PLANNING PHASE
    # ========================================================================

    api_integration_map: Dict[str, List[str]] = field(default_factory=dict)
    missing_endpoints: List[str] = field(default_factory=list)
    api_planning_complete: bool = False

    # ========================================================================
    # COMPONENT SCAFFOLDING PHASE
    # ========================================================================

    scaffolded_components: List[Dict[str, Any]] = field(default_factory=list)
    scaffolding_complete: bool = False

    # ========================================================================
    # STATE MANAGEMENT PHASE
    # ========================================================================

    state_plan: Optional[Dict[str, Any]] = None
    state_management_complete: bool = False

    # ========================================================================
    # ACCESSIBILITY IMPLEMENTATION PHASE
    # ========================================================================

    a11y_enriched_components: List[Dict[str, Any]] = field(default_factory=list)
    a11y_implementation_complete: bool = False

    # ========================================================================
    # UNIT TEST GENERATION PHASE
    # ========================================================================

    test_files: List[Dict[str, Any]] = field(default_factory=list)
    test_generation_complete: bool = False

    # ========================================================================
    # HUMAN CHECKPOINT
    # ========================================================================

    components_approved: bool = False
    approval_feedback: str = ""

    # ========================================================================
    # PR DESCRIPTION PHASE
    # ========================================================================

    pr_description: str = ""
    pr_creation_complete: bool = False

    # ========================================================================
    # CODE REVIEW PHASE
    # ========================================================================

    review_comments: List[Dict[str, Any]] = field(default_factory=list)
    code_review_complete: bool = False

    # ========================================================================
    # METADATA
    # ========================================================================

    workflow_start: datetime = field(default_factory=datetime.utcnow)
    current_agent: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # ========================================================================
    # WEB MODE
    # ========================================================================

    web_mode: bool = False
    checkpoint_reached: bool = False

    def to_dict(self) -> dict:
        """Convert state to dictionary for serialization."""
        return {
            "ux_handoff": self.ux_handoff.to_dict() if self.ux_handoff else None,
            "api_contract": self.api_contract.to_dict() if self.api_contract else None,
            "sprint_plan_context": self.sprint_plan_context,
            "validated_handoff": self.validated_handoff.to_dict() if self.validated_handoff else None,
            "intake_gaps": self.intake_gaps,
            "handoff_validation_complete": self.handoff_validation_complete,
            "component_plan": self.component_plan,
            "component_breakdown_complete": self.component_breakdown_complete,
            "token_mappings": self.token_mappings,
            "token_gaps": self.token_gaps,
            "token_mapping_complete": self.token_mapping_complete,
            "api_integration_map": self.api_integration_map,
            "missing_endpoints": self.missing_endpoints,
            "api_planning_complete": self.api_planning_complete,
            "scaffolded_components": self.scaffolded_components,
            "scaffolding_complete": self.scaffolding_complete,
            "state_plan": self.state_plan,
            "state_management_complete": self.state_management_complete,
            "a11y_enriched_components": self.a11y_enriched_components,
            "a11y_implementation_complete": self.a11y_implementation_complete,
            "test_files": self.test_files,
            "test_generation_complete": self.test_generation_complete,
            "components_approved": self.components_approved,
            "approval_feedback": self.approval_feedback,
            "pr_description": self.pr_description,
            "pr_creation_complete": self.pr_creation_complete,
            "review_comments": self.review_comments,
            "code_review_complete": self.code_review_complete,
            "workflow_start": self.workflow_start.isoformat(),
            "current_agent": self.current_agent,
            "messages": self.messages,
            "errors": self.errors,
            "web_mode": self.web_mode,
            "checkpoint_reached": self.checkpoint_reached,
        }
