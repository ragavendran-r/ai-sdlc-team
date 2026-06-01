"""Shared context store for team orchestrator."""

import json
from datetime import datetime
from typing import Any, Dict, Optional, List
from pathlib import Path


class ContextStore:
    """Persistent context store for team artifacts."""

    def __init__(self, base_path: str = "team_contracts/context-store"):
        """
        Initialize context store.

        Args:
            base_path: Path to store context files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for each workflow
        self.workflows_dir = self.base_path / "workflows"
        self.artifacts_dir = self.base_path / "artifacts"
        self.metadata_dir = self.base_path / "metadata"

        for dir_path in [self.workflows_dir, self.artifacts_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)

        # In-memory cache
        self.cache: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def write_artifact(
        self,
        key: str,
        data: Any,
        workflow: str = "",
        artifact_type: str = ""
    ) -> str:
        """
        Write an artifact to context store.

        Args:
            key: Unique identifier for artifact
            data: Data to store (dict or object with to_dict method)
            workflow: Source workflow
            artifact_type: Type of artifact

        Returns:
            Path to stored artifact
        """
        # Convert data to dict if needed
        if hasattr(data, "to_dict"):
            data_dict = data.to_dict()
        elif hasattr(data, "model_dump"):  # Pydantic v2
            data_dict = data.model_dump()
        elif isinstance(data, dict):
            data_dict = data
        else:
            data_dict = {"data": str(data)}

        # Store metadata
        self.metadata[key] = {
            "workflow": workflow,
            "artifact_type": artifact_type,
            "created_at": datetime.utcnow().isoformat(),
            "size_bytes": len(json.dumps(data_dict)),
        }

        # Store in cache
        self.cache[key] = data_dict

        # Write to file
        file_path = self.artifacts_dir / f"{key}.json"
        with open(file_path, "w") as f:
            json.dump(
                {
                    "key": key,
                    "workflow": workflow,
                    "artifact_type": artifact_type,
                    "created_at": datetime.utcnow().isoformat(),
                    "data": data_dict,
                },
                f,
                indent=2,
                default=str,
            )

        return str(file_path)

    def read_artifact(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Read an artifact from context store.

        Args:
            key: Artifact identifier

        Returns:
            Artifact data or None if not found
        """
        # Check cache first
        if key in self.cache:
            return self.cache[key]

        # Try to read from file
        file_path = self.artifacts_dir / f"{key}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                artifact = json.load(f)
                # Cache it
                self.cache[key] = artifact.get("data", artifact)
                return self.cache[key]

        return None

    def list_artifacts(
        self,
        workflow: Optional[str] = None,
        artifact_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List artifacts in store.

        Args:
            workflow: Filter by source workflow
            artifact_type: Filter by artifact type

        Returns:
            List of artifact metadata
        """
        artifacts = []

        for file_path in self.artifacts_dir.glob("*.json"):
            with open(file_path, "r") as f:
                artifact = json.load(f)

            key = artifact.get("key", file_path.stem)
            meta = self.metadata.get(key, {})

            if workflow and meta.get("workflow") != workflow:
                continue
            if artifact_type and meta.get("artifact_type") != artifact_type:
                continue

            artifacts.append({
                "key": key,
                "workflow": meta.get("workflow", "unknown"),
                "artifact_type": meta.get("artifact_type", "unknown"),
                "created_at": meta.get("created_at", ""),
                "size_bytes": meta.get("size_bytes", 0),
            })

        return sorted(artifacts, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_latest_by_type(
        self,
        artifact_type: str,
        workflow: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent artifact of a type.

        Args:
            artifact_type: Type of artifact
            workflow: Optional workflow filter

        Returns:
            Latest artifact or None
        """
        artifacts = self.list_artifacts(
            workflow=workflow,
            artifact_type=artifact_type
        )

        if artifacts:
            return self.read_artifact(artifacts[0]["key"])

        return None

    def write_workflow_state(
        self,
        workflow: str,
        state: Dict[str, Any]
    ) -> str:
        """
        Write workflow state to store.

        Args:
            workflow: Workflow name
            state: Workflow state dict

        Returns:
            Path to stored state
        """
        key = f"{workflow}_state_{datetime.utcnow().timestamp()}"
        return self.write_artifact(
            key=key,
            data=state,
            workflow=workflow,
            artifact_type="workflow_state"
        )

    def read_workflow_state(self, workflow: str) -> Optional[Dict[str, Any]]:
        """
        Read latest workflow state.

        Args:
            workflow: Workflow name

        Returns:
            Latest state or None
        """
        return self.get_latest_by_type("workflow_state", workflow=workflow)

    def export_timeline(self) -> str:
        """
        Export a timeline of all artifacts created.

        Returns:
            Formatted timeline string
        """
        artifacts = self.list_artifacts()
        if not artifacts:
            return "No artifacts in context store yet."

        lines = ["Team Artifact Timeline", "=" * 60]

        current_workflow = None
        for artifact in artifacts:
            if artifact["workflow"] != current_workflow:
                current_workflow = artifact["workflow"]
                lines.append(f"\n📦 {current_workflow.upper()} Workflow")
                lines.append("-" * 40)

            lines.append(
                f"  {artifact['created_at'][:10]} "
                f"{artifact['artifact_type']:20} "
                f"({artifact['size_bytes']} bytes)"
            )

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all stored artifacts (use with caution)."""
        import shutil
        if self.artifacts_dir.exists():
            shutil.rmtree(self.artifacts_dir)
        self.artifacts_dir.mkdir()
        self.cache.clear()
        self.metadata.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get context store statistics."""
        artifacts = self.list_artifacts()
        stats = {
            "total_artifacts": len(artifacts),
            "by_workflow": {},
            "by_type": {},
            "total_size_bytes": 0,
        }

        for artifact in artifacts:
            workflow = artifact["workflow"]
            artifact_type = artifact["artifact_type"]

            if workflow not in stats["by_workflow"]:
                stats["by_workflow"][workflow] = 0
            stats["by_workflow"][workflow] += 1

            if artifact_type not in stats["by_type"]:
                stats["by_type"][artifact_type] = 0
            stats["by_type"][artifact_type] += 1

            stats["total_size_bytes"] += artifact.get("size_bytes", 0)

        return stats
