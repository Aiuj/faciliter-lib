# Language Utilities

This module provides utilities for standard language manipulation tasks.

## Features

- **Language Detection**: Detects the language of a given text using `fast-langdetect`.

Two related convenience methods are provided on `LanguageUtils`:

- `detect_language(text: str) -> dict`: Detects the single best language candidate for `text` and returns a dictionary `{'lang': <code>, 'score': <confidence|None>}`. The method preprocesses the input (trims, collapses whitespace, crops long inputs while preserving word/sentence boundaries) and will raise a `ValueError` for non-string or empty inputs. If the underlying detector returns multiple candidates, this method selects the candidate with the highest numeric score (treating missing scores as 0.0).

- `detect_languages(text: str, min_confidence: float = 0.5) -> List[dict]`: Returns a list of language candidate dictionaries `{'lang': <code>, 'score': <float|None>}` whose numeric confidence is greater than or equal to `min_confidence`. The same preprocessing is applied as with `detect_language`. Only candidates with a numeric `score` are considered for thresholding; entries without a numeric score are ignored when applying `min_confidence`. The returned list is sorted by descending confidence.

- `detect_most_common_language(texts: List[str], min_confidence: float = 0.5) -> Optional[str]`: Analyze multiple text samples and return the most common top language detected across samples. Short or invalid samples (non-string, whitespace-only, or under ~10 characters) are skipped. Per-sample detection uses `detect_languages` with the provided `min_confidence`. If no reliable detections are found, the method returns `None`.


## Usage

```python
from core_lib.utils.language_utils import LanguageUtils

text = "Bonjour tout le monde!"

# Single best candidate
best = LanguageUtils.detect_language(text)
print(best)  # Example output: {'lang': 'fr', 'score': 0.99}

# Multiple candidates above a confidence threshold
# Note: only numeric scores are used for thresholding; items without numeric
# scores may be present in detector output but will not pass the numeric filter.
multi = LanguageUtils.detect_languages(text, min_confidence=0.2)
print(multi)  # Example output: [{'lang': 'fr', 'score': 0.99}]

# If you lower the threshold you may see weaker candidates included:
multi_loose = LanguageUtils.detect_languages(text, min_confidence=0.1)
print(multi_loose)  # Example output: [{'lang': 'fr', 'score': 0.99}, {'lang': 'en', 'score': 0.25}]

### Detecting the most common language across samples

If you have several short text samples (for example, multiple fields extracted from a document), you can get the most common detected language using `detect_most_common_language`:

```python
samples = [
	"Bonjour tout le monde! Ceci est un test.",
	"Une autre phrase en français.",
	"Short"  # will be ignored as too short
]

most_common = LanguageUtils.detect_most_common_language(samples, min_confidence=0.2)
print(most_common)  # 'fr' (or None if nothing reliable)
```
```

## Dependencies

- [fast-langdetect](https://pypi.org/project/fast-langdetect/)
