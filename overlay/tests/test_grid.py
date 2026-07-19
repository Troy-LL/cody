from PIL import Image

from overlay.grid import annotate, cell_center, default_grid, legend_text


def test_cell_center_a1_is_top_left_bucket():
    spec = default_grid(1200, 800)
    pt = cell_center(spec, "A1")
    assert pt is not None
    assert 0 <= pt[0] < 1200 / spec.cols
    assert 0 <= pt[1] < 800 / spec.rows


def test_cell_center_rejects_bad():
    spec = default_grid(1200, 800)
    assert cell_center(spec, "ZZ9") is None
    assert cell_center(spec, "") is None


def test_cell_center_case_insensitive():
    spec = default_grid(1200, 800)
    assert cell_center(spec, "b7") == cell_center(spec, "B7")


def test_default_grid_clamps():
    spec = default_grid(600, 400)
    assert 6 <= spec.cols <= 16
    assert 4 <= spec.rows <= 12


def test_annotate_does_not_mutate_input():
    img = Image.new("RGB", (120, 80), color=(10, 20, 30))
    before = img.tobytes()
    spec = default_grid(120, 80)
    out = annotate(img, spec)
    assert img.tobytes() == before
    assert out is not img


def test_legend_text_mentions_grid():
    spec = default_grid(1200, 800)
    text = legend_text(spec)
    assert "grid" in text.lower()
    assert "B7" in text or "cell" in text.lower()
