#!/usr/bin/env python
"""Main entry point for running the complete team pipeline."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from team_orchestrator import main

if __name__ == "__main__":
    sys.exit(main())
