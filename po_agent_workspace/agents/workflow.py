"""LangGraph workflow for PO Agent."""

from typing import Literal
from langgraph.graph import StateGraph, END
from .state import PoWorkflowState
from .nodes import (
    stakeholder_interview,
    requirements_extraction,
    ambiguity_detection,
    conflict_detection,
    story_generation,
    acceptance_criteria,
    prioritization,
    backlog_grooming,
    jira_population,
)
from .checkpoints import (
    checkpoint_story_generation,
    checkpoint_backlog_grooming,
    should_proceed_to_acceptance_criteria,
    should_proceed_to_jira,
    should_revise_stories,
    should_revise_backlog,
)


def create_po_workflow() -> StateGraph:
    """
    Create and configure the PO Agent workflow using LangGraph.

    The workflow consists of 9 agent nodes plus 2 human checkpoint nodes:

    1. stakeholder_interview - Conversational interviews to extract requirements
    2. requirements_extraction - Structure raw requirements into requirement objects
    3. ambiguity_detection - Flag vague or unmeasurable requirements
    4. conflict_detection - Find contradictions across requirements
    5. story_generation - Produce UserStory schema objects
    [CHECKPOINT 1: Human review of generated stories]
    6. acceptance_criteria - Enrich stories with Given/When/Then criteria
    7. prioritization - Score stories by business value and effort
    8. backlog_grooming - Order and group stories into themes
    [CHECKPOINT 2: Human review of groomed backlog]
    9. jira_population - Create Jira tickets (stubbed)

    Returns:
        StateGraph: Compiled LangGraph workflow
    """

    # Create state graph
    workflow = StateGraph(PoWorkflowState)

    # ========================================================================
    # ADD NODES
    # ========================================================================

    # Phase 1: Stakeholder Interview and Structuring
    workflow.add_node("stakeholder_interview", stakeholder_interview)
    workflow.add_node("requirements_extraction", requirements_extraction)

    # Phase 2: Quality Assurance
    workflow.add_node("ambiguity_detection", ambiguity_detection)
    workflow.add_node("conflict_detection", conflict_detection)

    # Phase 3: Story Generation with Checkpoint
    workflow.add_node("story_generation", story_generation)
    workflow.add_node("checkpoint_story_generation", checkpoint_story_generation)

    # Phase 4: Refinement
    workflow.add_node("acceptance_criteria", acceptance_criteria)
    workflow.add_node("prioritization", prioritization)

    # Phase 5: Backlog Organization with Checkpoint
    workflow.add_node("backlog_grooming", backlog_grooming)
    workflow.add_node("checkpoint_backlog_grooming", checkpoint_backlog_grooming)

    # Phase 6: Jira Integration
    workflow.add_node("jira_population", jira_population)

    # ========================================================================
    # ADD EDGES
    # ========================================================================

    # Start: Entry point is stakeholder interview
    workflow.set_entry_point("stakeholder_interview")

    # Phase 1: Linear flow to structure requirements
    workflow.add_edge("stakeholder_interview", "requirements_extraction")

    # Phase 2: Linear flow through QA
    workflow.add_edge("requirements_extraction", "ambiguity_detection")
    workflow.add_edge("ambiguity_detection", "conflict_detection")

    # Phase 3: Story generation → Checkpoint
    workflow.add_edge("conflict_detection", "story_generation")
    workflow.add_edge("story_generation", "checkpoint_story_generation")

    # Checkpoint 1: Conditional routing
    # If approved: proceed to acceptance criteria
    workflow.add_conditional_edges(
        "checkpoint_story_generation",
        should_proceed_to_acceptance_criteria,
        {
            True: "acceptance_criteria",   # Approved
            False: "story_generation",     # Rejected - revise
        }
    )

    # Phase 4: Refinement (linear flow)
    workflow.add_edge("acceptance_criteria", "prioritization")

    # Phase 5: Backlog grooming → Checkpoint
    workflow.add_edge("prioritization", "backlog_grooming")
    workflow.add_edge("backlog_grooming", "checkpoint_backlog_grooming")

    # Checkpoint 2: Conditional routing
    # If approved: proceed to Jira
    workflow.add_conditional_edges(
        "checkpoint_backlog_grooming",
        should_proceed_to_jira,
        {
            True: "jira_population",       # Approved
            False: "backlog_grooming",     # Rejected - revise
        }
    )

    # Phase 6: End state
    workflow.add_edge("jira_population", END)

    return workflow


def compile_po_workflow() -> object:
    """
    Compile the PO Agent workflow for execution.

    Returns:
        Compiled workflow (runnable graph)
    """
    workflow_graph = create_po_workflow()
    return workflow_graph.compile()


def compile_po_workflow_web() -> object:
    """
    Compile the PO Agent workflow for the web interface.

    Adds an in-memory checkpointer and interrupts before the story-generation
    checkpoint so the web layer can pause the graph, present generated stories
    for human review, then resume via update_state + invoke(None, config).

    Returns:
        Compiled workflow with checkpointer and interrupt configured
    """
    from langgraph.checkpoint.memory import MemorySaver

    workflow_graph = create_po_workflow()
    return workflow_graph.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["checkpoint_story_generation"],
    )


# ============================================================================
# WORKFLOW VISUALIZATION
# ============================================================================

def print_workflow_graph(compiled_graph: object) -> None:
    """Print ASCII representation of the workflow graph."""
    print("\n" + "="*80)
    print(" PO AGENT WORKFLOW GRAPH")
    print("="*80)

    graph_description = """
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PO AGENT LANGGRAPH WORKFLOW                         │
└─────────────────────────────────────────────────────────────────────────────┘

                            INTERVIEW PHASE
                                   │
                                   ▼
                        stakeholder_interview
                                   │
                                   ▼
                       requirements_extraction
                                   │
                      ┌────────────┴────────────┐
                      │   QUALITY ASSURANCE     │
                      ▼                         ▼
              ambiguity_detection    conflict_detection
                      │                         │
                      └────────────┬────────────┘
                                   ▼
                          story_generation
                                   │
                                   ▼
                 ┌──────────────────────────────────┐
                 │  CHECKPOINT 1: STORY APPROVAL    │
                 │  (Human review + approval gate)  │
                 └──────────────────────────────────┘
                      ✓ Approved    ✗ Rejected
                      │                │
                      ▼                │
               acceptance_criteria     │
                      │                │
                      ▼                │
                prioritization         │
                      │                │
                      ▼                │
                backlog_grooming       │
                      │                │
                      ▼                │
                 ┌──────────────────────────────────┐
                 │  CHECKPOINT 2: BACKLOG APPROVAL  │
                 │  (Human review + approval gate)  │
                 └──────────────────────────────────┘
                      ✓ Approved    ✗ Rejected
                      │                │
                      ▼                │
                jira_population        │
                      │                │
                      ▼                ▼
                    (END)          (REVISE)

LEGEND:
  ─────► Linear flow
  ✓/✗   Conditional routing based on human approval
  [1-9] Agent nodes (9 total)
  [ ]   Checkpoint nodes (2 total)

NODE COUNT: 11 total (9 agents + 2 checkpoints)
CHECKPOINTS: 2 (story generation, backlog grooming)
CONDITIONAL ROUTES: 2 (approval gates with revision loops)
"""

    print(graph_description)


# ============================================================================
# EXECUTION HELPER
# ============================================================================

def run_po_workflow(
    initial_context: str = "General product requirement gathering",
    verbose: bool = True,
) -> PoWorkflowState:
    """
    Run the PO Agent workflow.

    Args:
        initial_context: Context for the workflow (e.g., project description)
        verbose: Print detailed logs during execution

    Returns:
        Final workflow state with all generated artifacts
    """
    import json

    # Create and compile workflow
    compiled_workflow = compile_po_workflow()

    # Initialize state
    initial_state = PoWorkflowState(
        interview_notes=initial_context,
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
        print(f"Interview Complete: {final_state.interview_complete}")
        print(f"Raw Requirements: {len(final_state.raw_requirements)}")
        print(f"Structured Requirements: {len(final_state.structured_requirements)}")
        print(f"Ambiguity Flags: {len(final_state.ambiguity_flags)}")
        print(f"Conflict Flags: {len(final_state.conflict_flags)}")
        print(f"Generated Stories: {len(final_state.generated_stories)}")
        print(f"Stories Approved: {final_state.stories_approved}")
        print(f"Enriched Stories: {len(final_state.enriched_stories)}")
        print(f"Prioritized Stories: {len(final_state.prioritized_stories)}")
        print(f"Groomed Backlog Themes: {len(final_state.groomed_backlog)}")
        print(f"Backlog Approved: {final_state.backlog_approved}")
        print(f"Jira Tickets Created: {len(final_state.jira_tickets_created)}")
        print(f"Jira Sync Complete: {final_state.jira_sync_complete}")
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


if __name__ == "__main__":
    # Example usage
    initial_context = "Building a modern SaaS authentication system with email/password and OAuth support"

    final_state = run_po_workflow(
        initial_context=initial_context,
        verbose=True,
    )

    # Save final state to file
    import json
    with open("workflow_output.json", "w") as f:
        json.dump(final_state.to_dict(), f, indent=2)

    print("\n✅ Workflow output saved to workflow_output.json")
