"""
language_utils.py
Utilities for language manipulation, including detection and future NLP features.

This module provides utilities for:
- Language detection with secure input handling
- Text cropping while preserving word and sentence boundaries
"""

from fast_langdetect import detect

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

    @staticmethod
    def detect_language(text: str) -> dict:
        """
        Detects the language of the given text.
        Args:
            text (str): The input text.
        Returns:
            dict: A dictionary with keys 'lang' (language code, e.g., 'en', 'fr') and 'score' (confidence score).
            Example: {'lang': 'en', 'score': 0.92}
        Notes:
            - Trims whitespace, removes newlines, and limits input to 500 characters for fast-langdetect compatibility.
        """
        # Secure input for fast-langdetect
        if not isinstance(text, str):
            raise ValueError("Input to detect_language must be a string.")
        
        # Trim whitespace
        text = text.strip()
        
        # Check for empty text after trimming
        if not text:
            raise ValueError("Input text cannot be empty after trimming whitespace.")
        
        # Remove newline characters to prevent FastText errors
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove multiple spaces that might result from newline replacement
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Crop text using the dedicated method
        text = LanguageUtils.crop_text_preserve_words(text, max_length=500, prefer_sentences=True, min_word_boundary=400)
        
        # Final check for minimum length
        if len(text) < 3:
            raise ValueError("Input text is too short for reliable language detection (minimum 3 characters after processing).")
        
        return detect(text)
