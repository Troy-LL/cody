from overlay.brain import Answer, GuideStep
from overlay.input_router import Deps, handle_query
from overlay.screenshot import Shot


def _deps(answer, point):
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    return Deps(
        capture=lambda: shot,
        ask=lambda q, s: answer,
        boxes_for=lambda s: [],
        resolve=lambda target, coords, boxes, s: point,
    )


def test_query_with_point():
    out = handle_query(
        "where is save",
        _deps(Answer("Here.", target="Save", coords=(1, 2)), (500, 300)),
    )
    assert out.reply_text == "Here." and out.point == (500, 300)
    assert len(out.steps) == 1


def test_query_text_only():
    out = handle_query("what is this", _deps(Answer("A browser."), None))
    assert out.reply_text == "A browser." and out.point is None


def test_empty_question_short_circuits():
    out = handle_query("", _deps(Answer("should not run"), (1, 1)))
    assert out.reply_text == "Didn't catch that." and out.point is None


def test_ask_failure_returns_graceful_message():
    shot = Shot(image=None, scale=1.0, origin=(0, 0))

    def _raise(_q, _s):
        raise RuntimeError("network down")

    deps = Deps(
        capture=lambda: shot,
        ask=_raise,
        boxes_for=lambda s: [],
        resolve=lambda target, coords, boxes, s: None,
    )
    out = handle_query("hello", deps)
    assert out.reply_text == "I couldn't reach the model." and out.point is None


def test_not_found_does_not_point():
    out = handle_query(
        "where's spotify",
        _deps(
            Answer("I don't see Spotify.", found=False, target="Spotify", coords=(9, 9)),
            (999, 999),
        ),
    )
    assert out.point is None
    assert out.steps == []
    assert "don't see" in out.reply_text.lower() or out.reply_text


def test_guide_resolves_multiple_steps():
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    answer = Answer(
        "Two clicks.",
        found=True,
        steps=[
            GuideStep("File", (10, 10), "Click File"),
            GuideStep("Settings", (20, 20), "Then Settings"),
        ],
    )

    def resolve(target, coords, boxes, s):
        return {"File": (100, 50), "Settings": (120, 200)}[target]

    deps = Deps(
        capture=lambda: shot,
        ask=lambda q, s: answer,
        boxes_for=lambda s: [],
        resolve=resolve,
    )
    out = handle_query("open settings", deps)
    assert out.point == (100, 50)
    assert len(out.steps) == 2
    assert out.steps[1].say == "Then Settings"
