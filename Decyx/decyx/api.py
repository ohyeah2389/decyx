import json
import re

from anthropic import Anthropic
from anthropic import APIConnectionError, APIError, APIStatusError

def parse_json_response(content):
    """Parse the JSON response from Claude API.

    Args:
        content (str): The response content as a string.

    Returns:
        dict: The parsed JSON object, or None if parsing failed.
    """
    decoder = json.JSONDecoder()
    candidates = [content]
    candidates.extend(
        match.group(1)
        for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", content, re.IGNORECASE)
    )

    for candidate in candidates:
        for i, ch in enumerate(candidate):
            if ch != "{":
                continue
            try:
                parsed_json, _ = decoder.raw_decode(candidate, i)
                return parsed_json
            except ValueError:
                continue

    print("No valid JSON object found in Claude's response.")
    return None

def extract_text_content(message):
    """Extract plain text blocks from an Anthropic message response."""
    text_blocks = [
        block.text for block in getattr(message, "content", [])
        if getattr(block, "type", None) == "text"
    ]
    return "".join(text_blocks).strip()

def get_response_from_claude(prompt, api_key, model, monitor, is_explanation=False):
    """Get a response from the Claude API.

    Args:
        prompt (str): The prompt to send to the Claude API.
        api_key (str): The API key for authentication.
        model (str): The model name to use.
        monitor (object): An object with a setMessage method to display status messages.
        is_explanation (bool, optional): Flag indicating if the response is an explanation. Defaults to False.

    Returns:
        dict or str: The parsed JSON response, or the content string if is_explanation is True.
    """
    try:
        monitor.setMessage("Sending request to Claude API...")
        client = Anthropic(api_key=api_key)
        monitor.setMessage("Waiting for response from Claude API...")
        message = client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=6000,
            temperature=0.2,
        )

        content_text = extract_text_content(message)
        if content_text:
            print("Received response from Claude API.")

            if is_explanation:
                return content_text
            return parse_json_response(content_text)

        print("Received empty content from Claude API.")
        return None

    except APIStatusError as e:
        print("Claude API status error {}: {}".format(e.status_code, str(e)))
        return None
    except APIConnectionError as e:
        print("Failed to reach Claude API: {}".format(e))
        return None
    except APIError as e:
        print("Claude API error: {}".format(e))
        return None
    except Exception as e:
        print("Unexpected exception in get_response_from_claude: {}".format(e))
        return None
    finally:
        monitor.setMessage("")
