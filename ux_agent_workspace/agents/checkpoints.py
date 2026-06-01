"""Human checkpoint for UX Agent workflow."""

from .state import UXWorkflowState


def should_proceed_to_figma(state: UXWorkflowState) -> bool:
    """Guard function: proceed to Figma only if briefs approved."""
    return state.briefs_approved


def should_revise_briefs(state: UXWorkflowState) -> bool:
    """Guard function: return to wireframe brief if rejected."""
    return not state.briefs_approved
