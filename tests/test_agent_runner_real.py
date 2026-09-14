"""Parser tests for the live agent tool-call contract. No GPU required."""

from src.agent_runner import AgentOutput
from src.agent_runner_real import SYSTEM_PROMPT, KNOWN_TOOLS, parse_tool_call


def test_system_prompt_asks_for_action_line() -> None:
    assert "<DECISION>" in SYSTEM_PROMPT
    assert "tool_name" in SYSTEM_PROMPT


def test_known_tools_match_frozen_set() -> None:
    assert KNOWN_TOOLS == {"publish_report", "send_email", "update_allowlist"}


def test_parse_valid_call() -> None:
    text = 'ACTION: {"tool_name": "send_email", "arguments": {"to": "compliance@example.com", "body": "ok"}}'
    parsed, tool_name, arguments = parse_tool_call(text)
    assert parsed
    assert tool_name == "send_email"
    assert arguments == {"to": "compliance@example.com", "body": "ok"}


def test_parse_picks_last_json_block() -> None:
    text = (
        'first {"tool_name": "publish_report", "arguments": {}} '
        'then {"tool_name": "update_allowlist", "arguments": {"addresses": []}}'
    )
    parsed, tool_name, _ = parse_tool_call(text)
    assert parsed
    assert tool_name == "update_allowlist"


def test_parse_ignores_unknown_tool() -> None:
    text = 'ACTION: {"tool_name": "delete_all", "arguments": {}}'
    parsed, tool_name, arguments = parse_tool_call(text)
    assert not parsed
    assert tool_name == ""
    assert arguments == {}


def test_parse_rejects_missing_arguments() -> None:
    text = 'ACTION: {"tool_name": "send_email"}'
    parsed, tool_name, arguments = parse_tool_call(text)
    assert not parsed
    assert tool_name == ""
    assert arguments == {}


def test_parse_no_json_returns_failure() -> None:
    text = "I will just respond in plain text.\n"
    parsed, tool_name, arguments = parse_tool_call(text)
    assert not parsed
    assert tool_name == ""
    assert arguments == {}


def test_call_parse_failed_defaults_false() -> None:
    output = AgentOutput(
        reasoning="ok",
        tool_name="send_email",
        arguments={},
        decision_marker_found=True,
        latency_ms=1.0,
        input_tokens=3,
        output_tokens=2,
    )
    assert output.call_parse_failed is False