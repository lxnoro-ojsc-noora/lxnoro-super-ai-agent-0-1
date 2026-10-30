import os
import requests
from typing import Dict, Any, Optional

NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1"
DEFAULT_NEBIUS_MODEL = "nvidia/nemotron-3-super-120b-a12b"

def get_nebius_api_key() -> str:
    """Read the API key exclusively from server-side st.secrets or environment variables."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "NEBIUS_API_KEY" in st.secrets:
            return str(st.secrets["NEBIUS_API_KEY"]).strip()
    except Exception:
        pass
    return os.getenv("NEBIUS_API_KEY", "").strip()

def get_nebius_model() -> str:
    """Get the configured Nebius model from st.secrets or environment, falling back to default NVIDIA Nemotron model."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "NEBIUS_MODEL" in st.secrets:
            return str(st.secrets["NEBIUS_MODEL"]).strip()
    except Exception:
        pass
    return os.getenv("NEBIUS_MODEL", DEFAULT_NEBIUS_MODEL).strip()

def nebius_chat_completion(prompt: str, model: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Send a chat completion request to Nebius Token Factory using OpenAI-compatible API.
    
    Args:
        prompt: The user prompt string.
        model: Optional model override. Defaults to NEBIUS_MODEL or nvidia/nemotron-3-super-120b-a12b.
        timeout: Request timeout in seconds (default 30).
        
    Returns:
        Dict with keys:
            - success (bool)
            - content (str, optional)
            - error (str, optional)
            - raw (dict, optional)
    """
    api_key = get_nebius_api_key()
    if not api_key:
        return {
            "success": False,
            "error": "Nebius API key is missing. Please set the NEBIUS_API_KEY environment variable."
        }
        
    target_model = model or get_nebius_model()
    url = f"{NEBIUS_BASE_URL}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": target_model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code != 200:
            # Safely log status code without leaking API key or headers
            return {
                "success": False,
                "error": f"Nebius API error (HTTP {response.status_code}): Request failed."
            }
            
        data = response.json()
        
        # Validate OpenAI-compatible response structure
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
                return {
                    "success": True,
                    "content": content,
                    "raw": data
                }
                
        return {
            "success": False,
            "error": "Malformed response received from Nebius API: missing expected 'choices' structure."
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Nebius API request timed out."
        }
    except requests.exceptions.RequestException:
        return {
            "success": False,
            "error": "Nebius API network error occurred."
        }
    except Exception:
        return {
            "success": False,
            "error": "An unexpected error occurred while communicating with Nebius API."
        }
