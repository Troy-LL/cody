"""Local OpenVoice V2 synthesis (MeloTTS base + optional tone-color convert).

See https://github.com/myshell-ai/OpenVoice — MeloTTS generates speech; OpenVoice
optionally clones tone color from a reference wav.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# MeloTTS / OpenVoice V2 native languages do not include Tagalog; EN is the demo fallback.
MELO_LANGUAGE_BY_MODE = {
    "en": "EN",
    "tl": "EN",
    "taglish": "EN",
}


class OpenVoiceUnavailable(RuntimeError):
    """OpenVoice/MeloTTS not installed or checkpoints missing."""


def _import_stack():
    try:
        from melo.api import TTS  # type: ignore[import-untyped]
    except ImportError as exc:
        raise OpenVoiceUnavailable(
            "MeloTTS is not installed. See voice/README.md (OpenVoice setup)."
        ) from exc

    try:
        from openvoice import se_extractor  # type: ignore[import-untyped]
        from openvoice.api import ToneColorConverter  # type: ignore[import-untyped]
    except ImportError as exc:
        raise OpenVoiceUnavailable(
            "openvoice is not installed. See voice/README.md (OpenVoice setup)."
        ) from exc

    return TTS, se_extractor, ToneColorConverter


def synthesize_to_wav(
    *,
    text: str,
    speaker: str,
    language_mode: str,
    checkpoints_dir: str | Path,
    device: str,
    reference_wav: str | None,
    tone_convert: bool,
) -> Path:
    """Synthesize *text* to a temp WAV path. Caller owns cleanup policy (leave on disk)."""
    TTS, se_extractor, ToneColorConverter = _import_stack()
    ckpt = Path(checkpoints_dir)
    language = MELO_LANGUAGE_BY_MODE.get(language_mode.lower(), "EN")

    tts = TTS(language=language, device=device)
    speaker_ids = tts.hps.data.spk2id
    if speaker not in speaker_ids:
        # Case-insensitive fallback (EN-US vs en-us).
        lookup = {str(k).lower(): k for k in speaker_ids}
        key = lookup.get(speaker.lower())
        if key is None:
            raise OpenVoiceUnavailable(
                f"unknown MeloTTS speaker {speaker!r}; available={list(speaker_ids)}"
            )
        speaker_id = speaker_ids[key]
        speaker_key = str(key)
    else:
        speaker_id = speaker_ids[speaker]
        speaker_key = speaker

    out_dir = Path(tempfile.mkdtemp(prefix="cody-openvoice-"))
    base_path = out_dir / "base.wav"
    final_path = out_dir / "final.wav"

    tts.tts_to_file(text, speaker_id, str(base_path), speed=1.0)

    if not tone_convert:
        return base_path

    converter_dir = ckpt / "converter"
    config_json = converter_dir / "config.json"
    checkpoint = converter_dir / "checkpoint.pth"
    if not config_json.is_file() or not checkpoint.is_file():
        raise OpenVoiceUnavailable(
            f"OpenVoice checkpoints missing under {converter_dir} "
            "(download checkpoints_v2 per voice/README.md)"
        )

    if not reference_wav or not Path(reference_wav).is_file():
        raise OpenVoiceUnavailable(
            f"reference_wav missing or not a file: {reference_wav!r}"
        )

    converter = ToneColorConverter(str(config_json), device=device)
    converter.load_ckpt(str(checkpoint))

    # Prefer packaged base-speaker SE when present (official V2 demo path).
    se_name = speaker_key.lower().replace("_", "-")
    source_se_path = ckpt / "base_speakers" / "ses" / f"{se_name}.pth"
    if source_se_path.is_file():
        import torch

        source_se = torch.load(str(source_se_path), map_location=device)
    else:
        source_se, _ = se_extractor.get_se(str(base_path), converter, vad=True)

    target_se, _ = se_extractor.get_se(str(reference_wav), converter, vad=True)
    converter.convert(
        audio_src_path=str(base_path),
        src_se=source_se,
        tgt_se=target_se,
        output_path=str(final_path),
    )
    return final_path
