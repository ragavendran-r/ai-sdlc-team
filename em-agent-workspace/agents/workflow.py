"""LangGraph workflow for EM Agent."""

from langgraph.graph import StateGraph, END
from .state import EMWorkflowState
from .nodes import (
    backlog_intake,
    dependency_mapping,
    capacity_analysis,
    risk_assessment,
    sprint_composition,
    definition_of_done,
    human_checkpoint,
    sprint_creation,
    status_monitoring,
    blocker_detection,
    stakeholder_reporting,
)
from .checkpoints import (
    should_proceed_to_sprint_creation,
    should_revise_sprint,
)


def create_em_workflow() -> StateGraph:
    """
    Create and configure the EM Agent workflow using LangGraph.

    The workflow consists of 11 agent nodes plus 1 human checkpoint:

    1. backlog_intake - Validate incoming stories
    2. dependency_mapping - Build dependency graph
    3. capacity_analysis - Estimate sprint capacity
    4. risk_assessment - Identify and flag risks
    5. sprint_composition - Compose draft sprint plan
    6. definition_of_done - Generate DoD checklist
    [CHECKPOINT: Human review of draft sprint]
    7. sprint_creation - Create sprint in Jira (stubbed)
    8. status_monitoring - Poll sprint status continuously
    9. blocker_detection - Identify blocked stories
    10. stakeholder_reporting - Generate status reports

    Returns:
        StateGraph: Compiled LangGraph workflow
    """

    # Create state graph
    workflow = StateGraph(EMWorkflowState)

    # ========================================================================
    # ADD NODES
    # ========================================================================

    # Phase 1: Backlog Processing
    workflow.add_node("backlog_intake", backlog_intake)
    workflow.add_node("dependency_mapping", dependency_mapping)

    # Phase 2: Capacity and Risk Analysis
    workflow.add_node("capacity_analysis", capacity_analysis)
    workflow.add_node("risk_assessment", risk_assessment)

    # Phase 3: Sprint Planning with Checkpoint
    workflow.add_node("sprint_composition", sprint_composition)
    workflow.add_node("definition_of_done", definition_of_done)
    workflow.add_node("human_checkpoint", human_checkpoint)

    # Phase 4: Sprint Execution
    workflow.add_node("sprint_creation", sprint_creation)
    workflow.add_node("status_monitoring", status_monitoring)
    workflow.add_node("blocker_detection", blocker_detection)
    workflow.add_node("stakeholder_reporting", stakeholder_reporting)

    # ========================================================================
    # ADD EDGES
    # ========================================================================

    # Start: Entry point
    workflow.set_entry_point("backlog_intake")

    # Phase 1: Linear flow to validate and map dependencies
    workflow.add_edge("backlog_intake", "dependency_mapping")

    # Phase 2: Analyze capacity and risks (can be parallel)
    workflow.add_edge("dependency_mapping", "capacity_analysis")
    workflow.add_edge("dependency_mapping", "risk_assessment")

    # Converge on sprint composition
    workflow.add_edge("capacity_analysis", "sprint_composition")
    workflow.add_edge("risk_assessment", "sprint_composition")

    # Phase 3: Plan sprint with DoD checklist
    workflow.add_edge("sprint_composition", "definition_of_done")
    workflow.add_edge("definition_of_done", "human_checkpoint")

    # Checkpoint: Conditional routing
    # If approved: proceed to sprint creation
    workflow.add_conditional_edges(
        "human_checkpoint",
        should_proceed_to_sprint_creation,
        {
            True: "sprint_creation",       # ✅ Approved
            False: "sprint_composition",   # ❌ Rejected - revise
        }
    )

    # Phase 4: Execution and Monitoring (sequential for now)
    workflow.add_edge("sprint_creation", "status_monitoring")
    workflow.add_edge("status_monitoring", "blocker_detection")
    workflow.add_edge("blocker_detection", "stakeholder_reporting")

    # End state
    workflow.add_edge("stakeholder_reporting", END)

    return workflow


def compile_em_workflow() -> object:
    """
    Compile the EM Agent workflow for execution.

    Returns:
        Compiled workflow (runnable graph)
    """
    workflow_graph = create_em_workflow()
    return workflow_graph.compile()


# ============================================================================
# WORKFLOW VISUALIZATION
# ============================================================================

def print_workflow_graph(compiled_graph: object) -> None:
    """Print ASCII representation of the workflow graph."""
    print("\n" + "="*80)
    print(" EM AGENT LANGGRAPH WORKFLOW")
    print("="*80)

    graph_description = """
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EM AGENT LANGGRAPH WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

                        BACKLOG PROCESSING PHASE
                                   │
                                   ▼
                          backlog_intake
                                   │
                                   ▼
                        dependency_mapping
                                   │
                    ┌──────────────┴──────────────┐
                    │  ANALYSIS PHASE (parallel)  │
                    ▼                             ▼
            capacity_analysis          risk_assessment
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
                        sprint_composition
                                   │
                                   ▼
                        definition_of_done
                                   │
                                   ▼
                ┌──────────────────────────────────┐
                │    CHECKPOINT: SPRINT APPROVAL   │
                │    (Human review + approval)     │
                └──────────────────────────────────┘
                     ✓ Approved    ✗ Rejected
                     │                │
                     ▼                │
                sprint_creation       │
                     │                │
                     ▼                │
                status_monitoring     │
                     │                │
                     ▼                │
                blocker_detection     │
                     │                │
                     ▼                │
            stakeholder_reporting     │
                     │                │
                     └────────────────┘
                            │
                            ▼
                          (END)

LEGEND:
  ─────► Linear flow
  ┌─┘    Parallel flows (converge)
  ✓/✗    Conditional routing based on human approval
  [1-11] Agent nodes (11 total)
  [ ]    Checkpoint node (1 total)

NODE COUNT: 12 total (11 agents + 1 checkpoint)
CHECKPOINT: 1 (sprint approval with rejection loop)
CONDITIONAL ROUTES: 1 (approval gate with revision loop)
"""

    print(graph_description)


# ============================================================================
# EXECUTION HELPER
# ============================================================================

def run_em_workflow(
    input_stories: list = None,
    verbose: bool = True,
) -> EMWorkflowState:
    """
    Run the EM Agent workflow.

    Args:
        input_stories: List of UserStory objects from PO workflow
        verbose: Print detailed logs during execution

    Returns:
        Final workflow state with sprint plan and artifacts
    """
    import json

    # Create and compile workflow
    compiled_workflow = compile_em_workflow()

    # Initialize state
    initial_state = EMWorkflowState(
        input_stories=input_stories or [],
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
        print(f"Input Stories: {len(final_state.input_stories)}")
        print(f"Validated Stories: {len(final_state.validated_stories)}")
        print(f"Dependency Graph: {len(final_state.dependency_graph)} stories")
        print(f"Circular Dependencies: {len(final_state.circular_dependencies)}")
        print(f"Capacity Report: {final_state.capacity_report.estimated_story_points_capacity if final_state.capacity_report else 'None'} points")
        print(f"Risk Flags: {len(final_state.risk_flags)}")
        print(f"Draft Sprint: {final_state.draft_sprint.sprint.id if final_state.draft_sprint else 'None'}")
        print(f"Sprint Approved: {final_state.sprint_approved}")
        print(f"DoD Checklist: {len(final_state.dod_checklist.items) if final_state.dod_checklist else 0} items")
        print(f"Sprint ID: {final_state.sprint_id}")
        print(f"Jira Tickets: {len(final_state.jira_tickets_created)}")
        print(f"Sprint Status: {final_state.current_sprint_status.health_status if final_state.current_sprint_status else 'None'}")
        print(f"Blockers: {len(final_state.blockers)}")
        print(f"Report Generated: {final_state.report_generated}")
        print(f"\nWorkflow Messages: {len(final_state.messages)}")
        print(f"Workflow Errors: {len(final_state.errors)}")

        if final_state.messages:
            print("\nWorkflow Log:")
            for msg in final_state.messages[-5:]:  # Last 5 messages
                print(f"  [{msg['agent']}] {msg['message']}")

        if final_state.errors:
            print("\nErrors:")
            for error in final_state.errors[-3:]:  # Last 3 errors
                print(f"  {error}")

    return final_state


# Export compiled workflow
em_workflow = compile_em_workflow


if __name__ == "__main__":
    # Example usage
    final_state = run_em_workflow(verbose=True)

    # Save final state to file
    import json
    with open("em_workflow_output.json", "w") as f:
        json.dump(final_state.to_dict(), f, indent=2, default=str)

    print("\n✅ Workflow output saved to em_workflow_output.json")
