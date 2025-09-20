"""
language_utils.py
Utilities for language manipulation, including detection and future NLP features.

This module provides utilities for:
- Language detection with secure input handling
- Text cropping while preserving word and sentence boundaries
"""

from fast_langdetect import detect
import logging
import re
from typing import List, Dict, Optional

class LanguageUtils:
    @staticmethod
    def crop_text_preserve_words(text: str, max_length: int = 200, prefer_sentences: bool = True, min_word_boundary: int = None) -> str:
        """
        Crops text to a specified length while preserving word boundaries and optionally sentence boundaries.
        
        Args:
            text (str): The input text to crop.
            max_length (int): Maximum length of the cropped text. Default is 500.
            prefer_sentences (bool): If True, tries to crop at sentence boundaries first. Default is True.
            min_word_boundary (int): Minimum length threshold for word boundary breaking. 
                                   If None, defaults to 80% of max_length.
        
        Returns:
            str: The cropped text, preserving word/sentence boundaries when possible.
            
        Raises:
            ValueError: If input is not a string or max_length is not positive.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")
        
        if not isinstance(max_length, int) or max_length <= 0:
            raise ValueError("max_length must be a positive integer.")
        
        # Set default min_word_boundary if not provided
        if min_word_boundary is None:
            min_word_boundary = int(max_length * 0.8)
        
        # If text is already short enough, return as-is
        if len(text) <= max_length:
            return text
        
        cropped_text = text
        
        # Try to crop at sentence boundary if prefer_sentences is True
        if prefer_sentences:
            sentence_endings = ['. ', '! ', '? ']
            first_sentence_end = None
            
            for ending in sentence_endings:
                pos = text.find(ending)
                if pos != -1:
                    if first_sentence_end is None or pos < first_sentence_end:
                        first_sentence_end = pos + len(ending.rstrip())  # Include punctuation but not space
            
            # Use first sentence if it's within the limit and we found one
            if first_sentence_end is not None and first_sentence_end <= max_length:
                cropped_text = text[:first_sentence_end].strip()
                return cropped_text
        
        # Crop to max_length
        cropped_text = text[:max_length].strip()
        
        # Try to break at word boundary if we're above the minimum threshold
        last_space = cropped_text.rfind(' ')
        if last_space > min_word_boundary:
            cropped_text = cropped_text[:last_space].strip()
        
        return cropped_text

    # New helper: normalize raw detector output into a list of {'lang':..., 'score':...}
    @staticmethod
    def _normalize_detector_output(raw) -> List[Dict[str, Optional[float]]]:
        """
        Normalize various detector return shapes into a list of dicts:
        [{'lang': <code>, 'score': <float|None>}, ...]
        """
        out: List[Dict[str, Optional[float]]] = []

        # Single dict result
        if isinstance(raw, dict):
            lang = raw.get("lang") or raw.get("language")
            score = raw.get("score")
            if lang is not None:
                out.append({"lang": lang, "score": score})
            return out

        # Iterable result (list/tuple)
        if isinstance(raw, (list, tuple)):
            for item in raw:
                # tuple/list like ('en', 0.95)
                if isinstance(item, (list, tuple)) and len(item) >= 1:
                    lang = item[0]
                    score = item[1] if len(item) > 1 else None
                    out.append({"lang": lang, "score": score})
                    continue

                # dict like {'lang': 'en', 'score': 0.95}
                if isinstance(item, dict):
                    lang = item.get("lang") or item.get("language")
                    score = item.get("score")
                    if lang is not None:
                        out.append({"lang": lang, "score": score})
                    continue

                # plain string items ['en', 'fr', ...]
                if isinstance(item, str):
                    out.append({"lang": item, "score": None})
                    continue

            return out

        # Plain string result 'en'
        if isinstance(raw, str):
            return [{"lang": raw, "score": None}]

        # Fallback: stringify unknown types
        try:
            return [{"lang": str(raw), "score": None}]
        except Exception:
            raise RuntimeError("Unexpected return type from language detector: %r" % (type(raw),))

    # New helper to centralize preprocessing for detection methods
    @staticmethod
    def _preprocess_text_for_detection(text: str, max_length: int = 500, min_word_boundary: int = 400) -> str:
        """
        Validate and preprocess text for language detection:
        - Ensure it's a non-empty string
        - Trim and remove newlines
        - Collapse whitespace
        - Crop using crop_text_preserve_words
        - Ensure minimum length (>=3) after processing
        Returns the processed text.
        """
        if not isinstance(text, str):
            raise ValueError("Input to detect_language must be a string.")
        text = text.strip()
        if not text:
            raise ValueError("Input text cannot be empty after trimming whitespace.")
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        text = LanguageUtils.crop_text_preserve_words(text, max_length=max_length, prefer_sentences=True, min_word_boundary=min_word_boundary)
        if len(text) < 3:
            raise ValueError("Input text is too short for reliable language detection (minimum 3 characters after processing).")
        return text

    @staticmethod
    def detect_languages(text: str, min_confidence: float = 0.5) -> List[Dict[str, Optional[float]]]:
        """
        Detects languages and returns a list of candidates with scores >= min_confidence.
        Only candidates with a numeric score are considered for thresholding.
        """
        # Reuse centralized preprocessing
        text = LanguageUtils._preprocess_text_for_detection(text, max_length=500, min_word_boundary=400)

        raw = detect(text)
        normalized = LanguageUtils._normalize_detector_output(raw)

        # Filter by min_confidence: only keep entries with numeric score >= min_confidence
        result: List[Dict[str, Optional[float]]] = []
        for entry in normalized:
            score = entry.get("score")
            if isinstance(score, (int, float)) and score >= min_confidence:
                result.append(entry)

        # Optionally sort by score descending (highest confidence first)
        result.sort(key=lambda e: e.get("score", 0.0), reverse=True)
        return result

    @staticmethod
    def detect_language(text: str) -> dict:
        """
        Detects the single best language candidate for the given text.
        Returns a dict {'lang': <code>, 'score': <confidence|None>}.
        Uses the same preprocessing as detect_languages and the normalizer.
        """
        # Reuse centralized preprocessing
        text = LanguageUtils._preprocess_text_for_detection(text, max_length=500, min_word_boundary=400)

        raw = detect(text)
        normalized = LanguageUtils._normalize_detector_output(raw)

        # Choose best candidate by numerical score (None treated as 0.0)
        if not normalized:
            raise RuntimeError("Language detector returned no results.")

        def score_val(d: Dict[str, Optional[float]]) -> float:
            s = d.get("score")
            return float(s) if isinstance(s, (int, float)) else 0.0

        best = max(normalized, key=score_val)
        return {"lang": best.get("lang"), "score": best.get("score")}

    @staticmethod
    def detect_most_common_language(texts: List[str], min_confidence: float = 0.5) -> Optional[str]:
        """
        Detect the most common language across multiple text samples.

        Args:
            texts (List[str]): Iterable of text samples to analyze.
            min_confidence (float): Minimum numeric confidence threshold for per-sample
                candidates (passed to `detect_languages`). Default is 0.5.

        Returns:
            Optional[str]: The most common language code across samples, or `None`
                if no reliable detections were made.
        """
        if not texts:
            return None

        detections: List[str] = []
        for t in texts:
            if not isinstance(t, str):
                continue
            s = t.strip()
            # skip very short samples that aren't useful for detection
            if len(s) < 10:
                continue

            try:
                candidates = LanguageUtils.detect_languages(s, min_confidence=min_confidence)
            except Exception:
                # Avoid failing the whole operation for one bad sample
                logging.getLogger(__name__).warning("Language detection failed for a sample; skipping.")
                continue

            if candidates:
                # candidates are sorted by confidence; take the top candidate's lang
                top = candidates[0]
                lang = top.get("lang")
                if isinstance(lang, str):
                    detections.append(lang)

        if not detections:
            return None

        from collections import Counter

        most_common = Counter(detections).most_common(1)
        return most_common[0][0] if most_common else None
