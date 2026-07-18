# Frozen contracts (spec.md §6.1–§6.7)

Human-readable copy of shapes. Machine types live in `schemas.py`.  
**Additive-only** mid-sprint; consumers ignore unknown fields (spec §6.9).

## 6.1 FileRecord (indexer)

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | Absolute path |
| `filename` | string | Basename |
| `extension` | string | Includes leading dot |
| `size_bytes` | int | File size |
| `created_at` | string | ISO-8601 UTC |
| `modified_at` | string | ISO-8601 UTC |

Indexer returns `FileRecord[]` for top-level files in the scan folder.

## 6.2 ExtractedContent (extractor)

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | Absolute path |
| `extractable` | bool | False for unsupported/binary |
| `text_snippet` | string \| null | Null when not extractable; ~500–1000 chars when true |
| `extraction_method` | string | e.g. `pdf_text_layer`, `unsupported` |

## 6.3 QueryIntent (NLU)

| Field | Type | Notes |
|-------|------|-------|
| `raw_query` | string | User text as typed |
| `description` | string | Normalized description |
| `time_hint` | object \| null | `{type, value, resolved_range}` |
| `type_hint` | string \| null | Implied file type |
| `language_mix` | string | e.g. `taglish`, `en`, `tl` |

## 6.4 MatchResult (matcher / Cody)

| Field | Type | Notes |
|-------|------|-------|
| `best_match` | object | `{path, confidence, reasoning}` |
| `alternatives` | array | `{path, confidence}` (+ optional reasoning) |

## 6.5 RevealRequest (reveal input)

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | Resolved absolute path |

Entry `reveal(path) -> bool` (side effect + success).

## 6.6 SpeechRequest (voice)

| Field | Type | Notes |
|-------|------|-------|
| `filename` | string | Spoken name |
| `language_mode` | string | `en` / `tl` / `auto` |

Entry `speak(filename, language_mode) -> bool`.

## 6.7 RevealAnimation (orchestration-built)

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | Matched file |
| `root` | string | Scan root |
| `segments` | string[] | Path segments relative to root |
