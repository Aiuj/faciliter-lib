"""Tests for JSON parser utilities."""

import pytest
from pydantic import BaseModel, Field

from faciliter_lib.llm.json_parser import (
    extract_json_from_text,
    parse_structured_output,
    augment_prompt_for_json,
)


class SampleSchema(BaseModel):
    """Test schema for structured output."""
    result: str
    score: float
    is_valid: bool


class TestExtractJsonFromText:
    """Test JSON extraction from text."""
    
    def test_extract_valid_json_object(self):
        """Test extracting valid JSON object."""
        text = '{"key": "value", "number": 42}'
        result = extract_json_from_text(text)
        assert result == {"key": "value", "number": 42}
    
    def test_extract_json_with_surrounding_text(self):
        """Test extracting JSON from text with surrounding content."""
        text = 'Here is the result: {"key": "value"} and some more text'
        result = extract_json_from_text(text)
        assert result == {"key": "value"}
    
    def test_extract_json_array(self):
        """Test extracting JSON array."""
        text = '[{"item": 1}, {"item": 2}]'
        result = extract_json_from_text(text)
        assert result == [{"item": 1}, {"item": 2}]
    
    def test_extract_json_in_code_block(self):
        """Test extracting JSON from markdown code block."""
        text = '```json\n{"key": "value"}\n```'
        # This won't work with just the regex, but shows the pattern
        result = extract_json_from_text(text)
        assert result == {"key": "value"}
    
    def test_no_json_in_text(self):
        """Test when no JSON is present."""
        text = "This is just plain text with no JSON"
        result = extract_json_from_text(text)
        assert result is None
    
    def test_empty_text(self):
        """Test with empty text."""
        result = extract_json_from_text("")
        assert result is None


class TestParseStructuredOutput:
    """Test structured output parsing."""
    
    def test_parse_valid_structured_output(self):
        """Test parsing valid structured output."""
        text = '{"result": "success", "score": 0.95, "is_valid": true}'
        result = parse_structured_output(text, SampleSchema)
        
        assert result is not None
        assert result["result"] == "success"
        assert result["score"] == 0.95
        assert result["is_valid"] is True
    
    def test_parse_structured_output_with_text(self):
        """Test parsing structured output embedded in text."""
        text = 'Here is the analysis:\n{"result": "success", "score": 0.95, "is_valid": true}\nEnd of analysis'
        result = parse_structured_output(text, SampleSchema)
        
        assert result is not None
        assert result["result"] == "success"
    
    def test_parse_invalid_schema(self):
        """Test parsing with invalid schema."""
        text = '{"wrong_field": "value"}'
        result = parse_structured_output(text, SampleSchema)
        
        assert result is None
    
    def test_parse_no_json(self):
        """Test parsing when no JSON is present."""
        text = "No JSON here"
        result = parse_structured_output(text, SampleSchema)
        
        assert result is None


class TestAugmentPromptForJson:
    """Test prompt augmentation for JSON output."""
    
    def test_augment_prompt(self):
        """Test that prompt is augmented with schema."""
        prompt = "Analyze this data"
        result = augment_prompt_for_json(prompt, SampleSchema)
        
        assert "Analyze this data" in result
        assert "JSON" in result
        assert "schema" in result.lower()
        assert "result" in result  # Field from schema
        assert "score" in result   # Field from schema
    
    def test_augment_empty_prompt(self):
        """Test augmenting empty prompt."""
        result = augment_prompt_for_json("", SampleSchema)
        
        assert "JSON" in result
        assert "result" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
