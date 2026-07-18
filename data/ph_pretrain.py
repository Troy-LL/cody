"""Streaming loader for the jpaulpoliquit/ph-pretrain-03 Hugging Face dataset.

The dataset is a 1.93M-row Philippine-language text corpus
(https://huggingface.co/datasets/jpaulpoliquit/ph-pretrain-03), mostly
Tagalog web text from fineweb-2. It is too large to vendor into the repo,
so everything here streams rows over the network on demand.

Rows carry ``text`` plus metadata such as ``language`` (e.g. "tl"),
``language_bucket`` (register labels like "filipino_formal"),
``quality_score``, and ``url``.
"""

from __future__ import annotations

from collections.abc import Iterator

DATASET_ID = "jpaulpoliquit/ph-pretrain-03"


def load_ph_pretrain(split: str = "train", streaming: bool = True):
    """Return the dataset for *split* ("train", "validation", or "test").

    With ``streaming=True`` (default) this returns an IterableDataset that
    fetches rows lazily; set it to False only if you really want the full
    multi-GB download cached locally.
    """
    from datasets import load_dataset

    return load_dataset(DATASET_ID, split=split, streaming=streaming)


def iter_texts(
    split: str = "train",
    language: str | None = None,
    min_quality: float | None = None,
    limit: int | None = None,
) -> Iterator[str]:
    """Yield raw text rows, optionally filtered.

    Args:
        split: Dataset split to read.
        language: Keep only rows whose ``language`` matches (e.g. "tl").
        min_quality: Keep only rows with ``quality_score`` >= this value.
        limit: Stop after yielding this many texts.
    """
    count = 0
    for row in load_ph_pretrain(split=split, streaming=True):
        if language is not None and row.get("language") != language:
            continue
        if min_quality is not None:
            score = row.get("quality_score")
            if score is None or score < min_quality:
                continue
        yield row["text"]
        count += 1
        if limit is not None and count >= limit:
            return


def iter_tts_lines(
    count: int = 20,
    language: str | None = "tl",
    max_chars: int = 120,
    split: str = "validation",
) -> Iterator[str]:
    """Yield short, clean sentences suitable for TTS smoke-testing (OpenVoice).

    Pulls high-quality rows for *language* (default Tagalog, "tl"), splits
    them into sentences, and keeps ones short enough to speak naturally.
    Defaults to the validation split so iteration starts fast (19.5k rows
    vs 1.9M).
    """
    import re

    yielded = 0
    for text in iter_texts(split=split, language=language, min_quality=0.8):
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            sentence = sentence.strip()
            # Skip fragments, headings, and anything with markup-ish noise.
            if not 20 <= len(sentence) <= max_chars:
                continue
            if not sentence[0].isupper() or sentence[-1] not in ".!?":
                continue
            if any(ch in sentence for ch in "|{}[]<>=_/\\"):
                continue
            yield sentence
            yielded += 1
            if yielded >= count:
                return
