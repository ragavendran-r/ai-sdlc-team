"""Pytest fixtures for EM agent node tests.

The EM nodes call a module-level ``llm = ChatAnthropic(...)`` and invoke it with
``llm.invoke(prompt)``. Without a real ANTHROPIC_API_KEY that call raises, which
is why these tests historically only passed against the live API. The nodes do
not actually consume the response (they build structured objects themselves), so
we stub ``llm.invoke`` to return a dummy message and let the node logic run
offline.
"""

import pytest

from em_agent_workspace.agents import nodes as em_nodes


class _FakeMessage:
    """Minimal stand-in for a LangChain chat message."""

    def __init__(self, content: str = "{}"):
        self.content = content


class _FakeLLM:
    """Stand-in for the ChatAnthropic client used by the nodes.

    ChatAnthropic is a pydantic model, so its attributes can't be monkeypatched
    in place; we replace the whole module-level ``llm`` object instead.
    """

    def invoke(self, *args, **kwargs):
        return _FakeMessage()


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    """Replace the module-level llm so node tests never hit the network."""
    monkeypatch.setattr(em_nodes, "llm", _FakeLLM())
