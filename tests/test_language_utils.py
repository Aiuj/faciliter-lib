import unittest
from faciliter_lib.utils.language_utils import LanguageUtils

class TestLanguageUtils(unittest.TestCase):
    # Tests for crop_text_preserve_words method
    def test_crop_text_short_text(self):
        """Test that short text is returned unchanged"""
        text = "Short text."
        result = LanguageUtils.crop_text_preserve_words(text, max_length=50)
        self.assertEqual(result, text)

    def test_crop_text_at_sentence_boundary(self):
        """Test cropping at sentence boundary"""
        text = "First sentence. Second sentence. Third sentence."
        result = LanguageUtils.crop_text_preserve_words(text, max_length=20, prefer_sentences=True)
        self.assertEqual(result, "First sentence.")

    def test_crop_text_at_word_boundary(self):
        """Test cropping at word boundary when no sentence boundary is suitable"""
        text = "This is a very long phrase without any punctuation that goes on and on"
        result = LanguageUtils.crop_text_preserve_words(text, max_length=30, min_word_boundary=20)
        # Should crop at word boundary, not mid-word
        self.assertFalse(' ' in result[-1:])  # Shouldn't end with space
        self.assertTrue(len(result) <= 30)
        self.assertTrue(len(result) >= 20)  # Above min_word_boundary
        # Check that it's not cutting mid-word by ensuring last char is not in middle of a word
        words = text.split()
        result_words = result.split()
        # The result should end with a complete word
        if result_words:
            last_word_in_result = result_words[-1]
            self.assertTrue(any(word.startswith(last_word_in_result) for word in words))

    def test_crop_text_exact_length(self):
        """Test text that is exactly at max_length"""
        text = "Exactly fifty characters long text here now!"  # 44 chars
        result = LanguageUtils.crop_text_preserve_words(text, max_length=44)
        self.assertEqual(result, text)

    def test_crop_text_disable_sentence_preference(self):
        """Test with prefer_sentences=False"""
        text = "First sentence. Second sentence with more content."
        result = LanguageUtils.crop_text_preserve_words(text, max_length=30, prefer_sentences=False)
        # Should not stop at first sentence, but crop to word boundary
        self.assertNotEqual(result, "First sentence.")
        self.assertTrue(len(result) <= 30)

    def test_crop_text_custom_min_word_boundary(self):
        """Test with custom min_word_boundary"""
        text = "This is a test sentence with multiple words"
        result = LanguageUtils.crop_text_preserve_words(text, max_length=25, min_word_boundary=10)
        self.assertTrue(len(result) <= 25)
        self.assertTrue(len(result) >= 10)

    def test_crop_text_invalid_input_type(self):
        """Test that non-string input raises ValueError"""
        with self.assertRaises(ValueError):
            LanguageUtils.crop_text_preserve_words(123, max_length=50)

    def test_crop_text_invalid_max_length(self):
        """Test that invalid max_length raises ValueError"""
        with self.assertRaises(ValueError):
            LanguageUtils.crop_text_preserve_words("test", max_length=0)
        
        with self.assertRaises(ValueError):
            LanguageUtils.crop_text_preserve_words("test", max_length=-5)

    def test_crop_text_default_parameters(self):
        """Test default parameter values"""
        long_text = "This is a sentence. " * 30  # Very long text
        result = LanguageUtils.crop_text_preserve_words(long_text)
        self.assertTrue(len(result) <= 500)  # Default max_length
        self.assertEqual(result, "This is a sentence.")  # Should crop at first sentence

    # Existing language detection tests
    def test_detect_language_english(self):
        text = "This is a test sentence."
        lang = LanguageUtils.detect_language(text)
        self.assertEqual(lang["lang"], "en")

    def test_detect_language_french(self):
        text = "Ceci est une phrase de test."
        lang = LanguageUtils.detect_language(text)
        self.assertEqual(lang["lang"], "fr")

    def test_detect_language_spanish(self):
        text = "Esta es una frase de prueba."
        lang = LanguageUtils.detect_language(text)
        self.assertEqual(lang["lang"], "es")

    def test_detect_language_with_newlines(self):
        """Test that newlines are properly handled"""
        text = "This is a test\nsentence with\nnewlines."
        lang = LanguageUtils.detect_language(text)
        self.assertEqual(lang["lang"], "en")

    def test_detect_language_long_text(self):
        """Test that long text is properly truncated"""
        text = "This is a very long sentence. " * 50  # Creates very long text
        lang = LanguageUtils.detect_language(text)
        self.assertEqual(lang["lang"], "en")

    def test_detect_language_first_sentence_extraction(self):
        """Test that first sentence is extracted from multi-sentence text when text is long enough"""
        # Create text long enough to trigger cropping
        text = "This is the first sentence in English language and it needs to be long. " + "Esta es una segunda frase en español. " * 20
        lang = LanguageUtils.detect_language(text)
        self.assertEqual(lang["lang"], "en")  # Should detect English from first sentence

    def test_detect_language_empty_string(self):
        """Test that empty string raises ValueError"""
        with self.assertRaises(ValueError):
            LanguageUtils.detect_language("")

    def test_detect_language_whitespace_only(self):
        """Test that whitespace-only string raises ValueError"""
        with self.assertRaises(ValueError):
            LanguageUtils.detect_language("   \n\t   ")

    def test_detect_language_non_string_input(self):
        """Test that non-string input raises ValueError"""
        with self.assertRaises(ValueError):
            LanguageUtils.detect_language(123)

    def test_detect_language_too_short(self):
        """Test that very short text raises ValueError"""
        with self.assertRaises(ValueError):
            LanguageUtils.detect_language("ab")

    def test_detect_language_whitespace_trimming(self):
        """Test that leading/trailing whitespace is properly trimmed"""
        text = "   This is a test sentence.   "
        lang = LanguageUtils.detect_language(text)
        self.assertEqual(lang["lang"], "en")

if __name__ == "__main__":
    unittest.main()
