"""LangGraph workflow for Backend Agent."""

from langgraph.graph import StateGraph, END
from .state import BackendWorkflowState
from .nodes import (
    requirements_intake,
    domain_model,
    database_schema,
    api_contract,
    business_logic_scaffolding,
    validation_rules,
    security_review,
    unit_test_generation,
    human_checkpoint,
    pr_description,
    code_review,
    api_publishing,
)
from .checkpoints import (
    should_proceed_to_pr_description,
    should_route_to_security_checkpoint,
)


def create_backend_workflow() -> StateGraph:
    """
    Create and configure the Backend Agent workflow using LangGraph.

    The workflow consists of 12 nodes: 11 agent nodes + 1 human checkpoint.

    1. requirements_intake - Extract backend requirements from stories
    2. domain_model - Build domain model from requirements
    3. database_schema - Generate database schema from domain model
    4. api_contract - Generate OpenAPI 3.0 spec
    5. business_logic_scaffolding - Generate service layer code
    6. validation_rules - Generate Pydantic validators
    7. security_review - Review against OWASP Top 10
    8. unit_test_generation - Generate test stubs
    [CHECKPOINT: Human review of implementation]
    9. pr_description - Generate PR description
    10. code_review - Review code quality
    11. api_publishing - Publish API contract to context store

    Returns:
        StateGraph: Compiled LangGraph workflow
    """

    # Create state graph
    workflow = StateGraph(BackendWorkflowState)

    # ========================================================================
    # ADD NODES
    # ========================================================================

    # Phase 1: Requirements and Domain Modeling
    workflow.add_node("requirements_intake", requirements_intake)
    workflow.add_node("domain_model", domain_model)
    workflow.add_node("database_schema", database_schema)

    # Phase 2: API and Business Logic
    workflow.add_node("api_contract", api_contract)
    workflow.add_node("business_logic_scaffolding", business_logic_scaffolding)
    workflow.add_node("validation_rules", validation_rules)

    # Phase 3: Security and Testing
    workflow.add_node("security_review", security_review)
    workflow.add_node("unit_test_generation", unit_test_generation)

    # Phase 4: Approval and Publishing
    workflow.add_node("human_checkpoint", human_checkpoint)
    workflow.add_node("pr_description", pr_description)
    workflow.add_node("code_review", code_review)
    workflow.add_node("api_publishing", api_publishing)

    # ========================================================================
    # ADD EDGES
    # ========================================================================

    # Start: Entry point
    workflow.set_entry_point("requirements_intake")

    # Phase 1: Linear flow for domain modeling
    workflow.add_edge("requirements_intake", "domain_model")
    workflow.add_edge("domain_model", "database_schema")

    # Phase 2: API and business logic (sequential)
    workflow.add_edge("database_schema", "api_contract")
    workflow.add_edge("api_contract", "business_logic_scaffolding")
    workflow.add_edge("business_logic_scaffolding", "validation_rules")

    # Phase 3: Security and testing
    workflow.add_edge("validation_rules", "security_review")

    # Conditional routing: If critical security flags, route early to checkpoint
    workflow.add_conditional_edges(
        "security_review",
        should_route_to_security_checkpoint,
        {
            True: "human_checkpoint",    # Critical issues - early checkpoint
            False: "unit_test_generation",  # No critical issues - continue to tests
        }
    )

    workflow.add_edge("unit_test_generation", "human_checkpoint")

    # Phase 4: Checkpoint and approval
    workflow.add_conditional_edges(
        "human_checkpoint",
        should_proceed_to_pr_description,
        {
            True: "pr_description",      # ✅ Approved
            False: "api_contract",       # ❌ Rejected - revise from api_contract
        }
    )

    # Phase 4: Execution (sequential)
    workflow.add_edge("pr_description", "code_review")
    workflow.add_edge("code_review", "api_publishing")

    # End state
    workflow.add_edge("api_publishing", END)

    return workflow


def compile_backend_workflow() -> object:
    """
    Compile the Backend Agent workflow for execution.

    Returns:
        Compiled workflow (runnable graph)
    """
    workflow_graph = create_backend_workflow()
    return workflow_graph.compile()


# ============================================================================
# WORKFLOW VISUALIZATION
# ============================================================================

def print_workflow_graph(compiled_graph: object = None) -> None:
    """Print ASCII representation of the workflow graph."""
    print("\n" + "="*80)
    print(" BACKEND AGENT LANGGRAPH WORKFLOW")
    print("="*80)

    graph_description = """
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BACKEND AGENT LANGGRAPH WORKFLOW                       │
└─────────────────────────────────────────────────────────────────────────────┘

                    REQUIREMENTS & DOMAIN MODELING PHASE
                                   │
                                   ▼
                          requirements_intake
                                   │
                                   ▼
                            domain_model
                                   │
                                   ▼
                          database_schema
                                   │
                    ┌──────────────────────────────────┐
                    │   API & BUSINESS LOGIC PHASE     │
                    ▼
                          api_contract
                                   │
                                   ▼
              business_logic_scaffolding
                                   │
                                   ▼
                         validation_rules
                                   │
                    ┌──────────────────────────────────┐
                    │  SECURITY & TESTING PHASE        │
                    ▼
                         security_review
                                   │
                    Critical Security Issues?
                     ✓ Yes      ✗ No
                     │           │
                     │           ▼
                     │    unit_test_generation
                     │           │
                     └──────┬────┘
                            ▼
            ┌──────────────────────────────┐
            │    CHECKPOINT: APPROVAL      │
            │  (Human review + approval)   │
            └──────────────────────────────┘
                 ✓ Approved    ✗ Rejected
                 │                │
                 ▼                │
            pr_description         │
                 │                │
                 ▼                │
             code_review          │
                 │                │
                 ▼                │
            api_publishing         │
                 │                │
                 └────────────────┘
                        │
                        ▼
                      (END)

LEGEND:
  ─────► Linear flow
  ✓/✗    Conditional routing based on human approval
  [ ]    Nodes (12 total)
  [ ]    Checkpoint (1 total)

NODE COUNT: 12 total (11 agents + 1 checkpoint)
CHECKPOINT: 1 (implementation approval with rejection loop)
CONDITIONAL ROUTES: 2 (security severity + approval gate)
"""

    print(graph_description)


# ============================================================================
# EXECUTION HELPER
# ============================================================================

def run_backend_workflow(
    user_stories: list = None,
    sprint_plan: dict = None,
    verbose: bool = True,
) -> BackendWorkflowState:
    """
    Run the Backend Agent workflow.

    Args:
        user_stories: List of UserStory objects from PO workflow
        sprint_plan: SprintPlan from EM workflow
        verbose: Print detailed logs during execution

    Returns:
        Final workflow state with API contract and artifacts
    """
    import json

    # Create and compile workflow
    compiled_workflow = compile_backend_workflow()

    # Initialize state
    initial_state = BackendWorkflowState(
        user_stories=user_stories or [],
        sprint_plan=sprint_plan,
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
        print(f"User Stories: {len(final_state.user_stories)}")
        print(f"Backend Requirements: {len(final_state.backend_requirements)}")
        print(f"Domain Model Entities: {len(final_state.domain_model.get('entities', []) if final_state.domain_model else 0)}")
        print(f"Database Tables: {len(final_state.db_schema.get('ddl_sql', '').split('CREATE TABLE') if final_state.db_schema else 0) - 1}")
        print(f"API Endpoints: {len(final_state.api_contract.get('endpoints', []) if final_state.api_contract else 0)}")
        print(f"Service Classes: {len(final_state.service_scaffolds)}")
        print(f"Validators: {len(final_state.validation_modules)}")
        print(f"Security Flags: {len(final_state.security_flags)}")
        print(f"Test Files: {len(final_state.test_files)}")
        print(f"Implementation Approved: {final_state.implementation_approved}")
        print(f"PR Description Generated: {final_state.pr_creation_complete}")
        print(f"Code Review Complete: {final_state.code_review_complete}")
        print(f"API Published: {final_state.api_published}")
        print(f"\nWorkflow Messages: {len(final_state.messages)}")
        print(f"Workflow Errors: {len(final_state.errors)}")

        if final_state.messages:
            print("\nWorkflow Log (last 5):")
            for msg in final_state.messages[-5:]:
                print(f"  [{msg['agent']}] {msg['message']}")

        if final_state.errors:
            print("\nErrors (last 3):")
            for error in final_state.errors[-3:]:
                print(f"  {error}")

    return final_state


# Export compiled workflow
backend_workflow = compile_backend_workflow


if __name__ == "__main__":
    # Example usage
    final_state = run_backend_workflow(verbose=True)

    # Save final state to file
    import json
    with open("backend_workflow_output.json", "w") as f:
        json.dump(final_state.to_dict(), f, indent=2, default=str)

    print("\n✅ Workflow output saved to backend_workflow_output.json")
