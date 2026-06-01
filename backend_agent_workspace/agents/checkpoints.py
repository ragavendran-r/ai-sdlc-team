"""Checkpoint functions for Backend Agent workflow."""

from .state import BackendWorkflowState


def should_proceed_to_pr_description(state: BackendWorkflowState) -> bool:
    """
    Determine if we should proceed from human_checkpoint to pr_description.
    Returns True if implementation was approved.
    """
    return state.implementation_approved


def should_route_to_security_checkpoint(state: BackendWorkflowState) -> bool:
    """
    Determine if security review found critical issues requiring
    early human checkpoint routing.
    Returns True if critical security flags were found.
    """
    return state.has_critical_security_flags
