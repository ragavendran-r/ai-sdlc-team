"""LangGraph workflow for UX Agent."""

from langgraph.graph import StateGraph, END
from .state import UXWorkflowState
from .nodes import (
    story_intake,
    persona_agent,
    user_flow_mapping,
    information_architecture,
    wireframe_brief,
    design_system_compliance,
    accessibility_review,
    human_checkpoint,
    figma_annotation,
    handoff_spec,
)
from .checkpoints import should_proceed_to_figma, should_revise_briefs


def create_ux_workflow() -> StateGraph:
    """Create UX Agent LangGraph workflow."""

    workflow = StateGraph(UXWorkflowState)

    # Add nodes
    workflow.add_node("story_intake", story_intake)
    workflow.add_node("persona_agent", persona_agent)
    workflow.add_node("user_flow_mapping", user_flow_mapping)
    workflow.add_node("information_architecture", information_architecture)
    workflow.add_node("wireframe_brief", wireframe_brief)
    workflow.add_node("design_system_compliance", design_system_compliance)
    workflow.add_node("accessibility_review", accessibility_review)
    workflow.add_node("human_checkpoint", human_checkpoint)
    workflow.add_node("figma_annotation", figma_annotation)
    workflow.add_node("handoff_spec", handoff_spec)

    # Add edges
    workflow.set_entry_point("story_intake")
    workflow.add_edge("story_intake", "persona_agent")
    workflow.add_edge("persona_agent", "user_flow_mapping")
    workflow.add_edge("user_flow_mapping", "information_architecture")
    workflow.add_edge("information_architecture", "wireframe_brief")
    workflow.add_edge("wireframe_brief", "design_system_compliance")
    workflow.add_edge("design_system_compliance", "accessibility_review")
    workflow.add_edge("accessibility_review", "human_checkpoint")

    # Checkpoint conditional routing
    workflow.add_conditional_edges(
        "human_checkpoint",
        should_proceed_to_figma,
        {
            True: "figma_annotation",
            False: "wireframe_brief",
        }
    )

    workflow.add_edge("figma_annotation", "handoff_spec")
    workflow.add_edge("handoff_spec", END)

    return workflow


def compile_ux_workflow() -> object:
    """Compile the UX Agent workflow."""
    workflow_graph = create_ux_workflow()
    return workflow_graph.compile()


def print_workflow_graph(compiled_graph: object) -> None:
    """Print ASCII representation of the workflow."""
    print("\n" + "="*80)
    print(" UX AGENT LANGGRAPH WORKFLOW")
    print("="*80)

    description = """
┌─────────────────────────────────────────────────────────────────┐
│                    UX AGENT LANGGRAPH WORKFLOW                  │
└─────────────────────────────────────────────────────────────────┘

story_intake
    ↓
persona_agent
    ↓
user_flow_mapping
    ↓
information_architecture
    ↓
wireframe_brief
    ↓
design_system_compliance
    ↓
accessibility_review
    ↓
[CHECKPOINT: Brief Approval]
    ↓ (if approved)
figma_annotation
    ↓
handoff_spec
    ↓
(END)

LEGEND:
  ─────► Linear flow
  ✓/✗   Conditional routing
  [1-10] Agent nodes (10 total)
  [ ]    Checkpoint node (1 total)

NODE COUNT: 11 total (10 agents + 1 checkpoint)
CHECKPOINT: 1 (brief approval with revision loop)
"""

    print(description)


def run_ux_workflow(verbose: bool = True) -> UXWorkflowState:
    """Run the UX Agent workflow."""
    compiled = compile_ux_workflow()
    initial_state = UXWorkflowState()

    if verbose:
        print_workflow_graph(compiled)
        print("\n" + "="*80)
        print(" WORKFLOW EXECUTION STARTING")
        print("="*80)

    final_state = compiled.invoke(initial_state)

    if verbose:
        print("\n" + "="*80)
        print(" WORKFLOW EXECUTION COMPLETED")
        print("="*80)

    return final_state


ux_workflow = compile_ux_workflow


if __name__ == "__main__":
    final_state = run_ux_workflow(verbose=True)

    import json
    with open("ux_workflow_output.json", "w") as f:
        json.dump(final_state.to_dict(), f, indent=2, default=str)

    print("\n✅ Workflow output saved to ux_workflow_output.json")
