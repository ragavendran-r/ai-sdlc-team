"""LangGraph workflow for Frontend Agent."""

from langgraph.graph import StateGraph, END
from .state import FrontendWorkflowState
from .nodes import (
    ux_handoff_intake,
    component_breakdown,
    design_token_mapping,
    api_integration_planning,
    component_scaffolding,
    state_management,
    accessibility_implementation,
    unit_test_generation,
    human_checkpoint,
    pr_description,
    code_review,
)
from .checkpoints import (
    should_proceed_to_pr_description,
)


def create_frontend_workflow() -> StateGraph:
    """
    Create and configure the Frontend Agent workflow using LangGraph.

    The workflow consists of 11 agent nodes plus 1 human checkpoint node:

    1. ux_handoff_intake - Validate UX handoff completeness
    2. component_breakdown - Decompose screens into atomic components
    3. design_token_mapping - Map components to design tokens
    4. api_integration_planning - Identify API dependencies
    5. component_scaffolding - Generate React component boilerplate
    6. state_management - Plan state management architecture
    7. accessibility_implementation - Add ARIA and keyboard handlers
    8. unit_test_generation - Generate test stubs
    [CHECKPOINT: Human review of components]
    9. pr_description - Generate PR description
    10. code_review - Review against team conventions
    11. (END)

    Returns:
        StateGraph: Compiled LangGraph workflow
    """

    workflow = StateGraph(FrontendWorkflowState)

    # ========================================================================
    # ADD NODES
    # ========================================================================

    # Phase 1: Intake and Breakdown
    workflow.add_node("ux_handoff_intake", ux_handoff_intake)
    workflow.add_node("component_breakdown", component_breakdown)

    # Phase 2: Design System Integration
    workflow.add_node("design_token_mapping", design_token_mapping)
    workflow.add_node("api_integration_planning", api_integration_planning)

    # Phase 3: Component Scaffolding
    workflow.add_node("component_scaffolding", component_scaffolding)
    workflow.add_node("state_management", state_management)

    # Phase 4: Enhancement
    workflow.add_node("accessibility_implementation", accessibility_implementation)
    workflow.add_node("unit_test_generation", unit_test_generation)

    # Phase 5: Checkpoint
    workflow.add_node("human_checkpoint", human_checkpoint)

    # Phase 6: PR and Review
    workflow.add_node("pr_description", pr_description)
    workflow.add_node("code_review", code_review)

    # ========================================================================
    # ADD EDGES
    # ========================================================================

    # Start: Entry point
    workflow.set_entry_point("ux_handoff_intake")

    # Phase 1: Intake → Breakdown
    workflow.add_edge("ux_handoff_intake", "component_breakdown")

    # Phase 2: Design System Integration
    workflow.add_edge("component_breakdown", "design_token_mapping")
    workflow.add_edge("design_token_mapping", "api_integration_planning")

    # Phase 3: Component Scaffolding
    workflow.add_edge("api_integration_planning", "component_scaffolding")
    workflow.add_edge("component_scaffolding", "state_management")

    # Phase 4: Enhancement
    workflow.add_edge("state_management", "accessibility_implementation")
    workflow.add_edge("accessibility_implementation", "unit_test_generation")

    # Phase 5: Checkpoint
    workflow.add_edge("unit_test_generation", "human_checkpoint")

    # Checkpoint: Conditional routing
    workflow.add_conditional_edges(
        "human_checkpoint",
        should_proceed_to_pr_description,
        {
            True: "pr_description",        # Approved
            False: "component_scaffolding",  # Rejected - revise
        }
    )

    # Phase 6: PR and Review
    workflow.add_edge("pr_description", "code_review")
    workflow.add_edge("code_review", END)

    return workflow


def compile_frontend_workflow() -> object:
    """
    Compile the Frontend Agent workflow for execution.

    Returns:
        Compiled workflow (runnable graph)
    """
    workflow_graph = create_frontend_workflow()
    return workflow_graph.compile()


def print_workflow_graph(compiled_graph: object) -> None:
    """Print ASCII representation of the workflow graph."""
    print("\n" + "="*80)
    print(" FRONTEND AGENT WORKFLOW GRAPH")
    print("="*80)

    graph_description = """
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND AGENT LANGGRAPH WORKFLOW                        │
└─────────────────────────────────────────────────────────────────────────────┘

                           UX HANDOFF INTAKE
                                  │
                                  ▼
                          component_breakdown
                                  │
                       ┌──────────┴──────────┐
                       │                     │
                       ▼                     ▼
            design_token_mapping    api_integration_planning
                       │                     │
                       └──────────┬──────────┘
                                  ▼
                        component_scaffolding
                                  │
                                  ▼
                          state_management
                                  │
                                  ▼
                      accessibility_implementation
                                  │
                                  ▼
                          unit_test_generation
                                  │
                                  ▼
                     ┌──────────────────────────────┐
                     │  CHECKPOINT: COMPONENT REVIEW│
                     │  (Human approval + revision) │
                     └──────────────────────────────┘
                      ✓ Approved    ✗ Rejected
                      │                │
                      ▼                │
                  pr_description       │
                      │                │
                      ▼                │
                  code_review          │
                      │                │
                      ▼                ▼
                    (END)        (REVISE)

LEGEND:
  ─────► Linear flow
  ✓/✗   Conditional routing based on human approval
  [1-11] Agent nodes (11 total)
  [ ]   Checkpoint node (1 total)

NODE COUNT: 12 total (11 agents + 1 checkpoint)
CHECKPOINTS: 1 (component approval)
CONDITIONAL ROUTES: 1 (approval gate with revision loop)
"""

    print(graph_description)


def run_frontend_workflow(
    ux_handoff_id: str = "UX-001",
    api_contract_id: str = "API-001",
    verbose: bool = True,
) -> FrontendWorkflowState:
    """
    Run the Frontend Agent workflow.

    Args:
        ux_handoff_id: ID of UX handoff to fetch
        api_contract_id: ID of API contract to fetch
        verbose: Print detailed logs during execution

    Returns:
        Final workflow state with all generated artifacts
    """
    from .tools import ContextStoreTool

    # Create and compile workflow
    compiled_workflow = compile_frontend_workflow()

    # Fetch handoffs from context store
    ux_result = ContextStoreTool.read_ux_handoff(ux_handoff_id)
    api_result = ContextStoreTool.read_api_contract(api_contract_id)

    # Initialize state
    initial_state = FrontendWorkflowState(
        ux_handoff=ux_result.data if ux_result.success else None,
        api_contract=api_result.data if api_result.success else None,
    )

    # Run workflow
    if verbose:
        print_workflow_graph(compiled_workflow)
        print("\n" + "="*80)
        print(" WORKFLOW EXECUTION STARTING")
        print("="*80)

    # Execute the workflow
    final_state = compiled_workflow.invoke(initial_state)

    if verbose:
        print("\n" + "="*80)
        print(" WORKFLOW EXECUTION COMPLETED")
        print("="*80)

        # Print final summary
        print("\nFINAL WORKFLOW STATE SUMMARY:")
        print("-" * 80)
        print(f"Handoff Validation: {final_state.handoff_validation_complete}")
        print(f"Component Breakdown: {len(final_state.component_plan)} components")
        print(f"Token Mapping: {len(final_state.token_gaps)} gaps")
        print(f"API Planning: {len(final_state.missing_endpoints)} missing endpoints")
        print(f"Scaffolded Components: {len(final_state.scaffolded_components)}")
        print(f"State Plan: {final_state.state_plan is not None}")
        print(f"A11y Implementation: {len(final_state.a11y_enriched_components)} components")
        print(f"Test Generation: {len(final_state.test_files)} test files")
        print(f"Components Approved: {final_state.components_approved}")
        print(f"PR Created: {final_state.pr_creation_complete}")
        print(f"Code Review: {len(final_state.review_comments)} comments")
        print(f"\nWorkflow Messages: {len(final_state.messages)}")
        print(f"Workflow Errors: {len(final_state.errors)}")

        if final_state.messages:
            print("\nWorkflow Log:")
            for msg in final_state.messages[-5:]:
                print(f"  [{msg['agent']}] {msg['message']}")

        if final_state.errors:
            print("\nErrors:")
            for error in final_state.errors[-3:]:
                print(f"  {error}")

    return final_state


if __name__ == "__main__":
    final_state = run_frontend_workflow(verbose=True)

    # Save final state to file
    import json
    with open("workflow_output.json", "w") as f:
        json.dump(final_state.to_dict(), f, indent=2)

    print("\n✅ Workflow output saved to workflow_output.json")
