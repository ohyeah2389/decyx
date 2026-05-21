# api.py

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from decyx.config import CLAUDE_API_URL

def send_request(url, headers, data):
    """Send a POST request to the specified URL with the given headers and data.

    Args:
        url (str): The URL to send the request to.
        headers (dict): A dictionary of HTTP headers to include in the request.
        data (dict): The data to send in the body of the request.

    Returns:
        urllib.response.addinfourl or urllib.error.HTTPError: The response object returned by the server.
    """
    req = Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        return urlopen(req)
    except HTTPError as e:
        return e
    except URLError as e:
        print("Failed to reach server: {}".format(e.reason))
        return None

def read_response(response):
    """Read the response from the response object.

    Args:
        response (urllib.response.addinfourl or urllib.error.HTTPError): The response object returned by send_request.

    Returns:
        str: The content of the response as a string, or None if an error occurred.
    """
    if response is None:
        return None
    elif isinstance(response, HTTPError):
        error_content = response.read()
        print("Error: HTTP response code {}".format(response.code))
        print("Error message: {}".format(error_content.decode("utf-8", errors="replace")))
        return None
    else:
        return response.read().decode("utf-8", errors="replace")

def parse_json_response(content):
    """Parse the JSON response from Claude API.

    Args:
        content (str): The response content as a string.

    Returns:
        dict: The parsed JSON object, or None if parsing failed.
    """
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    if json_start != -1 and json_end != -1:
        json_str = content[json_start:json_end]
        try:
            return json.loads(json_str)
        except ValueError as e:
            print("Failed to parse JSON from Claude's response: {}".format(str(e)))
    else:
        print("No JSON object found in Claude's response")
    return None

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
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.2,
        }

        print("Sending request to Claude API...")
        response = send_request(CLAUDE_API_URL, headers, data)

        monitor.setMessage("Waiting for response from Claude API...")
        content = read_response(response)

        if content:
            print("Received response from Claude API.")
            response_json = json.loads(content)
            content_text = response_json['content'][0]['text']

            if is_explanation:
                return content_text.strip()
            else:
                return parse_json_response(content_text)

        return None

    except Exception as e:
        print("Exception in get_response_from_claude: {}".format(e))
        return None
    finally:
        monitor.setMessage("")
