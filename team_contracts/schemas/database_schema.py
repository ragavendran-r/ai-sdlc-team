"""DatabaseSchema for backend agent."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DatabaseSchema(BaseModel):
    """Generated database schema from domain model."""

    id: str = Field(..., description="Schema identifier")
    feature_name: str = Field(..., description="Feature name")
    domain_model_id: str = Field(..., description="Reference to domain model")

    # Generated SQL DDL
    ddl_sql: str = Field(..., description="Complete DDL SQL for table creation")

    # SQLAlchemy models
    sqlalchemy_models: str = Field(..., description="SQLAlchemy model class definitions")

    # Migration notes
    migration_notes: Optional[str] = Field(
        default=None,
        description="Notes for database migrations (indexes, constraints, etc.)"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent creating this")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"# Database Schema: {self.feature_name}",
            f"**ID:** {self.id}",
            f"**Domain Model:** {self.domain_model_id}",
            "",
            "## DDL SQL",
            "```sql",
            self.ddl_sql,
            "```",
            "",
            "## SQLAlchemy Models",
            "```python",
            self.sqlalchemy_models,
            "```",
        ]

        if self.migration_notes:
            lines.extend([
                "",
                "## Migration Notes",
                self.migration_notes,
            ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "feature_name": self.feature_name,
            "domain_model_id": self.domain_model_id,
            "ddl_sql": self.ddl_sql,
            "sqlalchemy_models": self.sqlalchemy_models,
            "migration_notes": self.migration_notes,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
