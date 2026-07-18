# Data — external dataset access

Streaming access to [`jpaulpoliquit/ph-pretrain-03`](https://huggingface.co/datasets/jpaulpoliquit/ph-pretrain-03), a 1.93M-row Philippine-language web-text corpus (mostly Tagalog, from fineweb-2). Nothing is committed to the repo; rows stream from Hugging Face on demand.

## Setup

The `datasets` dependency is included in `pyproject.toml`. Install with:

```bash
.venv/Scripts/pip install -e .
```

## Usage

```python
from data import iter_texts, load_ph_pretrain

# Grab 10 higher-quality Tagalog texts without downloading the corpus
for text in iter_texts(language="tl", min_quality=0.8, limit=10):
    print(text[:120])

# Or work with the raw streaming dataset (full row metadata)
ds = load_ph_pretrain(split="validation")
row = next(iter(ds))  # keys: text, language, quality_score, url, title, ...
```

Splits: `train` (1.9M), `validation` (19.5k), `test` (19.1k).

## Voice / OpenVoice TTS

`iter_tts_lines` pulls short, clean Tagalog sentences for smoke-testing the voice layer (e.g. feeding reference text to OpenVoice):

```python
from data import iter_tts_lines

for line in iter_tts_lines(count=10):  # defaults to Tagalog ("tl")
    print(line)  # short sentences, ready to hand to the TTS engine
```

Web text is noisy, so expect the occasional English boilerplate line even in `tl` rows; bump `min_quality` in `iter_texts` if you need stricter filtering.

Useful row fields: `text`, `language` (e.g. `tl`), `language_bucket` (register, e.g. `filipino_formal`), `quality_score`, `quality_bucket` (A/B/C), `source`, `url`, `title`.
