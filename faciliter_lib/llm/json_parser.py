from faciliter_lib import get_module_logger
import json
import re

logger = get_module_logger()

def clean_and_parse_json_response(response_str):
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

    # Try direct parsing first
    try:
        parsed = json.loads(response_str)
        # Ensure it's a list
        if isinstance(parsed, list):
            logger.info(f"Successfully parsed JSON array with {len(parsed)} items")
            return parsed
        elif isinstance(parsed, dict):
            logger.info("Parsed single JSON object, converting to list")
            return [parsed]
        else:
            logger.warning(f"Parsed JSON is not array or object, got: {type(parsed)}")
            return None
    except json.JSONDecodeError as e:
        logger.debug(f"Direct JSON parsing failed: {e}")

    # Remove common text wrappers that models might add
    clean_response = response_str.strip()
    
    # Remove markdown code blocks if present
    if clean_response.startswith("```json") and clean_response.endswith("```"):
        clean_response = clean_response[7:-3].strip()
    elif clean_response.startswith("```") and clean_response.endswith("```"):
        clean_response = clean_response[3:-3].strip()
    
    # Try parsing cleaned response
    try:
        parsed = json.loads(clean_response)
        if isinstance(parsed, list):
            logger.info(f"Successfully parsed cleaned JSON array with {len(parsed)} items")
            return parsed
        elif isinstance(parsed, dict):
            logger.info("Parsed single cleaned JSON object, converting to list")
            return [parsed]
        else:
            logger.warning(f"Cleaned JSON is not array or object, got: {type(parsed)}")
            return None
    except json.JSONDecodeError:
        logger.debug("Cleaned JSON parsing also failed, trying substring extraction")

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
    
