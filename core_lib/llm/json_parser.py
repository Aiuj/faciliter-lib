from core_lib import get_module_logger
import json
import re
from typing import Dict, Any, Optional, Type

from pydantic import BaseModel, ValidationError

logger = get_module_logger()

def clean_and_parse_json_response(response_str, force_list=False):
    """
    Extracts and parses a JSON array from the response string.
    Handles corrupted or incomplete responses by finding the valid JSON portion.
    Returns a list of dict or None if parsing fails.
    """
    # Handle None or empty input
    if not response_str:
        logger.warning("Empty or None response string provided for JSON parsing")
        return None

    # Convert to string if needed
    if not isinstance(response_str, str):
        response_str = str(response_str)


    # Log the raw response for debugging (truncated if too long)
    response_preview = response_str[:500] + "..." if len(response_str) > 500 else response_str
    logger.debug(f"Parsing JSON response: {response_preview}")

    # Remove common text wrappers that models might add
    clean_response = response_str.strip()
    
    # Remove markdown code blocks if present
    if clean_response.startswith("```json") and clean_response.endswith("```"):
        clean_response = clean_response[7:-3].strip()
    elif clean_response.startswith("```") and clean_response.endswith("```"):
        clean_response = clean_response[3:-3].strip()
    

    # Try direct parsing first on clean string
    try:
        parsed = json.loads(clean_response)
        # Ensure it's a list
        if isinstance(parsed, list):
            logger.info(f"Successfully parsed JSON array with {len(parsed)} items")
            return parsed
        elif isinstance(parsed, dict):
            if force_list:
                logger.info("Parsed single JSON object, converting to list")
                return [parsed]
            else:
                logger.info("Parsed single JSON object")
                return parsed
        else:
            logger.warning(f"Parsed JSON is not array or object, got: {type(parsed)}")
            return None
    except json.JSONDecodeError as e:
        logger.debug(f"Direct JSON parsing failed: {e}")

    # Try to extract as many valid JSON objects/arrays as possible from a possibly truncated response
    # This will extract items from a top-level array, even if the last item is incomplete
    # Only works for top-level arrays (not objects)
    array_match = re.search(r'\[.*', clean_response, re.DOTALL)
    if array_match:
        array_str = array_match.group(0)
        # Remove trailing commas before closing brackets
        array_str = re.sub(r',([\s]*[\]])', r'\1', array_str)
        # Try to extract as many complete items as possible
        items = []
        decoder = json.JSONDecoder()
        idx = 0
        # Skip initial whitespace and opening bracket
        while idx < len(array_str) and array_str[idx] not in '[{':
            idx += 1
        if idx < len(array_str) and array_str[idx] == '[':
            idx += 1
        while idx < len(array_str):
            # Skip whitespace and commas
            while idx < len(array_str) and array_str[idx] in ' \n\r\t,':
                idx += 1
            if idx >= len(array_str) or array_str[idx] == ']':
                break
            try:
                obj, end = decoder.raw_decode(array_str, idx)
                items.append(obj)
                idx = end
            except json.JSONDecodeError:
                # Truncated/incomplete item at the end, ignore
                break
        if items:
            logger.info(f"Successfully extracted {len(items)} JSON items from possibly truncated array")
            return items
        else:
            logger.warning("No complete JSON items could be extracted from array")
            return None

    # If not a top-level array, try to extract as many objects as possible (for object streams)
    # This is less robust, but can help if the response is a stream of objects
    object_matches = list(re.finditer(r'\{', clean_response))
    if object_matches:
        items = []
        decoder = json.JSONDecoder()
        idx = 0
        while idx < len(clean_response):
            # Find next object
            next_obj = clean_response.find('{', idx)
            if next_obj == -1:
                break
            try:
                obj, end = decoder.raw_decode(clean_response, next_obj)
                items.append(obj)
                idx = end
            except json.JSONDecodeError:
                # Truncated/incomplete object at the end, ignore
                break
        if items:
            logger.info(f"Successfully extracted {len(items)} JSON objects from possibly truncated stream")
            return items
        else:
            logger.warning("No complete JSON objects could be extracted from stream")
            return None

    logger.warning("No JSON brackets found in response or unable to extract valid items")
    return None


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from text response.
    
    Tries multiple strategies:
    1. Parse entire text as JSON
    2. Find JSON object with regex (first {...})
    3. Find JSON array with regex (first [...])
    
    Args:
        text: Text response that may contain JSON
        
    Returns:
        Parsed JSON dict/list or None if extraction fails
    """
    if not text:
        return None
    
    # Strategy 1: Try parsing entire text as JSON
    try:
        result = json.loads(text.strip())
        if isinstance(result, (dict, list)):
            return result
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Strategy 2: Extract first JSON object {...}
    json_obj_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_obj_match:
        try:
            result = json.loads(json_obj_match.group())
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Strategy 3: Extract first JSON array [...]
    json_arr_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_arr_match:
        try:
            result = json.loads(json_arr_match.group())
            if isinstance(result, list):
                return result
        except (json.JSONDecodeError, ValueError):
            pass
    
    return None


def parse_structured_output(
    text: str,
    schema: Type[BaseModel],
) -> Optional[Dict[str, Any]]:
    """Parse text response into structured output matching Pydantic schema.
    
    This is a fallback when native structured output is not available.
    
    Args:
        text: LLM text response
        schema: Pydantic model defining expected structure
        
    Returns:
        Dict matching schema or None if parsing/validation fails
    """
    # Extract JSON from text
    json_data = extract_json_from_text(text)
    if json_data is None:
        logger.warning("Could not extract JSON from LLM response for structured output")
        return None
    
    # Validate against Pydantic schema
    try:
        validated = schema.model_validate(json_data)
        return validated.model_dump()
    except ValidationError as e:
        logger.warning(
            f"JSON validation failed against schema {schema.__name__}: {e}",
            extra={"validation_errors": e.errors()}
        )
        return None
    except Exception as e:
        logger.warning(f"Unexpected error validating JSON: {e}")
        return None


def augment_prompt_for_json(
    prompt: str,
    schema: Type[BaseModel],
) -> str:
    """Augment prompt to request JSON output matching schema.
    
    Args:
        prompt: Original user prompt
        schema: Pydantic model defining expected structure
        
    Returns:
        Enhanced prompt requesting JSON format
    """
    # Get schema description
    schema_json = schema.model_json_schema()
    
    # Build JSON format instruction
    json_instruction = f"""
Your response MUST be valid JSON matching this exact schema:

{json.dumps(schema_json, indent=2)}

Respond ONLY with the JSON object, no additional text or explanation.
"""
    
    return f"{prompt}\n\n{json_instruction}"
