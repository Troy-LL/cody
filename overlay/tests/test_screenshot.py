from overlay.screenshot import Shot, to_screen


def test_to_screen_inverts_scale_and_origin():
    shot = Shot(image=None, scale=0.5, origin=(-1920, 0))
    # image point (100, 40) at 0.5 scale -> (200, 80) desktop px, minus origin.
    assert to_screen(shot, 100, 40) == (-1920 + 200, 0 + 80)


def test_to_screen_rounds():
    shot = Shot(image=None, scale=0.5, origin=(0, 0))
    assert to_screen(shot, 33, 33) == (66, 66)
