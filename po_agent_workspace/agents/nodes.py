"""Agent nodes for PO Agent workflow."""

import os
from typing import Optional
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from .state import (
    PoWorkflowState,
    RawRequirement,
    StructuredRequirement,
    AmbiguityFlag,
    ConflictFlag,
)
from .tools import (
    StakeholderInterviewTool,
    RequirementsStructuringTool,
    AmbiguityDetectionTool,
    ConflictDetectionTool,
    StoryGenerationTool,
    AcceptanceCriteriaTool,
    PrioritizationTool,
    BacklogGroomingTool,
    JiraPopulationTool,
)

llm = ChatAnthropic(
    model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5"),
    temperature=float(os.getenv("CLAUDE_TEMPERATURE", "0.7")),
    max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", "2048")),
)


# ============================================================================
# NODE 1: STAKEHOLDER INTERVIEW
# ============================================================================

def stakeholder_interview(state: PoWorkflowState) -> PoWorkflowState:
    """
    Conduct conversational interview with stakeholders.

    Extracts requirements through natural conversation.
    """
    state.current_agent = "stakeholder_interview"

    # Use LLM to conduct interview
    interview_prompt = """You are a skilled product manager conducting a stakeholder interview.

Your task is to:
1. Ask clarifying questions about their needs
2. Extract specific requirements
3. Understand business context and priorities
4. Identify constraints and dependencies

Generate a realistic interview with 3-4 exchanges that would extract meaningful requirements.
Format the output as:
INTERVIEWER: [question]
STAKEHOLDER: [response]
...

Then provide a summary of key extracted requirements."""

    response = llm.invoke(interview_prompt)
    interview_output = response.content

    state.interview_notes = interview_output

    # Simulate extracted raw requirements
    raw_reqs = [
        RawRequirement(
            id="RAW-001",
            text="Users need to be able to log in with email and password",
            source="stakeholder_interview",
            timestamp=datetime.utcnow(),
        ),
        RawRequirement(
            id="RAW-002",
            text="Must support OAuth login with Google and GitHub",
            source="stakeholder_interview",
            timestamp=datetime.utcnow(),
        ),
        RawRequirement(
            id="RAW-003",
            text="Login must be fast and secure",
            source="stakeholder_interview",
            timestamp=datetime.utcnow(),
        ),
    ]

    state.raw_requirements.extend(raw_reqs)
    state.interview_complete = True
    state.add_message("stakeholder_interview", "Interview completed, requirements extracted")

    return state


# ============================================================================
# NODE 2: REQUIREMENTS EXTRACTION
# ============================================================================

def requirements_extraction(state: PoWorkflowState) -> PoWorkflowState:
    """
    Structure raw requirements into requirement objects.

    Converts unstructured interview notes into formal requirement specs.
    """
    state.current_agent = "requirements_extraction"

    # Use tool to structure requirements
    tool_result = RequirementsStructuringTool.extract_requirements(state.interview_notes)

    if not tool_result.success:
        state.add_error(f"Requirements extraction failed: {tool_result.error}")
        return state

    # Use LLM to further refine and structure
    refinement_prompt = f"""Given these raw requirements extracted from stakeholder interviews:
{[r.text for r in state.raw_requirements]}

Structure them into formal requirements with:
- Clear title
- Detailed description
- Category (functional, non-functional, constraint)
- Initial priority signal
- Effort signal

Output should be JSON array of requirements."""

    response = llm.invoke(refinement_prompt)

    # Create structured requirements
    structured_reqs = [
        StructuredRequirement(
            id="SR-001",
            title="Email/Password Authentication",
            description="Users must be able to authenticate using email and password credentials",
            category="functional",
            priority_signal="critical",
            effort_signal="medium",
        ),
        StructuredRequirement(
            id="SR-002",
            title="OAuth Social Login",
            description="Support OAuth login with Google and GitHub",
            category="functional",
            priority_signal="high",
            effort_signal="high",
        ),
        StructuredRequirement(
            id="SR-003",
            title="Login Performance",
            description="Login must complete within 2 seconds",
            category="non-functional",
            priority_signal="high",
            effort_signal="medium",
        ),
    ]

    state.structured_requirements.extend(structured_reqs)
    state.add_message("requirements_extraction", f"Structured {len(structured_reqs)} requirements")

    return state


# ============================================================================
# NODE 3: AMBIGUITY DETECTION
# ============================================================================

def ambiguity_detection(state: PoWorkflowState) -> PoWorkflowState:
    """
    Flag vague or unmeasurable requirements.

    Identifies requirements that need clarification.
    """
    state.current_agent = "ambiguity_detection"

    # Use tool to detect ambiguities
    req_dicts = [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
        }
        for r in state.structured_requirements
    ]

    tool_result = AmbiguityDetectionTool.detect_ambiguities(req_dicts)

    if tool_result.success and tool_result.data.get("ambiguities"):
        for amb in tool_result.data["ambiguities"]:
            flag = AmbiguityFlag(
                requirement_id=amb["requirement_id"],
                issue=amb["issue"],
                severity=amb["severity"],
                suggested_clarification=amb["suggested_clarification"],
            )
            state.ambiguity_flags.append(flag)

            # Mark requirement with ambiguity
            for req in state.structured_requirements:
                if req.id == amb["requirement_id"]:
                    req.ambiguities.append(amb["issue"])

    state.add_message(
        "ambiguity_detection",
        f"Detected {len(state.ambiguity_flags)} ambiguities",
    )

    return state


# ============================================================================
# NODE 4: CONFLICT DETECTION
# ============================================================================

def conflict_detection(state: PoWorkflowState) -> PoWorkflowState:
    """
    Find contradictions across requirements.

    Identifies conflicting or duplicate requirements.
    """
    state.current_agent = "conflict_detection"

    # Use tool to detect conflicts
    req_dicts = [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
        }
        for r in state.structured_requirements
    ]

    tool_result = ConflictDetectionTool.detect_conflicts(req_dicts)

    if tool_result.success and tool_result.data.get("conflicts"):
        for conflict in tool_result.data["conflicts"]:
            flag = ConflictFlag(
                requirement_ids=conflict["requirement_ids"],
                conflict_type=conflict["conflict_type"],
                description=conflict["description"],
                resolution=conflict.get("resolution"),
            )
            state.conflict_flags.append(flag)

            # Mark requirements with conflict
            for req in state.structured_requirements:
                if req.id in conflict["requirement_ids"]:
                    req.conflicts.append(
                        {
                            "conflicting_ids": conflict["requirement_ids"],
                            "type": conflict["conflict_type"],
                        }
                    )

    state.add_message(
        "conflict_detection",
        f"Detected {len(state.conflict_flags)} conflicts",
    )

    return state


# ============================================================================
# NODE 5: STORY GENERATION
# ============================================================================

def story_generation(state: PoWorkflowState) -> PoWorkflowState:
    """
    Produce UserStory schema objects from requirements.

    Converts requirements into user stories.
    """
    state.current_agent = "story_generation"

    # Use tool to generate stories
    req_dicts = [r.__dict__ for r in state.structured_requirements]

    tool_result = StoryGenerationTool.generate_stories(req_dicts)

    if tool_result.success:
        state.generated_stories.extend(tool_result.data.get("stories", []))

    # Use LLM to review and enhance stories
    review_prompt = f"""Review these generated user stories and ensure they follow best practices:
{state.generated_stories}

Provide feedback on:
1. Story clarity (3 sentence limit on description)
2. Acceptance criteria testability
3. Role/Goal/Value alignment
4. Estimate reasonableness"""

    response = llm.invoke(review_prompt)

    state.add_message(
        "story_generation",
        f"Generated {len(state.generated_stories)} user stories",
    )

    return state


# ============================================================================
# NODE 6: ACCEPTANCE CRITERIA
# ============================================================================

def acceptance_criteria(state: PoWorkflowState) -> PoWorkflowState:
    """
    Enrich stories with Given/When/Then acceptance criteria.

    Adds detailed BDD-style acceptance criteria to each story.
    """
    state.current_agent = "acceptance_criteria"

    # Use tool to enrich with BDD criteria
    tool_result = AcceptanceCriteriaTool.enrich_with_bdd_criteria(state.generated_stories)

    if tool_result.success:
        state.enriched_stories.extend(tool_result.data.get("enriched_stories", []))

    # Use LLM to validate BDD format
    validation_prompt = f"""Validate these BDD acceptance criteria for clarity and completeness:
{state.enriched_stories}

Check that each scenario has:
- Clear Given (setup/context)
- Clear When (action/trigger)
- Clear Then (expected outcome)"""

    response = llm.invoke(validation_prompt)

    state.add_message(
        "acceptance_criteria",
        f"Enriched {len(state.enriched_stories)} stories with BDD criteria",
    )

    return state


# ============================================================================
# NODE 7: PRIORITIZATION
# ============================================================================

def prioritization(state: PoWorkflowState) -> PoWorkflowState:
    """
    Score stories by business value and effort.

    Calculates priority based on value/effort ratio.
    """
    state.current_agent = "prioritization"

    # Use tool to prioritize
    tool_result = PrioritizationTool.score_and_prioritize(state.enriched_stories)

    if tool_result.success:
        state.prioritized_stories.extend(tool_result.data.get("prioritized_stories", []))

    # Use LLM to review priority reasoning
    reasoning_prompt = f"""Review the prioritization of these stories:
{state.prioritized_stories}

Provide business justification for the priority order and flag any concerns about dependencies or sequencing."""

    response = llm.invoke(reasoning_prompt)

    state.add_message(
        "prioritization",
        f"Prioritized {len(state.prioritized_stories)} stories",
    )

    return state


# ============================================================================
# NODE 8: BACKLOG GROOMING
# ============================================================================

def backlog_grooming(state: PoWorkflowState) -> PoWorkflowState:
    """
    Order and group stories into themes.

    Organizes stories into epics and sprints.
    """
    state.current_agent = "backlog_grooming"

    # Use tool to groom backlog
    tool_result = BacklogGroomingTool.groom_backlog(state.prioritized_stories)

    if tool_result.success:
        state.groomed_backlog.extend(tool_result.data.get("groomed_backlog", []))
        state.themes.extend(tool_result.data.get("themes", []))

    # Use LLM to review sprint organization
    review_prompt = f"""Review this backlog organization:
{state.groomed_backlog}

Provide feedback on:
1. Theme coherence
2. Sprint sizing and balance
3. Dependency ordering
4. Risk areas that might need earlier attention"""

    response = llm.invoke(review_prompt)

    state.add_message(
        "backlog_grooming",
        f"Groomed backlog into {len(state.themes)} themes",
    )

    return state


# ============================================================================
# NODE 9: JIRA POPULATION
# ============================================================================

def jira_population(state: PoWorkflowState) -> PoWorkflowState:
    """
    Stub node for writing stories to Jira API.

    In production, would create Jira tickets.
    """
    state.current_agent = "jira_population"

    # Use tool (stubbed) to create Jira tickets
    tool_result = JiraPopulationTool.create_jira_tickets(state.groomed_backlog)

    if tool_result.success:
        jira_data = tool_result.data
        state.jira_tickets_created.extend([t["id"] for t in jira_data.get("jira_tickets", [])])
        state.jira_sync_complete = True

    state.add_message(
        "jira_population",
        f"Created {len(state.jira_tickets_created)} Jira tickets",
    )

    return state
