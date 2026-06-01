"""Pytest fixtures for Frontend agent node tests.

The Frontend nodes use a module-level ``LLM = Anthropic()`` and call
``LLM.messages.create(...)`` then parse ``response.content[0].text`` as JSON.
Unlike the Backend nodes, several Frontend nodes set their ``*_complete`` flag
*inside* the ``try`` block, so they only complete when the response is valid
JSON. Without a real ANTHROPIC_API_KEY the create call raises.

We stub ``LLM.messages.create`` to return a response whose text is a permissive
JSON object. Every consumer reads it via ``.get(...)`` (or assigns it directly /
takes ``len(...)``), so one shared payload satisfies all nodes and lets the tests
run offline and deterministically.
"""

import json

import pytest

from frontend_agent_workspace.agents import nodes as frontend_nodes

# Superset of keys the various nodes read from the parsed response. Reading a
# missing key via .get() returns the default, so extra keys are harmless.
_FAKE_PAYLOAD = {
    "valid": True,
    "gaps": [],
    "mappings": {},
    "missing_endpoints": [],
    "state_groups": [],
    "requires_global_store": False,
    "global_store_recommendation": "Zustand",
    "recommended_context_layers": [],
    "implementation_order": [],
}


class _FakeBlock:
    def __init__(self, text: str):
        self.text = text


class _FakeResponse:
    def __init__(self, text: str):
        self.content = [_FakeBlock(text)]


@pytest.fixture(autouse=True)
def _mock_anthropic(monkeypatch):
    """Replace LLM.messages.create so node tests never hit the network."""
    monkeypatch.setattr(
        frontend_nodes.LLM.messages,
        "create",
        lambda *a, **k: _FakeResponse(json.dumps(_FAKE_PAYLOAD)),
        raising=False,
    )
