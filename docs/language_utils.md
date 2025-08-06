# Language Utilities

This module provides utilities for standard language manipulation tasks.

## Features

- **Language Detection**: Detects the language of a given text using `fast-langdetect`.


## Usage

```python
from faciliter_lib.utils.language_utils import LanguageUtils

text = "Bonjour tout le monde!"
result = LanguageUtils.detect_language(text)
print(result)  # Output: {'lang': 'fr', 'score': 0.99}
```

## Dependencies

- [fast-langdetect](https://pypi.org/project/fast-langdetect/)
