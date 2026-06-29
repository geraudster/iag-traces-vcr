import os
import json
from functools import wraps

# 1. Load the shared Langfuse trajectory data
try:
    with open("mock_trajectory.json", "r") as f:
        MOCK_DATA = json.load(f)
except FileNotFoundError:
    MOCK_DATA = {}

def is_fuzzy_match(expected: dict, actual: dict) -> bool:
    """Checks if the actual kwargs contain the expected key-value pairs."""
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return expected == actual
    
    for key, val in expected.items():
        if key not in actual:
            return False
        if isinstance(val, str) and isinstance(actual[key], str):
            if val.lower() != actual[key].lower():
                return False
        elif val != actual[key]:
            return False
    return True

def vcr_mock(tool_name: str):
    """
    Decorator to intercept native tool calls and return mocked data.
    Only activates if the VCR_MODE environment variable is set to 'true'.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # If not in VCR mode, run the real tool normally
            if os.getenv("VCR_MODE", "false").lower() != "true":
                return func(*args, **kwargs)
                
            print(f"[VCR] Intercepting native tool: {tool_name}")
            
            if tool_name not in MOCK_DATA:
                raise ValueError(f"VCR Error: '{tool_name}' not in mock data.")
                
            # Most agent frameworks pass tool inputs as kwargs
            # We compare the kwargs against the expected Langfuse input
            for call in MOCK_DATA[tool_name]:
                expected_input = call.get("expected_input", {})
                
                if is_fuzzy_match(expected_input, kwargs):
                    print(f"[VCR] Match found for {tool_name}. Returning mock.")
                    return call.get("mocked_output")
                    
            raise ValueError(f"VCR Error: No match for {tool_name} with args: {kwargs}")
            
        return wrapper
    return decorator
