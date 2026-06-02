"""DesignDecision contract: Architecture Decision Records (ADR) format."""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class DecisionStatus(str, Enum):
    """Status of a decision."""
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class DecisionCategory(str, Enum):
    """Category of decision."""
    ARCHITECTURE = "architecture"
    DATA_MODEL = "data_model"
    API_DESIGN = "api_design"
    UI_UX = "ui_ux"
    INFRASTRUCTURE = "infrastructure"
    PROCESS = "process"
    TECHNOLOGY_CHOICE = "technology_choice"
    SECURITY = "security"
    PERFORMANCE = "performance"


class DecisionImpact(str, Enum):
    """Impact scope of decision."""
    LOCAL = "local"           # Affects single component/module
    FEATURE = "feature"       # Affects entire feature
    SYSTEM = "system"         # Affects multiple features/systems
    ORGANIZATION = "organization"  # Affects team practices/processes


class Alternative(BaseModel):
    """An alternative considered but not chosen."""

    name: str = Field(..., description="Name of alternative approach")
    description: str = Field(..., description="Detailed description of this approach")
    pros: List[str] = Field(default_factory=list, description="Advantages")
    cons: List[str] = Field(default_factory=list, description="Disadvantages")
    estimated_effort: Optional[str] = Field(
        default=None,
        description="Estimated effort to implement (e.g., '10 hours', '2 sprints')"
    )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "pros": self.pros,
            "cons": self.cons,
            "estimated_effort": self.estimated_effort,
        }


class Consequence(BaseModel):
    """A consequence of the chosen decision."""

    type: str = Field(
        ...,
        description="Type of consequence (performance, maintenance, scalability, etc.)"
    )
    description: str = Field(..., description="What is the consequence?")
    is_positive: bool = Field(..., description="Is this a positive consequence?")
    mitigation: Optional[str] = Field(
        default=None,
        description="How can we mitigate negative consequences?"
    )

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "description": self.description,
            "is_positive": self.is_positive,
            "mitigation": self.mitigation,
        }


class DesignDecision(BaseModel):
    """
    DesignDecision represents an important decision made during development.

    Follows the Architecture Decision Record (ADR) format for documentation.
    Can be created by any workflow when a significant decision is made.
    """

    id: str = Field(..., description="Unique decision identifier (e.g., 'ADR-001')")
    title: str = Field(..., description="Short, descriptive title", min_length=5)
    category: DecisionCategory = Field(..., description="Category of this decision")
    impact: DecisionImpact = Field(..., description="Scope of impact")

    # Status
    status: DecisionStatus = Field(default=DecisionStatus.PROPOSED, description="Current status")

    # The decision
    context: str = Field(
        ...,
        description="What is the issue or problem we're addressing?",
        min_length=10
    )
    decision: str = Field(
        ...,
        description="What is the decision? State it clearly.",
        min_length=10
    )
    rationale: str = Field(
        ...,
        description="Why did we make this decision? What are the key reasons?",
        min_length=10
    )

    # Alternatives considered
    alternatives: List[Alternative] = Field(
        default_factory=list,
        description="Other options we considered and why we didn't choose them"
    )

    # Consequences
    consequences: List[Consequence] = Field(
        default_factory=list,
        description="Positive and negative consequences of this decision"
    )

    # Trade-offs
    trade_offs: Optional[str] = Field(
        default=None,
        description="What are we trading off? (speed vs. maintainability, etc.)"
    )

    # Affected areas
    affects_areas: List[str] = Field(
        default_factory=list,
        description="What parts of the system are affected? (e.g., ['frontend', 'api', 'database'])"
    )

    # Related decisions
    related_decisions: List[str] = Field(
        default_factory=list,
        description="IDs of related decisions"
    )

    # Implementation
    implementation_notes: Optional[str] = Field(
        default=None,
        description="How do we implement this? What needs to happen?"
    )

    # Follow-up
    review_date: Optional[datetime] = Field(
        default=None,
        description="When should we review this decision?"
    )

    follow_up_actions: List[str] = Field(
        default_factory=list,
        description="Actions needed to implement or validate this decision"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(
        ...,
        description="Agent that created this decision record"
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="Agent that approved this decision"
    )
    superseded_by: Optional[str] = Field(
        default=None,
        description="If superseded, ID of the decision that replaces this one"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Tags for easy searching (e.g., 'authentication', 'performance')"
    )

    @field_validator('consequences')
    @classmethod
    def validate_consequences(cls, v: List[Consequence]) -> List[Consequence]:
        """Ensure we have both positive and negative consequences documented."""
        # Note: we don't enforce this, just ensure they're there
        return v

    def get_positive_consequences(self) -> List[Consequence]:
        """Get only positive consequences."""
        return [c for c in self.consequences if c.is_positive]

    def get_negative_consequences(self) -> List[Consequence]:
        """Get only negative consequences."""
        return [c for c in self.consequences if not c.is_positive]

    def to_markdown(self) -> str:
        """Convert to ADR-style Markdown document."""
        lines = [
            f"# {self.id}: {self.title}",
            "",
            f"**Date:** {self.created_at.strftime('%Y-%m-%d')}",
            f"**Status:** {self.status.value.upper()}",
            f"**Category:** {self.category.value.replace('_', ' ').title()}",
            f"**Impact:** {self.impact.value.upper()}",
        ]

        if self.approved_by:
            lines.append(f"**Approved By:** {self.approved_by}")

        if self.superseded_by:
            lines.append(f"⚠️ **Superseded By:** {self.superseded_by}")

        lines.extend([
            "",
            "## Context",
            "",
            self.context,
        ])

        lines.extend([
            "",
            "## Decision",
            "",
            self.decision,
        ])

        lines.extend([
            "",
            "## Rationale",
            "",
            self.rationale,
        ])

        if self.trade_offs:
            lines.extend([
                "",
                "## Trade-offs",
                "",
                self.trade_offs,
            ])

        if self.alternatives:
            lines.extend([
                "",
                "## Alternatives Considered",
                "",
            ])

            for alt in self.alternatives:
                lines.extend([
                    f"### {alt.name}",
                    alt.description,
                    "",
                ])

                if alt.pros:
                    lines.append("**Pros:**")
                    for pro in alt.pros:
                        lines.append(f"- {pro}")
                    lines.append("")

                if alt.cons:
                    lines.append("**Cons:**")
                    for con in alt.cons:
                        lines.append(f"- {con}")
                    lines.append("")

                if alt.estimated_effort:
                    lines.append(f"**Effort:** {alt.estimated_effort}")
                    lines.append("")

        # Consequences
        positive = self.get_positive_consequences()
        negative = self.get_negative_consequences()

        if positive or negative:
            lines.extend([
                "",
                "## Consequences",
                "",
            ])

            if positive:
                lines.append("### Positive")
                for consequence in positive:
                    lines.extend([
                        f"- **{consequence.type}:** {consequence.description}",
                    ])
                    if consequence.mitigation:
                        lines.append(f"  *Mitigation: {consequence.mitigation}*")
                lines.append("")

            if negative:
                lines.append("### Negative")
                for consequence in negative:
                    lines.extend([
                        f"- **{consequence.type}:** {consequence.description}",
                    ])
                    if consequence.mitigation:
                        lines.append(f"  *Mitigation: {consequence.mitigation}*")
                lines.append("")

        if self.affects_areas:
            lines.extend([
                "## Affected Areas",
                "",
            ])
            for area in self.affects_areas:
                lines.append(f"- {area}")
            lines.append("")

        if self.implementation_notes:
            lines.extend([
                "## Implementation",
                "",
                self.implementation_notes,
                "",
            ])

        if self.follow_up_actions:
            lines.extend([
                "## Follow-up Actions",
                "",
            ])
            for action in self.follow_up_actions:
                lines.append(f"- [ ] {action}")
            lines.append("")

        if self.related_decisions:
            lines.extend([
                "## Related Decisions",
                "",
            ])
            for decision_id in self.related_decisions:
                lines.append(f"- {decision_id}")
            lines.append("")

        if self.tags:
            lines.extend([
                "## Tags",
                "",
                " ".join(f"`{tag}`" for tag in self.tags),
                "",
            ])

        lines.extend([
            "---",
            "",
            f"**Created:** {self.created_at.isoformat()}",
            f"**Last Updated:** {self.updated_at.isoformat()}",
            f"**Created By:** {self.created_by}",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "impact": self.impact.value,
            "status": self.status.value,
            "context": self.context,
            "decision": self.decision,
            "rationale": self.rationale,
            "alternatives": [a.to_dict() for a in self.alternatives],
            "consequences": [c.to_dict() for c in self.consequences],
            "trade_offs": self.trade_offs,
            "affects_areas": self.affects_areas,
            "related_decisions": self.related_decisions,
            "implementation_notes": self.implementation_notes,
            "review_date": self.review_date.isoformat() if self.review_date else None,
            "follow_up_actions": self.follow_up_actions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "superseded_by": self.superseded_by,
            "tags": self.tags,
        }


if __name__ == "__main__":
    decision = DesignDecision(
        id="ADR-001",
        title="Use JWT tokens for API authentication",
        category=DecisionCategory.API_DESIGN,
        impact=DecisionImpact.SYSTEM,
        context=(
            "Our application needs to authenticate API requests from the frontend. "
            "We need a stateless solution that scales across multiple servers."
        ),
        decision=(
            "We will use JWT (JSON Web Tokens) for API authentication. "
            "Tokens will be issued on login and included in the Authorization header of subsequent requests."
        ),
        rationale=(
            "JWT tokens are stateless, scalable, and widely supported. "
            "They eliminate the need for server-side session storage and work well with distributed systems."
        ),
        alternatives=[
            Alternative(
                name="Session-based authentication",
                description="Store session data on the server and use cookie-based sessions.",
                pros=[
                    "Simpler to implement initially",
                    "Can revoke tokens immediately",
                    "Familiar pattern for many developers",
                ],
                cons=[
                    "Requires server-side storage",
                    "Doesn't scale well across multiple servers",
                    "More difficult to implement CORS properly",
                ],
                estimated_effort="2 hours",
            ),
            Alternative(
                name="API keys",
                description="Issue API keys to each client for authentication.",
                pros=[
                    "Simple to implement",
                    "Good for server-to-server communication",
                ],
                cons=[
                    "Not ideal for user authentication",
                    "Difficult to expire tokens on logout",
                    "Harder to implement refresh tokens",
                ],
                estimated_effort="1 hour",
            ),
        ],
        consequences=[
            Consequence(
                type="scalability",
                description="Stateless tokens allow horizontal scaling without shared session storage.",
                is_positive=True,
            ),
            Consequence(
                type="security",
                description="Tokens can be stolen if localStorage is compromised.",
                is_positive=False,
                mitigation="Use secure httpOnly cookies or store tokens in memory. Implement CSRF protection.",
            ),
            Consequence(
                type="complexity",
                description="Requires handling token refresh and expiration on the frontend.",
                is_positive=False,
                mitigation="Use a token refresh endpoint and automatic refresh on 401 responses.",
            ),
        ],
        trade_offs=(
            "We're trading immediate token revocation (on logout) for scalability and statelessness. "
            "Tokens will have a short expiration time (24 hours) to limit exposure."
        ),
        affects_areas=["api", "frontend", "authentication"],
        implementation_notes=(
            "Use RS256 (RSA) asymmetric signing. Frontend stores tokens in memory or secure httpOnly cookies. "
            "Refresh tokens stored in httpOnly cookies."
        ),
        follow_up_actions=[
            "Implement token refresh endpoint",
            "Add CSRF protection",
            "Test token expiration handling",
            "Document token refresh flow in API contract",
        ],
        tags=["authentication", "api", "security"],
        created_by="backend-agent",
    )

    print(decision.to_markdown())
    print("\n" + "="*60 + "\n")
    import json
    print(json.dumps(decision.to_dict(), indent=2))
