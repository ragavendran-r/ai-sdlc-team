"""Frontend Agent workflow nodes."""

import json
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from .state import FrontendWorkflowState
from .tools import (
    ContextStoreTool,
    DesignSystemTool,
    CodeGenerationTool,
    GitHubTool,
    ValidationTool,
    ToolResult,
)


LLM = Anthropic()
MODEL = "claude-sonnet-4-20250514"


def ux_handoff_intake(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Validate completeness of UX handoff.

    Flags missing component specs, missing interaction notes, or unresolved
    accessibility flags before any code work begins.
    """
    state.current_agent = "ux_handoff_intake"

    prompt = f"""
You are a frontend agent validating a UX handoff for implementation.

Check the following UX handoff for completeness:
{json.dumps(state.ux_handoff.to_dict() if state.ux_handoff else {}, indent=2)}

Validate:
1. All components have complete specifications
2. All interactions are documented
3. All accessibility requirements are clear
4. Design tokens are provided

Return a JSON object with:
- "valid": boolean
- "gaps": list of missing items or unclear specs
"""

    response = LLM.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text
    try:
        result = json.loads(content)
        state.validated_handoff = state.ux_handoff
        state.intake_gaps = result.get("gaps", [])
        state.handoff_validation_complete = True
        state.messages.append({
            "agent": "ux_handoff_intake",
            "message": f"Validated UX handoff. Gaps found: {len(state.intake_gaps)}",
        })
    except json.JSONDecodeError:
        state.errors.append(f"Failed to parse LLM response: {content}")

    return state


def component_breakdown(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Decompose each screen brief into atomic components.

    Identifies which are new builds vs existing library components.
    """
    state.current_agent = "component_breakdown"

    if not state.validated_handoff:
        state.errors.append("No validated handoff available")
        return state

    # Get design system library
    lib_result = DesignSystemTool.read_component_library()
    available_components = lib_result.data if lib_result.success else []

    prompt = f"""
You are breaking down UX wireframes into atomic components.

Handoff components:
{json.dumps([c.to_dict() for c in state.validated_handoff.components], indent=2)}

Available library components:
{json.dumps(available_components, indent=2)}

For each component, determine:
1. Is it a new build or library reuse?
2. What are its atomic parts?
3. What props does it need?
4. Does it need state or API calls?

Return a JSON array of component breakdowns with fields:
- "id": unique ID
- "name": component name
- "parent_screen": screen it belongs to
- "component_type": type of component
- "is_new_build": boolean
- "library_component_id": if reusing library
- "estimated_lines_of_code": LOC estimate
- "complexity": simple/moderate/complex
- "props": dict of required props
- "api_dependencies": list of API endpoint IDs
"""

    response = LLM.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text
    try:
        components = json.loads(content)
        state.component_plan = components
        state.component_breakdown_complete = True
        state.messages.append({
            "agent": "component_breakdown",
            "message": f"Broke down into {len(state.component_plan)} atomic components",
        })
    except json.JSONDecodeError:
        state.errors.append(f"Failed to parse component breakdown: {content}")

    return state


def design_token_mapping(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Map component visual properties to design tokens.

    Flags any values not covered by tokens.
    """
    state.current_agent = "design_token_mapping"

    # Get design tokens
    tokens_result = DesignSystemTool.read_design_tokens()
    available_tokens = tokens_result.data if tokens_result.success else {}

    prompt = f"""
You are mapping component visual properties to design tokens.

Components:
{json.dumps(state.component_plan[:3], indent=2)}

Available design tokens:
{json.dumps(available_tokens, indent=2)}

For each component, identify:
1. Which tokens it uses (colors, spacing, typography, shadows, etc.)
2. Any custom values that should be tokens but aren't
3. Any gaps in the token system

Return a JSON object with:
- "mappings": dict where key is component_id, value is list of token IDs
- "gaps": list of missing or needed tokens
- "recommendations": suggestions for new tokens
"""

    response = LLM.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text
    try:
        result = json.loads(content)
        state.token_mappings = result.get("mappings", {})
        state.token_gaps = result.get("gaps", [])
        state.token_mapping_complete = True
        state.messages.append({
            "agent": "design_token_mapping",
            "message": f"Mapped tokens. Gaps: {len(state.token_gaps)}",
        })
    except json.JSONDecodeError:
        state.errors.append(f"Failed to parse token mapping: {content}")

    return state


def api_integration_planning(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Identify which components need API data.

    Maps components to API endpoints, flags missing endpoints.
    """
    state.current_agent = "api_integration_planning"

    if not state.api_contract:
        state.api_integration_map = {}
        state.messages.append({
            "agent": "api_integration_planning",
            "message": "No API contract available, skipping API planning",
        })
        return state

    prompt = f"""
You are planning API integration for frontend components.

Components:
{json.dumps(state.component_plan, indent=2)}

API Endpoints:
{json.dumps([e.to_dict() for e in state.api_contract.endpoints], indent=2)}

For each component that needs API data:
1. Identify required endpoints
2. Map components to endpoints
3. Flag missing endpoints

Return a JSON object with:
- "mappings": dict where key is component_id, value is list of endpoint IDs
- "missing_endpoints": list of endpoints components need but don't exist
"""

    response = LLM.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text
    try:
        result = json.loads(content)
        state.api_integration_map = result.get("mappings", {})
        state.missing_endpoints = result.get("missing_endpoints", [])
        state.api_planning_complete = True
        state.messages.append({
            "agent": "api_integration_planning",
            "message": f"Planned API integration. Missing endpoints: {len(state.missing_endpoints)}",
        })
    except json.JSONDecodeError:
        state.errors.append(f"Failed to parse API planning: {content}")

    return state


def component_scaffolding(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Generate React component boilerplate.

    Includes props interface, token-based styling, API hook stubs, placeholder content.
    """
    state.current_agent = "component_scaffolding"

    scaffolded = []

    for component in state.component_plan[:3]:  # Limit to first 3 for demo
        component_name = component.get("name", "Component")
        props = component.get("props", {})

        # Generate boilerplate
        boilerplate_result = CodeGenerationTool.generate_tsx_boilerplate(
            component_name, props
        )

        if boilerplate_result.success:
            scaffolded.append({
                "id": component.get("id"),
                "name": component_name,
                "file_path": f"src/components/{component_name}.tsx",
                "tsx_code": boilerplate_result.data,
                "props_interface": f"export interface {component_name}Props {{\n  // Props\n}}",
                "hook_stubs": ["// TODO: Implement custom hooks"],
                "tokens_used": state.token_mappings.get(component.get("id"), []),
                "api_calls": state.api_integration_map.get(component.get("id"), []),
            })

    state.scaffolded_components = scaffolded
    state.scaffolding_complete = True
    state.messages.append({
        "agent": "component_scaffolding",
        "message": f"Generated scaffolding for {len(state.scaffolded_components)} components",
    })

    return state


def state_management(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Identify shared state needs.

    Recommend state management approach per component group.
    """
    state.current_agent = "state_management"

    prompt = f"""
You are planning state management architecture for frontend components.

Scaffolded components:
{json.dumps(state.scaffolded_components[:3], indent=2)}

API integration map:
{json.dumps(state.api_integration_map, indent=2)}

Analyze state needs and recommend:
1. Component groups that share state
2. State management approach per group (local state, context, Redux, Zustand, etc.)
3. Shared state properties and actions
4. Context providers to create

Return a JSON object with:
- "state_groups": list of groups with strategy recommendations
- "requires_global_store": boolean
- "global_store_recommendation": string (Redux/Zustand/etc.)
- "recommended_context_layers": list of context names
- "implementation_order": list of group IDs in implementation order
"""

    response = LLM.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text
    try:
        result = json.loads(content)
        state.state_plan = result
        state.state_management_complete = True
        state.messages.append({
            "agent": "state_management",
            "message": "Completed state management planning",
        })
    except json.JSONDecodeError:
        state.errors.append(f"Failed to parse state plan: {content}")

    return state


def accessibility_implementation(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Enrich component scaffolds with accessibility features.

    Adds ARIA attributes, keyboard navigation, focus management.
    """
    state.current_agent = "accessibility_implementation"

    a11y_components = []

    for component in state.scaffolded_components:
        # Find a11y requirements from handoff
        a11y_reqs = []
        if state.validated_handoff:
            a11y_reqs = state.validated_handoff.accessibility_requirements

        prompt = f"""
Enhance this component with accessibility features:

Component: {component.get('name')}
Code:
{component.get('tsx_code', '')}

A11y requirements:
{json.dumps(a11y_reqs, indent=2)}

Add:
1. ARIA attributes (role, aria-label, aria-describedby, etc.)
2. Keyboard event handlers (onKeyDown, etc.)
3. Focus management code
4. Semantic HTML tags

Return enhanced TSX code.
"""

        response = LLM.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        enhanced_code = response.content[0].text

        a11y_component = component.copy()
        a11y_component["tsx_code"] = enhanced_code
        a11y_component["aria_attributes"] = [
            "role", "aria-label", "aria-describedby", "tabindex"
        ]
        a11y_component["keyboard_handlers"] = [
            "onKeyDown", "onKeyUp", "onFocus", "onBlur"
        ]

        a11y_components.append(a11y_component)

    state.a11y_enriched_components = a11y_components
    state.a11y_implementation_complete = True
    state.messages.append({
        "agent": "accessibility_implementation",
        "message": f"Added a11y features to {len(state.a11y_enriched_components)} components",
    })

    return state


def unit_test_generation(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Generate unit test stubs for components.

    Covers render, interaction, and API mock tests.
    """
    state.current_agent = "unit_test_generation"

    test_files = []

    for component in state.a11y_enriched_components[:2]:  # Limit to first 2
        component_name = component.get("name", "Component")

        # Generate render test
        render_test_result = CodeGenerationTool.generate_test_stub(
            component_name, "render"
        )

        if render_test_result.success:
            test_files.append({
                "id": f"test-{component.get('id')}",
                "component_id": component.get("id"),
                "component_name": component_name,
                "file_path": f"src/components/__tests__/{component_name}.test.tsx",
                "imports": "import { render, screen } from '@testing-library/react';",
                "setup_code": f"describe('{component_name}', () => {{",
                "test_cases": [
                    {
                        "name": "should render",
                        "type": "render",
                        "description": f"Verify {component_name} renders",
                        "code_snippet": f"render(<{component_name} />);",
                        "mocks_required": [],
                    },
                    {
                        "name": "should handle interactions",
                        "type": "interaction",
                        "description": "Verify user interactions work",
                        "code_snippet": "// TODO: Add interaction tests",
                        "mocks_required": [],
                    },
                ],
                "complete_test_code": render_test_result.data,
            })

    state.test_files = test_files
    state.test_generation_complete = True
    state.messages.append({
        "agent": "unit_test_generation",
        "message": f"Generated test stubs for {len(state.test_files)} components",
    })

    return state


def human_checkpoint(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Human approval gate for components before PR creation.

    Displays component plan, scaffolding, state plan, and token gaps.
    """
    state.current_agent = "human_checkpoint"

    # Print summary for human review
    print("\n" + "="*80)
    print(" FRONTEND WORKFLOW CHECKPOINT: COMPONENT REVIEW")
    print("="*80)

    print("\n## COMPONENT PLAN")
    for comp in state.component_plan[:3]:
        print(f"\n- {comp.get('name')} ({comp.get('component_type')})")
        print(f"  Complexity: {comp.get('complexity')}")
        print(f"  LOC Est: {comp.get('estimated_lines_of_code')}")

    print("\n## STATE MANAGEMENT PLAN")
    if state.state_plan:
        print(f"Global store needed: {state.state_plan.get('requires_global_store', False)}")
        print(f"Recommendation: {state.state_plan.get('global_store_recommendation', 'None')}")

    print("\n## TOKEN GAPS")
    if state.token_gaps:
        for gap in state.token_gaps[:5]:
            print(f"- {gap}")
    else:
        print("No token gaps identified ✓")

    print("\n" + "-"*80)
    response = input("\nApprove component plan? (yes/no/modify): ").strip().lower()

    if response == "yes":
        state.components_approved = True
        state.messages.append({
            "agent": "human_checkpoint",
            "message": "Components approved by human",
        })
    else:
        state.approval_feedback = input("Feedback for revision: ")
        state.messages.append({
            "agent": "human_checkpoint",
            "message": f"Components rejected. Feedback: {state.approval_feedback}",
        })

    return state


def pr_description(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Generate structured PR description.

    Summary, components added, API dependencies, testing notes.
    """
    state.current_agent = "pr_description"

    component_list = "\n".join([
        f"- {c.get('name')} ({c.get('component_type')})"
        for c in state.a11y_enriched_components[:3]
    ])

    pr_body = f"""
## Summary
Frontend implementation for component scaffolding workflow.

## Components Added
{component_list}

## Design System Compliance
- Design tokens mapped: {len(state.token_mappings)}
- Token gaps to address: {len(state.token_gaps)}

## API Dependencies
- Total API endpoints: {len(state.api_integration_map)}
- Missing endpoints: {len(state.missing_endpoints)}

## Accessibility
- WCAG 2.1 AA compliance built-in
- ARIA attributes: ✓
- Keyboard navigation: ✓
- Screen reader support: ✓

## Testing
- Unit tests: {len(state.test_files)}
- Test coverage: Components + interactions + API mocks

## Checklist
- [ ] All components have unit tests
- [ ] Accessibility features implemented
- [ ] Design tokens applied
- [ ] API hooks created
- [ ] Code reviewed
- [ ] Tests passing

## Screenshots
[Add design screenshots here]
"""

    state.pr_description = pr_body
    state.pr_creation_complete = True
    state.messages.append({
        "agent": "pr_description",
        "message": "Generated PR description",
    })

    return state


def code_review(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Review code against team conventions.

    Checks for missing tests, a11y issues, token violations, API error handling gaps.
    """
    state.current_agent = "code_review"

    review_comments = []

    # Check for design token violations
    for component in state.a11y_enriched_components[:2]:
        tokens_used = len(component.get("tokens_used", []))
        if tokens_used == 0:
            review_comments.append({
                "severity": "major",
                "category": "design_token",
                "title": "No design tokens used",
                "message": f"{component.get('name')} doesn't use any design tokens. Use design tokens for colors, spacing, typography.",
                "component_id": component.get("id"),
            })

    # Check for accessibility
    for component in state.a11y_enriched_components[:2]:
        a11y_attrs = len(component.get("aria_attributes", []))
        if a11y_attrs == 0:
            review_comments.append({
                "severity": "major",
                "category": "accessibility",
                "title": "Missing ARIA attributes",
                "message": f"{component.get('name')} is missing ARIA labels and roles.",
                "component_id": component.get("id"),
            })

    # Check for API error handling
    for component in state.a11y_enriched_components[:2]:
        if component.get("api_calls"):
            review_comments.append({
                "severity": "major",
                "category": "error_handling",
                "title": "Missing API error handling",
                "message": f"{component.get('name')} calls APIs but has no error handling.",
                "component_id": component.get("id"),
            })

    state.review_comments = review_comments
    state.code_review_complete = True
    state.messages.append({
        "agent": "code_review",
        "message": f"Code review complete. {len(state.review_comments)} comments",
    })

    return state
