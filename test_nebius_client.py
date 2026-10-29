import os
import unittest
from unittest.mock import patch, MagicMock
import requests
from nebius_client import nebius_chat_completion, get_nebius_api_key, get_nebius_model

class TestNebiusClient(unittest.TestCase):

    def setUp(self):
        # Clear environment variables before each test
        if "NEBIUS_API_KEY" in os.environ:
            del os.environ["NEBIUS_API_KEY"]
        if "NEBIUS_MODEL" in os.environ:
            del os.environ["NEBIUS_MODEL"]

    def test_missing_api_key(self):
        result = nebius_chat_completion("Hello Nemotron")
        self.assertFalse(result["success"])
        self.assertIn("API key is missing", result["error"])
        # Ensure API key is not present in error
        self.assertNotIn("secret", result["error"].lower())

    @patch("requests.post")
    def test_successful_chat_completion(self, mock_post):
        os.environ["NEBIUS_API_KEY"] = "fake-nebius-secret-key-123"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-nebius-1",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello from NVIDIA Nemotron on Nebius Token Factory!"
                    },
                    "finish_reason": "stop"
                }
            ]
        }
        mock_post.return_value = mock_response

        result = nebius_chat_completion("Hello Nemotron")
        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "Hello from NVIDIA Nemotron on Nebius Token Factory!")
        self.assertIn("choices", result["raw"])

        # Verify request parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.tokenfactory.nebius.com/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer fake-nebius-secret-key-123")
        self.assertEqual(kwargs["json"]["model"], "nvidia/nemotron-3-super-120b-a12b")

    @patch("requests.post")
    def test_http_error_handling(self, mock_post):
        os.environ["NEBIUS_API_KEY"] = "fake-nebius-secret-key-123"
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        result = nebius_chat_completion("Hello")
        self.assertFalse(result["success"])
        self.assertIn("HTTP 401", result["error"])
        # Ensure secret key is never leaked in error message
        self.assertNotIn("fake-nebius-secret-key-123", result["error"])

    @patch("requests.post")
    def test_timeout_handling(self, mock_post):
        os.environ["NEBIUS_API_KEY"] = "fake-nebius-secret-key-123"
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        result = nebius_chat_completion("Hello")
        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"].lower())

    @patch("requests.post")
    def test_malformed_response_handling(self, mock_post):
        os.environ["NEBIUS_API_KEY"] = "fake-nebius-secret-key-123"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid_key": "no choices here"}
        mock_post.return_value = mock_response

        result = nebius_chat_completion("Hello")
        self.assertFalse(result["success"])
        self.assertIn("Malformed response", result["error"])

if __name__ == "__main__":
    unittest.main()
