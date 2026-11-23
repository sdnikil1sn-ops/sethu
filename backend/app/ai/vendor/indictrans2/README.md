# Vendored: IndicTrans2 inference helpers

Source: https://github.com/AI4Bharat/IndicTrans2 at commit `4f08e39cc6bf13cd62e2445dc725f22bff1a9219`
(`inference/`). Licence: MIT (`LICENSE`, copied unchanged). Taken 2026-11-23 from the source archive of that commit.

| File | Upstream | Changes |
|---|---|---|
| `normalize_punctuation.py` | `inference/normalize_punctuation.py` | `regex` replaced by the standard `re` (only standard syntax is used) |
| `normalize_regex_inference.py` | `inference/normalize_regex_inference.py` | the same; `tqdm` and `sys` imports removed (unused); one invalid escape made a raw string |
| `flores_codes_map_indic.py` | `inference/flores_codes_map_indic.py` | none |
| `indic_num_map.py` | `inference/indic_num_map.py` | none |

## Review (2026-11-23)

- The code is pure Python. It uses only `re` and `typing`, with no I/O, no network, no `eval`, and no dynamic import.
- `normalize()` replaces e-mail addresses, URLs and long numbers with placeholders, which `app/ai/translate.py`
  puts back after translation. Nothing is logged.
- No model code is vendored. No `trust_remote_code` is used anywhere. The model is a CTranslate2 directory loaded by
  the `ctranslate2` library, from the checksum-verified registry only.

## Simplified, not vendored (in `app/ai/translate.py`)

The reference `inference/engine.py` also uses `indic-nlp-library` and `sacremoses`. SETHU reimplements their small
part instead of adding those packages (and their dependencies, which include pandas):

- **Transliteration to Devanagari** for Brahmic scripts: an offset mapping between Unicode blocks, the regular case
  of indic-nlp-library's `UnicodeIndicTransliterator`. Its special cases are not reproduced.
- **Tokenising**: punctuation and symbols split from words, which is close to `indic_tokenize.trivial_tokenize`.
- **Not done**: `IndicNormalizerFactory` normalisation (nukta and similar variants) and Moses English
  detokenisation. A short rule removes the space before punctuation instead.

The effect of these simplifications on translation quality is **not measured**. Measure it with
`tests/test_ai_models.py` (it runs only when the real model is installed) before relying on the translations.
