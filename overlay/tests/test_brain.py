import json
from types import SimpleNamespace
from overlay.brain import parse_tool_calls


def _msg(content, tools):
    calls = [SimpleNamespace(function=SimpleNamespace(name=n, arguments=json.dumps(a))) for n, a in tools]
    return SimpleNamespace(content=content, tool_calls=calls or None)


def test_parse_point_target():
    ans = parse_tool_calls(_msg("Here is Save.", [("point", {"target": "Save", "x": 12, "y": 34})]))
    assert ans.reply_text == "Here is Save."
    assert ans.target == "Save"
    assert ans.coords == (12.0, 34.0)


def test_parse_text_only():
    ans = parse_tool_calls(_msg("Just text.", []))
    assert ans.reply_text == "Just text."
    assert ans.target is None and ans.coords is None and ans.reveal_path is None


def test_parse_reveal():
    ans = parse_tool_calls(_msg("Opening it.", [("reveal", {"path": "C:/x.txt"})]))
    assert ans.reveal_path == "C:/x.txt"


def test_parse_point_empty_content_synthesizes_reply():
    ans = parse_tool_calls(_msg(None, [("point", {"target": "Save", "x": 12, "y": 34})]))
    assert ans.reply_text == "Here's Save."
    assert ans.target == "Save"
