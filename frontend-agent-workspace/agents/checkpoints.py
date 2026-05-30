"""Human checkpoint nodes for Frontend Agent workflow."""

from typing import Literal
from .state import FrontendWorkflowState


def should_proceed_to_pr_description(state: FrontendWorkflowState) -> bool:
    """Determine if components approved or should revise."""
    return state.components_approved


def should_revise_components(state: FrontendWorkflowState) -> bool:
    """Determine if components should be revised."""
    return not state.components_approved
