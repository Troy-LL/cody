"""Tests for voice.listen."""

from __future__ import annotations

import builtins
from unittest.mock import MagicMock, patch

import pytest

from voice.listen import ListenUnavailable, listen


def test_listen_missing_speechrecognition() -> None:
    real_import = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
        if name == "speech_recognition":
            raise ImportError("missing")
        return real_import(name, globals, locals, fromlist, level)

    with patch("builtins.__import__", side_effect=guarded):
        with pytest.raises(ListenUnavailable):
            listen()


def test_listen_returns_transcript() -> None:
    fake_sr = MagicMock()
    recognizer = MagicMock()
    mic_cm = MagicMock()
    mic_cm.__enter__.return_value = MagicMock()
    mic_cm.__exit__.return_value = False
    fake_sr.Recognizer.return_value = recognizer
    fake_sr.Microphone.return_value = mic_cm
    recognizer.recognize_sphinx.side_effect = Exception("no sphinx")
    recognizer.recognize_google.return_value = "find receipt_lazada.pdf"

    real_import = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
        if name == "speech_recognition":
            return fake_sr
        return real_import(name, globals, locals, fromlist, level)

    with patch("builtins.__import__", side_effect=guarded):
        assert listen() == "find receipt_lazada.pdf"
