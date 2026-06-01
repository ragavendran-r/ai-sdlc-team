"""Human checkpoint for EM Agent workflow."""

from .state import EMWorkflowState


def should_proceed_to_sprint_creation(state: EMWorkflowState) -> bool:
    """
    Guard function: proceed to sprint creation only if sprint approved.
    """
    return state.sprint_approved


def should_revise_sprint(state: EMWorkflowState) -> bool:
    """
    Guard function: return to sprint composition if rejected.
    """
    return not state.sprint_approved
