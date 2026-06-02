"""IAStructure schema: information architecture for UX design."""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class NavNode(BaseModel):
    """A node in the navigation hierarchy."""

    id: str = Field(..., description="Node identifier")
    name: str = Field(..., description="Page/section name")
    description: Optional[str] = Field(default=None)
    children: List[str] = Field(default_factory=list, description="Child node IDs")


class IAStructure(BaseModel):
    """
    IAStructure defines the information architecture and navigation.

    Shows page hierarchy, organization, and content groupings.
    """

    id: str = Field(..., description="Unique IA identifier")

    # Navigation
    root_nodes: List[str] = Field(
        ...,
        description="Top-level navigation items",
        min_items=1
    )
    nodes: Dict[str, NavNode] = Field(..., description="All nodes by ID")

    # Page inventory
    total_pages: int = Field(..., description="Estimated number of pages", ge=0)
    page_categories: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Pages grouped by category"
    )

    # Structure notes
    notes: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created this")

    def to_markdown(self) -> str:
        """Convert to Markdown."""
        lines = [
            "# Information Architecture",
            f"**Total Pages:** {self.total_pages}",
            "",
            "## Navigation Hierarchy",
            "",
        ]

        def render_tree(node_id: str, indent: int = 0) -> List[str]:
            if node_id not in self.nodes:
                return []
            node = self.nodes[node_id]
            result = [" " * indent + f"- {node.name}"]
            for child_id in node.children:
                result.extend(render_tree(child_id, indent + 2))
            return result

        for root_id in self.root_nodes:
            lines.extend(render_tree(root_id))

        if self.page_categories:
            lines.extend(["", "## Page Categories"])
            for category, pages in self.page_categories.items():
                lines.append(f"\n### {category}")
                for page in pages:
                    lines.append(f"- {page}")

        if self.notes:
            lines.extend(["", f"## Notes\n{self.notes}"])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "root_nodes": self.root_nodes,
            "nodes": {
                k: {"id": v.id, "name": v.name, "description": v.description, "children": v.children}
                for k, v in self.nodes.items()
            },
            "total_pages": self.total_pages,
            "page_categories": self.page_categories,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
