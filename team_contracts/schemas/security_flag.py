"""SecurityFlag schema for backend agent."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class SecuritySeverity(str, Enum):
    """Security issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SecurityCategory(str, Enum):
    """OWASP API Security Top 10 categories."""
    BROKEN_AUTHENTICATION = "broken_authentication"
    BROKEN_AUTHORIZATION = "broken_authorization"
    INJECTION = "injection"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INSUFFICIENT_LOGGING = "insufficient_logging"
    RATE_LIMITING_MISSING = "rate_limiting_missing"
    MASS_ASSIGNMENT = "mass_assignment"
    XXXE = "xxxe"
    BROKEN_OBJECT_LEVEL_AUTH = "broken_object_level_auth"
    CRYPTO_FAILURES = "crypto_failures"


class SecurityFlag(BaseModel):
    """Security issue found during review."""

    id: str = Field(..., description="Flag identifier")
    endpoint_id: str = Field(..., description="Endpoint with the issue")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Detailed description")

    # Classification
    severity: SecuritySeverity = Field(..., description="Severity level")
    category: SecurityCategory = Field(..., description="OWASP category")

    # Details
    vulnerable_code: Optional[str] = Field(
        default=None,
        description="Snippet showing the vulnerability"
    )
    remediation: str = Field(..., description="How to fix this issue")
    reference_url: Optional[str] = Field(
        default=None,
        description="Reference to security documentation"
    )

    # Status
    resolved: bool = Field(default=False, description="Has this been resolved?")
    resolved_by: Optional[str] = Field(default=None, description="Who resolved it?")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent creating this")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        severity_emoji = {
            SecuritySeverity.CRITICAL: "🔴",
            SecuritySeverity.HIGH: "🟠",
            SecuritySeverity.MEDIUM: "🟡",
            SecuritySeverity.LOW: "🟢",
        }

        emoji = severity_emoji.get(self.severity, "⚠️")

        lines = [
            f"{emoji} **{self.title}** (Endpoint: `{self.endpoint_id}`)",
            f"**Severity:** {self.severity.value.upper()}",
            f"**Category:** {self.category.value.replace('_', ' ').title()}",
            "",
            self.description,
        ]

        if self.vulnerable_code:
            lines.extend([
                "",
                "**Vulnerable Code:**",
                "```python",
                self.vulnerable_code,
                "```",
            ])

        lines.extend([
            "",
            "**Remediation:**",
            self.remediation,
        ])

        if self.reference_url:
            lines.extend([
                "",
                f"**Reference:** {self.reference_url}",
            ])

        if self.resolved:
            lines.append(f"\n✅ **Resolved by:** {self.resolved_by}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "vulnerable_code": self.vulnerable_code,
            "remediation": self.remediation,
            "reference_url": self.reference_url,
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
