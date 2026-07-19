from overlay.scene import SceneEl, format_scene, match_uia


def test_format_scene_lists_names():
    els = [SceneEl("Chrome", "Button", (10, 1000, 60, 1060))]
    text = format_scene(els)
    assert "Chrome" in text and "Button" in text


def test_match_uia_exact_and_core():
    els = [
        SceneEl("Google Chrome", "Button", (10, 1000, 60, 1060)),
        SceneEl("Settings", "ListItem", (100, 200, 400, 240)),
    ]
    hit = match_uia("Chrome icon", els)
    assert hit is not None and hit.name == "Google Chrome"
