"""Root pytest configuration for all tests."""

import sys
from pathlib import Path

# Add repository root to sys.path so all packages can be imported
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))
