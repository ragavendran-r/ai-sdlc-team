"""Pytest fixtures for Backend agent node tests.

The Backend nodes use a module-level ``client = Anthropic()`` and call
``client.messages.create(...)`` then parse ``message.content[0].text`` as JSON,
each with a deterministic fallback on ``JSONDecodeError``. Without a real
ANTHROPIC_API_KEY the create call raises, so these tests historically required
the live API.

We stub ``client.messages.create`` to return a response whose text is
intentionally non-JSON. Every node then takes its built-in fallback (minimal
requirements / empty lists) and still sets its ``*_complete`` flag, exercising
the node logic offline and deterministically.
"""

import pytest

from backend_agent_workspace.agents import nodes as backend_nodes


class _FakeBlock:
    def __init__(self, text: str):
        self.text = text


class _FakeResponse:
    def __init__(self, text: str = "not-json"):
        self.content = [_FakeBlock(text)]


@pytest.fixture(autouse=True)
def _mock_anthropic(monkeypatch):
    """Replace client.messages.create so node tests never hit the network."""
    monkeypatch.setattr(
        backend_nodes.client.messages,
        "create",
        lambda *a, **k: _FakeResponse(),
        raising=False,
    )
