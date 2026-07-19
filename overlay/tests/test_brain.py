import json
from types import SimpleNamespace

from overlay.brain import parse_tool_calls


def _msg(content, tools):
    calls = [SimpleNamespace(function=SimpleNamespace(name=n, arguments=json.dumps(a))) for n, a in tools]
    return SimpleNamespace(content=content, tool_calls=calls or None)


def test_parse_point_cell():
    ans = parse_tool_calls(
        _msg("Here.", [("point", {"found": True, "target": "Chrome", "cell": "B7", "x": 100, "y": 200})])
    )
    assert ans.cell == "B7"
    assert ans.coords == (100.0, 200.0)


def test_parse_point_target():
    ans = parse_tool_calls(
        _msg("Here is Save.", [("point", {"found": True, "target": "Save", "x": 12, "y": 34})])
    )
    assert ans.reply_text == "Here is Save."
    assert ans.found is True
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
    ans = parse_tool_calls(
        _msg(None, [("point", {"found": True, "target": "Save", "x": 12, "y": 34})])
    )
    assert ans.reply_text == "Here's Save."
    assert ans.target == "Save"


def test_parse_found_false_clears_coords():
    ans = parse_tool_calls(
        _msg(
            "I don't see Spotify here.",
            [("point", {"found": False, "target": "Spotify", "x": 10, "y": 10})],
        )
    )
    assert ans.found is False
    assert ans.coords is None
    assert ans.target is None


def test_parse_guide_steps():
    ans = parse_tool_calls(
        _msg(
            "Open the menu, then Settings.",
            [
                (
                    "guide",
                    {
                        "found": True,
                        "steps": [
                            {"target": "File", "x": 40, "y": 12, "say": "Click File"},
                            {"target": "Settings", "x": 55, "y": 80, "say": "Then Settings"},
                        ],
                    },
                )
            ],
        )
    )
    assert ans.found is True
    assert len(ans.steps) == 2
    assert ans.steps[0].say == "Click File"
    assert ans.coords == (40.0, 12.0)


def test_user_text_includes_scene_and_grid():
    from PIL import Image

    from overlay.brain import _user_text
    from overlay.screenshot import Shot

    img = Image.new("RGB", (1280, 720), color=(0, 0, 0))
    shot = Shot(image=img, scale=1.0, origin=(0, 0))
    text = _user_text(
        "where's gmail",
        shot,
        scene_text='Scene:\n- "Chrome" Button',
        grid_legend="Grid A1…H12",
    )
    assert "Chrome" in text
    assert "Grid A1" in text
    assert "1280x720" in text


def test_user_text_includes_image_dimensions():
    from PIL import Image

    from overlay.brain import _user_text
    from overlay.screenshot import Shot

    img = Image.new("RGB", (1280, 720), color=(0, 0, 0))
    shot = Shot(image=img, scale=1.0, origin=(0, 0))
    text = _user_text("where's gmail", shot)
    assert "1280x720" in text
    assert "0..1279" in text and "0..719" in text
    assert "found=false" in text
