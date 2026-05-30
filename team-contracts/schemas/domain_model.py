"""DomainModel schema for backend agent."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class DataType(str, Enum):
    """Data types for entity attributes."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    UUID = "uuid"
    JSON = "json"
    DECIMAL = "decimal"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


class Attribute(BaseModel):
    """Entity attribute definition."""

    name: str = Field(..., description="Attribute name")
    data_type: DataType = Field(..., description="Data type")
    required: bool = Field(default=True, description="Is this required?")
    unique: bool = Field(default=False, description="Must be unique?")
    indexed: bool = Field(default=False, description="Should be indexed?")
    default_value: Optional[Any] = Field(default=None, description="Default value")
    description: str = Field(..., description="Attribute description")


class Relationship(BaseModel):
    """Relationship between entities."""

    id: str = Field(..., description="Relationship identifier")
    from_entity: str = Field(..., description="Source entity name")
    to_entity: str = Field(..., description="Target entity name")
    relation_type: RelationType = Field(..., description="Type of relationship")
    foreign_key: Optional[str] = Field(default=None, description="Foreign key field name")
    cascade_delete: bool = Field(default=False, description="Cascade on delete?")
    description: str = Field(..., description="Relationship description")


class Entity(BaseModel):
    """Domain entity definition."""

    name: str = Field(..., description="Entity name")
    description: str = Field(..., description="Entity description")
    plural: str = Field(..., description="Plural form of entity name")

    # Attributes
    attributes: List[Attribute] = Field(
        ...,
        description="Entity attributes",
        min_items=1
    )

    # Business rules
    business_rules: List[str] = Field(
        default_factory=list,
        description="Business rules for this entity"
    )

    # Metadata
    is_aggregate_root: bool = Field(default=True, description="Is this an aggregate root?")
    is_value_object: bool = Field(default=False, description="Is this a value object?")


class DomainModel(BaseModel):
    """Domain model of the system."""

    id: str = Field(..., description="Model identifier")
    feature_name: str = Field(..., description="Feature name this models")
    description: str = Field(..., description="Domain model description")

    # Core definitions
    entities: List[Entity] = Field(
        ...,
        description="Domain entities",
        min_items=1
    )
    relationships: List[Relationship] = Field(
        default_factory=list,
        description="Relationships between entities"
    )

    # Domain-wide rules
    ubiquitous_language: Dict[str, str] = Field(
        default_factory=dict,
        description="Domain terminology glossary"
    )
    invariants: List[str] = Field(
        default_factory=list,
        description="Domain invariants that must hold"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent creating this")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"# Domain Model: {self.feature_name}",
            f"**ID:** {self.id}",
            "",
            self.description,
        ]

        # Entities
        lines.extend(["", "## Entities"])
        for entity in self.entities:
            lines.extend([
                "",
                f"### {entity.name}",
                f"_{entity.description}_",
                f"**Plural:** {entity.plural}",
            ])

            if entity.is_aggregate_root:
                lines.append("✓ Aggregate Root")
            if entity.is_value_object:
                lines.append("✓ Value Object")

            lines.append("**Attributes:**")
            for attr in entity.attributes:
                required = "✓ Required" if attr.required else "○ Optional"
                lines.append(f"- `{attr.name}` ({attr.data_type.value}) [{required}]: {attr.description}")
                if attr.unique:
                    lines.append("  (unique)")
                if attr.indexed:
                    lines.append("  (indexed)")

            if entity.business_rules:
                lines.append("**Business Rules:**")
                for rule in entity.business_rules:
                    lines.append(f"- {rule}")

        # Relationships
        if self.relationships:
            lines.extend(["", "## Relationships"])
            for rel in self.relationships:
                lines.append(
                    f"- {rel.from_entity} --[{rel.relation_type.value}]--> {rel.to_entity}: {rel.description}"
                )

        # Ubiquitous language
        if self.ubiquitous_language:
            lines.extend(["", "## Ubiquitous Language"])
            for term, definition in self.ubiquitous_language.items():
                lines.append(f"- **{term}:** {definition}")

        # Invariants
        if self.invariants:
            lines.extend(["", "## Domain Invariants"])
            for invariant in self.invariants:
                lines.append(f"- {invariant}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "feature_name": self.feature_name,
            "description": self.description,
            "entities": [
                {
                    "name": e.name,
                    "description": e.description,
                    "plural": e.plural,
                    "is_aggregate_root": e.is_aggregate_root,
                    "is_value_object": e.is_value_object,
                    "attributes": [
                        {
                            "name": a.name,
                            "data_type": a.data_type.value,
                            "required": a.required,
                            "unique": a.unique,
                            "indexed": a.indexed,
                            "description": a.description,
                        }
                        for a in e.attributes
                    ],
                    "business_rules": e.business_rules,
                }
                for e in self.entities
            ],
            "relationships": [
                {
                    "id": r.id,
                    "from_entity": r.from_entity,
                    "to_entity": r.to_entity,
                    "relation_type": r.relation_type.value,
                    "foreign_key": r.foreign_key,
                    "cascade_delete": r.cascade_delete,
                    "description": r.description,
                }
                for r in self.relationships
            ],
            "ubiquitous_language": self.ubiquitous_language,
            "invariants": self.invariants,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
