"""Human checkpoint nodes for approval gates in the workflow."""

from typing import Optional
from .state import PoWorkflowState
from .tools import ToolResult
import json


class HumanCheckpoint:
    """Base class for human approval checkpoints."""

    @staticmethod
    def print_section_header(title: str) -> None:
        """Print formatted section header."""
        print("\n" + "="*80)
        print(f" {title}")
        print("="*80 + "\n")

    @staticmethod
    def print_stories_summary(stories: list) -> None:
        """Print summary of generated stories."""
        for i, story in enumerate(stories, 1):
            print(f"\n[Story {i}]")
            print(f"  ID: {story.get('id', 'N/A')}")
            print(f"  Title: {story.get('title', 'N/A')}")
            print(f"  User Role: {story.get('user_role', 'N/A')}")
            print(f"  User Goal: {story.get('user_goal', 'N/A')}")
            print(f"  Business Value: {story.get('business_value', 'N/A')}")
            print(f"  Priority: {story.get('priority', 'N/A').upper() if story.get('priority') else 'N/A'}")
            print(f"  Complexity: {story.get('estimated_complexity', 'N/A').upper() if story.get('estimated_complexity') else 'N/A'}")

            if story.get("acceptance_criteria"):
                print(f"  Acceptance Criteria:")
                for criterion in story.get("acceptance_criteria", []):
                    print(f"    - {criterion}")

            if story.get("bdd_criteria"):
                print(f"  BDD Scenarios:")
                for scenario in story.get("bdd_criteria", []):
                    print(f"    - {scenario.get('scenario', 'N/A')}")

    @staticmethod
    def print_backlog_summary(backlog: list, themes: list) -> None:
        """Print summary of groomed backlog."""
        print(f"\nThemes ({len(themes)}):")
        for theme in themes:
            print(f"  - {theme}")

        print(f"\nBacklog Themes ({len(backlog)}):")
        for theme_group in backlog:
            theme_name = theme_group.get("theme", "Unknown")
            epic = theme_group.get("epic", "N/A")
            stories = theme_group.get("stories", [])
            total_effort = theme_group.get("total_effort_hours", 0)

            print(f"\n  [{theme_name}] Epic: {epic}")
            print(f"  Effort: {total_effort}h | Stories: {len(stories)}")

            for story in stories[:3]:  # Show first 3 stories per theme
                print(f"    - {story.get('id', 'N/A')}: {story.get('title', 'N/A')}")

            if len(stories) > 3:
                print(f"    ... and {len(stories) - 3} more")

    @staticmethod
    def get_user_approval(prompt: str) -> bool:
        """
        Get user approval via CLI.

        Returns:
            True if user approves (y), False if rejects (n)
        """
        while True:
            response = input(f"\n{prompt} (y/n): ").strip().lower()
            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no"]:
                return False
            else:
                print("Please enter 'y' or 'n'")

    @staticmethod
    def get_user_notes(prompt: str) -> str:
        """
        Get user notes/feedback via CLI.

        Returns:
            User input text (or empty string if no input)
        """
        print(f"\n{prompt}")
        print("(Enter text, press Enter twice to finish, or just press Enter to skip)")

        lines = []
        empty_count = 0

        while True:
            line = input()
            if not line:
                empty_count += 1
                if empty_count >= 1:
                    break
            else:
                empty_count = 0
                lines.append(line)

        return "\n".join(lines)


# ============================================================================
# CHECKPOINT 1: STORY GENERATION APPROVAL
# ============================================================================

def checkpoint_story_generation(state: PoWorkflowState) -> PoWorkflowState:
    """
    Human checkpoint after story generation.

    Displays generated stories and waits for approval before acceptance criteria enrichment.
    """
    state.current_agent = "checkpoint_story_generation"

    # In web mode the interface pauses the graph before this node and injects the
    # decision (stories_approved / generated_stories) via update_state, so we skip
    # the blocking CLI prompt and pass through.
    if state.web_mode:
        return state

    # Display section header
    HumanCheckpoint.print_section_header("HUMAN CHECKPOINT: REVIEW GENERATED STORIES")

    # Print summary
    print("\nGenerated Stories for Review:")
    print("-" * 80)
    HumanCheckpoint.print_stories_summary(state.generated_stories)

    # Quality summary
    print("\n" + "-" * 80)
    print(f"\nSummary:")
    print(f"  Total Stories: {len(state.generated_stories)}")

    if state.ambiguity_flags:
        print(f"  Ambiguities Detected: {len(state.ambiguity_flags)}")
        for flag in state.ambiguity_flags[:3]:
            print(f"    - {flag.requirement_id}: {flag.issue}")

    if state.conflict_flags:
        print(f"  Conflicts Detected: {len(state.conflict_flags)}")
        for flag in state.conflict_flags[:3]:
            print(f"    - {', '.join(flag.requirement_ids)}: {flag.conflict_type}")

    # Get approval
    approved = HumanCheckpoint.get_user_approval(
        "Do you approve these stories? Proceed to enrichment with acceptance criteria?"
    )

    state.stories_approved = approved

    if approved:
        print("\n✅ Stories approved. Proceeding to acceptance criteria enrichment...")
        state.add_message("checkpoint_story_generation", "Stories approved by human")
    else:
        # Get feedback
        notes = HumanCheckpoint.get_user_notes(
            "Please provide feedback for story revisions:"
        )
        state.approval_notes = notes
        print("\n⏸️  Stories rejected. Feedback recorded for revision.")
        state.add_message("checkpoint_story_generation", f"Stories rejected. Feedback: {notes}")

    return state


# ============================================================================
# CHECKPOINT 2: BACKLOG GROOMING APPROVAL
# ============================================================================

def checkpoint_backlog_grooming(state: PoWorkflowState) -> PoWorkflowState:
    """
    Human checkpoint after backlog grooming.

    Displays groomed backlog and waits for approval before Jira population.
    """
    state.current_agent = "checkpoint_backlog_grooming"

    # In web mode the single browser review covers story approval; the backlog
    # checkpoint auto-approves so the graph can run through to completion.
    if state.web_mode:
        state.backlog_approved = True
        state.add_message("checkpoint_backlog_grooming", "Auto-approved (web mode)")
        return state

    # Display section header
    HumanCheckpoint.print_section_header("HUMAN CHECKPOINT: REVIEW GROOMED BACKLOG")

    # Print prioritization details
    print("\nPrioritized Stories:")
    print("-" * 80)
    print(f"\n{'ID':<10} {'Title':<40} {'Priority':<10} {'Effort':<8} {'Score':<8}")
    print("-" * 80)

    for story in state.prioritized_stories[:10]:
        story_id = story.get("id", "N/A")
        title = story.get("title", "N/A")[:37] + "..." if len(story.get("title", "")) > 40 else story.get("title", "N/A")
        priority = story.get("priority_rank", "N/A")
        effort = f"{story.get('effort_estimate_hours', 'N/A')}h"
        score = f"{story.get('priority_score', 'N/A'):.2f}" if isinstance(story.get('priority_score'), (int, float)) else "N/A"

        print(f"{story_id:<10} {title:<40} {priority:<10} {effort:<8} {score:<8}")

    if len(state.prioritized_stories) > 10:
        print(f"... and {len(state.prioritized_stories) - 10} more stories")

    # Print backlog organization
    print("\n" + "-" * 80)
    print("\nBacklog Organization:")
    print("-" * 80)
    HumanCheckpoint.print_backlog_summary(state.groomed_backlog, state.themes)

    # Statistics
    total_stories = sum(len(theme.get("stories", [])) for theme in state.groomed_backlog)
    total_effort = sum(theme.get("total_effort_hours", 0) for theme in state.groomed_backlog)

    print("\n" + "-" * 80)
    print(f"\nStatistics:")
    print(f"  Total Stories: {total_stories}")
    print(f"  Total Effort: {total_effort}h")
    print(f"  Themes: {len(state.themes)}")

    if state.conflict_flags:
        print(f"  Unresolved Conflicts: {len(state.conflict_flags)}")

    # Get approval
    approved = HumanCheckpoint.get_user_approval(
        "Do you approve this backlog organization? Proceed to Jira population?"
    )

    state.backlog_approved = approved

    if approved:
        print("\n✅ Backlog approved. Proceeding to Jira ticket creation...")
        state.add_message("checkpoint_backlog_grooming", "Backlog approved by human")
    else:
        # Get feedback
        notes = HumanCheckpoint.get_user_notes(
            "Please provide feedback for backlog reorganization:"
        )
        state.backlog_approval_notes = notes
        print("\n⏸️  Backlog rejected. Feedback recorded for revision.")
        state.add_message("checkpoint_backlog_grooming", f"Backlog rejected. Feedback: {notes}")

    return state


# ============================================================================
# GUARD FUNCTIONS FOR CONDITIONAL ROUTING
# ============================================================================

def should_proceed_to_acceptance_criteria(state: PoWorkflowState) -> bool:
    """
    Guard function: proceed to acceptance criteria only if stories approved.
    """
    return state.stories_approved


def should_proceed_to_jira(state: PoWorkflowState) -> bool:
    """
    Guard function: proceed to Jira only if backlog approved.
    """
    return state.backlog_approved


def should_revise_stories(state: PoWorkflowState) -> bool:
    """
    Guard function: return to story generation if rejected.
    """
    return not state.stories_approved


def should_revise_backlog(state: PoWorkflowState) -> bool:
    """
    Guard function: return to backlog grooming if rejected.
    """
    return not state.backlog_approved
