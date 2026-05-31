"""Pytest configuration for team-orchestrator tests."""

import sys
from pathlib import Path

# Add parent directory to path so imports work with hyphenated package names
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
