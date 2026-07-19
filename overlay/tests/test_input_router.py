from overlay.input_router import handle_query, Deps
from overlay.brain import Answer
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
    out = handle_query("where is save", _deps(Answer("Here.", target="Save"), (500, 300)))
    assert out.reply_text == "Here." and out.point == (500, 300)


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
