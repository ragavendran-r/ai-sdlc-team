"""BackendWorkflowState for Backend Agent LangGraph workflow."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class BackendWorkflowState:
    """Complete state for backend agent workflow with 12 nodes."""

    # ========================================================================
    # INPUT PHASE
    # ========================================================================
    user_stories: List[Dict[str, Any]] = field(default_factory=list)
    sprint_plan: Optional[Dict[str, Any]] = field(default=None)

    # ========================================================================
    # REQUIREMENTS INTAKE PHASE
    # ========================================================================
    backend_requirements: List[Dict[str, Any]] = field(default_factory=list)
    requirements_intake_complete: bool = field(default=False)

    # ========================================================================
    # DOMAIN MODELING PHASE
    # ========================================================================
    domain_model: Optional[Dict[str, Any]] = field(default=None)
    domain_model_complete: bool = field(default=False)

    # ========================================================================
    # DATABASE SCHEMA PHASE
    # ========================================================================
    db_schema: Optional[Dict[str, Any]] = field(default=None)
    db_schema_complete: bool = field(default=False)

    # ========================================================================
    # API CONTRACT PHASE
    # ========================================================================
    api_contract: Optional[Dict[str, Any]] = field(default=None)
    api_contract_complete: bool = field(default=False)

    # ========================================================================
    # BUSINESS LOGIC SCAFFOLDING PHASE
    # ========================================================================
    service_scaffolds: List[Dict[str, Any]] = field(default_factory=list)
    scaffolding_complete: bool = field(default=False)

    # ========================================================================
    # VALIDATION RULES PHASE
    # ========================================================================
    validation_modules: List[Dict[str, Any]] = field(default_factory=list)
    validation_rules_complete: bool = field(default=False)

    # ========================================================================
    # SECURITY REVIEW PHASE
    # ========================================================================
    security_flags: List[Dict[str, Any]] = field(default_factory=list)
    has_critical_security_flags: bool = field(default=False)
    security_review_complete: bool = field(default=False)

    # ========================================================================
    # TEST GENERATION PHASE
    # ========================================================================
    test_files: List[Dict[str, Any]] = field(default_factory=list)
    test_generation_complete: bool = field(default=False)

    # ========================================================================
    # HUMAN CHECKPOINT PHASE
    # ========================================================================
    implementation_approved: bool = field(default=False)
    approval_feedback: Optional[str] = field(default=None)
    checkpoint_triggered_early_for_security: bool = field(default=False)

    # ========================================================================
    # PR GENERATION PHASE
    # ========================================================================
    pr_description: str = field(default="")
    pr_creation_complete: bool = field(default=False)

    # ========================================================================
    # CODE REVIEW PHASE
    # ========================================================================
    review_comments: List[Dict[str, Any]] = field(default_factory=list)
    code_review_complete: bool = field(default=False)

    # ========================================================================
    # API PUBLISHING PHASE
    # ========================================================================
    api_published: bool = field(default=False)
    api_publishing_complete: bool = field(default=False)

    # ========================================================================
    # METADATA
    # ========================================================================
    workflow_start: datetime = field(default_factory=datetime.utcnow)
    current_agent: str = field(default="")
    messages: List[Dict[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return asdict(self)
