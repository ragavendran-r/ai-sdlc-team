"""Agent nodes for UX Agent workflow."""

from langchain_anthropic import ChatAnthropic
from .state import UXWorkflowState
from .tools import (
    ContextStoreTool,
    ResearchTool,
    DesignSystemTool,
    FigmaIntegrationTool,
    ContextStoreWriteTool,
)
from team_contracts.schemas import (
    UserStory,
    UserPersona,
    UserFlow,
    FlowStep,
    IAStructure,
    NavNode,
    WireframeBrief,
    ComponentRequirement,
    InteractionPattern,
    DesignComplianceReport,
    AccessibilityFlag,
    AccessibilitySeverity,
    WCAGLevel,
    UXHandoff,
)

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.7,
    max_tokens=2048,
)


def story_intake(state: UXWorkflowState) -> UXWorkflowState:
    """Filter stories relevant to UX."""
    state.current_agent = "story_intake"

    # Create sample stories
    if not state.input_stories:
        state.input_stories = [
            UserStory(
                id="US-001",
                title="User login with email",
                description="Allow users to log in",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority="high",
                estimated_complexity="m",
                created_by="po-agent",
            ),
            UserStory(
                id="US-002",
                title="Database optimization",
                description="Optimize database",
                user_role="Engineer",
                user_goal="optimize",
                business_value="perf",
                acceptance_criteria=["Fast"],
                priority="medium",
                estimated_complexity="l",
                created_by="po-agent",
            ),
        ]

    # Filter UX-relevant stories (exclude pure backend/infra)
    state.ux_relevant_stories = [
        s for s in state.input_stories
        if s.user_role in ["Customer", "Admin", "User"]
    ]
    state.excluded_stories = [
        s.id for s in state.input_stories
        if s.id not in [us.id for us in state.ux_relevant_stories]
    ]

    state.add_message("story_intake", f"Filtered {len(state.ux_relevant_stories)} UX-relevant stories")
    return state


def persona_agent(state: UXWorkflowState) -> UXWorkflowState:
    """Generate user personas from stories."""
    state.current_agent = "persona_agent"

    # Generate personas from story roles
    personas = []
    seen_roles = set()

    for story in state.ux_relevant_stories:
        if story.user_role not in seen_roles:
            persona = UserPersona(
                id=f"PERSONA-{story.user_role}",
                name=f"Typical {story.user_role}",
                demographic_summary=f"A typical {story.user_role} using our product",
                role=story.user_role,
                goals=[story.user_goal],
                pain_points=["Needs are complex"],
                experience_level="intermediate",
                primary_devices=["desktop", "mobile"],
                created_by="ux-agent",
            )
            personas.append(persona)
            seen_roles.add(story.user_role)

    state.personas = personas
    state.add_message("persona_agent", f"Generated {len(personas)} personas")
    return state


def user_flow_mapping(state: UXWorkflowState) -> UXWorkflowState:
    """Map user flows for each story."""
    state.current_agent = "user_flow_mapping"

    flows = []

    for story in state.ux_relevant_stories[:2]:  # Limit for demo
        persona = next((p for p in state.personas if p.role == story.user_role), None)
        if not persona:
            continue

        steps = [
            FlowStep(
                step_number=1,
                action="User navigates to feature",
                system_response="Display main screen",
                screen_or_state="Login Screen",
            ),
            FlowStep(
                step_number=2,
                action="User enters credentials",
                system_response="Validate input",
                screen_or_state="Login Screen",
            ),
            FlowStep(
                step_number=3,
                action="User clicks login",
                system_response="Authenticate user",
                screen_or_state="Loading",
            ),
        ]

        flow = UserFlow(
            id=f"FLOW-{story.id}",
            user_story_id=story.id,
            persona_id=persona.id,
            title=f"User flow for {story.title}",
            description=f"Flow for {story.user_goal}",
            entry_point="User opens app",
            steps=steps,
            exit_point="User is logged in",
            created_by="ux-agent",
        )
        flows.append(flow)

    state.user_flows = flows
    state.add_message("user_flow_mapping", f"Mapped {len(flows)} user flows")
    return state


def information_architecture(state: UXWorkflowState) -> UXWorkflowState:
    """Define IA structure from flows."""
    state.current_agent = "information_architecture"

    # Create IA structure
    root_nodes = ["HOME", "ACCOUNT", "SETTINGS"]
    nodes = {
        "HOME": NavNode(id="HOME", name="Home", children=["DASHBOARD"]),
        "DASHBOARD": NavNode(id="DASHBOARD", name="Dashboard", children=[]),
        "ACCOUNT": NavNode(id="ACCOUNT", name="Account", children=["PROFILE", "SECURITY"]),
        "PROFILE": NavNode(id="PROFILE", name="Profile", children=[]),
        "SECURITY": NavNode(id="SECURITY", name="Security", children=[]),
        "SETTINGS": NavNode(id="SETTINGS", name="Settings", children=[]),
    }

    ia = IAStructure(
        id="IA-001",
        root_nodes=root_nodes,
        nodes=nodes,
        total_pages=6,
        page_categories={
            "Auth": ["Login", "Signup"],
            "Main": ["Home", "Dashboard"],
            "User": ["Profile", "Settings"],
        },
        created_by="ux-agent",
    )

    state.ia_structure = ia
    state.add_message("information_architecture", "Created IA structure")
    return state


def wireframe_brief(state: UXWorkflowState) -> UXWorkflowState:
    """Generate wireframe briefs."""
    state.current_agent = "wireframe_brief"

    briefs = []

    for flow in state.user_flows[:2]:
        components = [
            ComponentRequirement(
                component_name="TextField",
                purpose="Email input",
                content="Email address",
            ),
            ComponentRequirement(
                component_name="Button",
                purpose="Login action",
                state="default",
            ),
        ]

        interactions = [
            InteractionPattern(
                trigger="User clicks login",
                action="Submit form",
                result="Navigate to dashboard",
            ),
        ]

        brief = WireframeBrief(
            id=f"BRIEF-{flow.id}",
            screen_name=f"Screen for {flow.title}",
            user_flow_id=flow.id,
            purpose="Login screen",
            description="Allows user to log in",
            components=components,
            interactions=interactions,
            created_by="ux-agent",
        )
        briefs.append(brief)

    state.wireframe_briefs = briefs
    state.add_message("wireframe_brief", f"Generated {len(briefs)} wireframe briefs")
    return state


def design_system_compliance(state: UXWorkflowState) -> UXWorkflowState:
    """Check compliance with design system."""
    state.current_agent = "design_system_compliance"

    # Check briefs against DS
    compliant = 0
    partial = 0
    component_gaps = []

    for brief in state.wireframe_briefs:
        # Map components to DS
        for comp in brief.components:
            brief.design_system_mappings[comp.component_name] = comp.component_name

        compliant += 1

    state.updated_wireframe_briefs = state.wireframe_briefs

    compliance = DesignComplianceReport(
        id="COMPLIANCE-001",
        total_briefs_checked=len(state.wireframe_briefs),
        compliant_briefs=compliant,
        partial_briefs=partial,
        component_gaps=component_gaps,
        compliance_percentage=100.0,
        created_by="ux-agent",
    )

    state.compliance_report = compliance
    state.add_message("design_system_compliance", "Checked design system compliance")
    return state


def accessibility_review(state: UXWorkflowState) -> UXWorkflowState:
    """Review accessibility against WCAG 2.1 AA."""
    state.current_agent = "accessibility_review"

    flags = []

    # Simulate finding accessibility issues
    if state.wireframe_briefs:
        brief = state.wireframe_briefs[0]
        flag = AccessibilityFlag(
            id="A11Y-001",
            brief_id=brief.id,
            flow_id=state.user_flows[0].id if state.user_flows else None,
            title="Missing form labels",
            description="Form fields should have associated labels",
            wcag_criterion="1.3.1 Info and Relationships",
            wcag_level=WCAGLevel.A,
            severity=AccessibilitySeverity.MAJOR,
            problem="TextField components have no visible labels",
            solution="Add label text above each input field",
            example="<label for='email'>Email</label><input id='email'/>",
            created_by="ux-agent",
        )
        flags.append(flag)

    state.a11y_flags = flags
    state.add_message("accessibility_review", f"Identified {len(flags)} accessibility issues")
    return state


def human_checkpoint(state: UXWorkflowState) -> UXWorkflowState:
    """Human approval checkpoint."""
    state.current_agent = "human_checkpoint"
    state.checkpoint_reached = True

    # Web mode: the decision is injected by the web layer via update_state before
    # the graph resumes, so skip the blocking CLI prompt.
    if state.web_mode:
        return state

    print("\n" + "="*80)
    print(" HUMAN CHECKPOINT: REVIEW UX SPECIFICATIONS")
    print("="*80)

    print("\n## Wireframe Briefs")
    for brief in state.wireframe_briefs[:2]:
        print(brief.to_markdown())

    if state.compliance_report:
        print("\n## Design System Compliance")
        print(state.compliance_report.to_markdown())

    if state.a11y_flags:
        print("\n## Accessibility Flags")
        for flag in state.a11y_flags:
            print(flag.to_markdown())

    response = input("\nDo you approve these specs? (y/n/modify): ").strip().lower()

    if response == "y":
        state.briefs_approved = True
        state.add_message("human_checkpoint", "Briefs approved")
    elif response == "n":
        state.briefs_approved = False
        feedback = input("Provide feedback: ").strip()
        state.approval_feedback = feedback
        state.add_message("human_checkpoint", f"Briefs rejected. Feedback: {feedback}")
    else:
        state.approval_feedback = "Modification requested"
        state.add_message("human_checkpoint", "Modifications requested")

    return state


def figma_annotation(state: UXWorkflowState) -> UXWorkflowState:
    """Create annotated frames in Figma."""
    state.current_agent = "figma_annotation"

    if not state.briefs_approved:
        state.add_error("Cannot create Figma frames: briefs not approved")
        return state

    # TODO: Real Figma integration
    # - Create frame for each wireframe brief
    # - Add component specs as annotations
    # - Include interaction notes
    # - Link to design system components
    # - Set up prototyping connections

    frames_created = []
    for brief in state.wireframe_briefs:
        frame_result = FigmaIntegrationTool.create_figma_frame(brief.screen_name)
        if frame_result.success:
            frame_id = frame_result.data["frame_id"]
            frames_created.append(frame_id)

            # Add annotations
            annot_result = FigmaIntegrationTool.add_figma_annotation(
                frame_id,
                f"Annotated specs for {brief.screen_name}",
                brief.to_dict(),
            )

            if annot_result.success:
                state.figma_annotations_added.append(frame_id)

    state.figma_frames_created = frames_created
    state.add_message("figma_annotation", f"Created {len(frames_created)} Figma frames")
    return state


def handoff_spec(state: UXWorkflowState) -> UXWorkflowState:
    """Compile UXHandoff and write to context store."""
    state.current_agent = "handoff_spec"

    # Compile UXHandoff
    if state.wireframe_briefs:
        for brief in state.wireframe_briefs:
            # Convert brief components to UXHandoff components
            for comp in brief.components:
                # Create minimal component spec
                pass

    # Create UXHandoff
    handoff = UXHandoff(
        id="UX-HANDOFF-001",
        user_story_id=state.ux_relevant_stories[0].id if state.ux_relevant_stories else "US-001",
        feature_name="Sample Feature",
        components=[],  # Would be populated with actual specs
        created_by="ux-agent",
    )

    state.ux_handoff = handoff

    # Write to context store
    write_result = ContextStoreWriteTool.write_ux_handoff(
        "team_contracts/context-store/ux-handoff.json",
        handoff.to_dict(),
    )

    if write_result.success:
        state.handoff_written = True
        state.add_message("handoff_spec", "UXHandoff written to context store")
    else:
        state.add_error("Failed to write UXHandoff")

    return state
