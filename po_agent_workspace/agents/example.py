#!/usr/bin/env python3
"""Example usage of the PO Agent workflow."""

from workflow import run_po_workflow, print_workflow_graph, compile_po_workflow
import json


def example_basic_execution():
    """Run a basic workflow execution."""
    print("\n" + "="*80)
    print(" EXAMPLE 1: Basic Workflow Execution")
    print("="*80)

    context = "Building a modern SaaS authentication system with email/password and OAuth support"

    final_state = run_po_workflow(
        initial_context=context,
        verbose=True,
    )

    # Save output
    with open("po_workflow_output.json", "w") as f:
        json.dump(final_state.to_dict(), f, indent=2)

    print("\n✅ Output saved to po_workflow_output.json")

    return final_state


def example_visualize_graph():
    """Visualize the workflow graph structure."""
    print("\n" + "="*80)
    print(" EXAMPLE 2: Workflow Graph Visualization")
    print("="*80)

    compiled = compile_po_workflow()
    print_workflow_graph(compiled)


def example_access_results(state):
    """Show how to access workflow results."""
    print("\n" + "="*80)
    print(" EXAMPLE 3: Accessing Workflow Results")
    print("="*80)

    print("\n📊 WORKFLOW RESULTS:\n")

    print(f"Generated Stories: {len(state.generated_stories)}")
    if state.generated_stories:
        for i, story in enumerate(state.generated_stories[:2], 1):
            print(f"\n  Story {i}:")
            print(f"    ID: {story.get('id')}")
            print(f"    Title: {story.get('title')}")
            print(f"    Role: {story.get('user_role')}")
            print(f"    Goal: {story.get('user_goal')}")

    print(f"\nEnriched Stories: {len(state.enriched_stories)}")
    if state.enriched_stories:
        story = state.enriched_stories[0]
        print("\n  First enriched story BDD criteria:")
        if story.get("bdd_criteria"):
            for scenario in story["bdd_criteria"][:2]:
                print(f"    - {scenario.get('scenario')}")

    print(f"\nPrioritized Stories: {len(state.prioritized_stories)}")
    if state.prioritized_stories:
        print("\n  Top 3 by priority:")
        for i, story in enumerate(sorted(
            state.prioritized_stories,
            key=lambda s: s.get('priority_rank', 999)
        )[:3], 1):
            print(f"    {i}. {story.get('title')} (Score: {story.get('priority_score', 'N/A'):.2f})")

    print(f"\nGroomed Backlog Themes: {len(state.themes)}")
    if state.themes:
        print(f"  Themes: {', '.join(state.themes)}")

    print(f"\nJira Tickets Created: {len(state.jira_tickets_created)}")
    if state.jira_tickets_created:
        print(f"  Tickets: {', '.join(state.jira_tickets_created[:5])}")

    print("\nQuality Issues:")
    print(f"  Ambiguities: {len(state.ambiguity_flags)}")
    print(f"  Conflicts: {len(state.conflict_flags)}")

    print("\nApprovals:")
    print(f"  Stories Approved: {'✅ Yes' if state.stories_approved else '❌ No'}")
    print(f"  Backlog Approved: {'✅ Yes' if state.backlog_approved else '❌ No'}")
    print(f"  Jira Sync Complete: {'✅ Yes' if state.jira_sync_complete else '❌ No'}")

    print("\nWorkflow Artifacts:")
    print(f"  Total Messages: {len(state.messages)}")
    print(f"  Total Errors: {len(state.errors)}")

    if state.messages:
        print("\n  Recent Messages:")
        for msg in state.messages[-3:]:
            print(f"    [{msg['agent']}] {msg['message']}")


def example_state_serialization(state):
    """Show state serialization capabilities."""
    print("\n" + "="*80)
    print(" EXAMPLE 4: State Serialization")
    print("="*80)

    state_dict = state.to_dict()

    print("\nState Dictionary Keys:")
    for key in sorted(state_dict.keys()):
        value = state_dict[key]
        if isinstance(value, list):
            print(f"  - {key}: List[{len(value)} items]")
        elif isinstance(value, dict):
            print(f"  - {key}: Dict[{len(value)} keys]")
        elif isinstance(value, str):
            preview = value[:50] + "..." if len(value) > 50 else value
            print(f"  - {key}: '{preview}'")
        elif isinstance(value, bool):
            print(f"  - {key}: {value}")
        else:
            print(f"  - {key}: {type(value).__name__}")

    # Show JSON serializability
    try:
        json_str = json.dumps(state_dict, indent=2)
        print(f"\n✅ State is JSON serializable ({len(json_str)} bytes)")
    except Exception as e:
        print(f"\n❌ State serialization failed: {e}")


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print(" PO AGENT WORKFLOW - EXAMPLES")
    print("="*80)

    # Example 1: Basic execution
    final_state = example_basic_execution()

    # Example 2: Visualize graph
    example_visualize_graph()

    # Example 3: Access results
    example_access_results(final_state)

    # Example 4: Serialization
    example_state_serialization(final_state)

    print("\n" + "="*80)
    print(" ALL EXAMPLES COMPLETED")
    print("="*80)


if __name__ == "__main__":
    main()
