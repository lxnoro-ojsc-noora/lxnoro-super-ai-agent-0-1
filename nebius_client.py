import os
import requests
from typing import Dict, Any, Optional

NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1"
DEFAULT_NEBIUS_MODEL = "nvidia/nemotron-3-super-120b-a12b"
SUPPORTED_MODELS = {
    "NVIDIA Nemotron 3 Super 120B": "nvidia/nemotron-3-super-120b-a12b",
    "DeepSeek V4.1 Flash 1017": "deepseek/deepseek-v4.1-flash-1017"
}

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

def nebius_chat_completion(prompt: str, model: Optional[str] = None, timeout: int = 60, system_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a real chat completion request to Nebius Token Factory using OpenAI-compatible API.
    Supports both NVIDIA Nemotron and DeepSeek V4.1 Flash 1017 models.
    No mock or simulated paths.
    
    Args:
        prompt: The user prompt string.
        model: Optional model override (e.g. 'nvidia/nemotron-3-super-120b-a12b' or 'deepseek/deepseek-v4.1-flash-1017').
        timeout: Request timeout in seconds (default 60).
        system_prompt: Optional system prompt to guide model behavior.
        
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
            "error": "Nebius API key is missing. Please configure NEBIUS_API_KEY in environment or Streamlit secrets."
        }
        
    target_model = model or get_nebius_model()
    url = f"{NEBIUS_BASE_URL}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 4096
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code != 200:
            error_detail = response.text[:300] if response.text else "No error details"
            return {
                "success": False,
                "error": f"Nebius API error (HTTP {response.status_code}): {error_detail}"
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
            "error": "Nebius API request timed out after {timeout}s."
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Nebius API network error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error during Nebius API call: {str(e)}"
        }
