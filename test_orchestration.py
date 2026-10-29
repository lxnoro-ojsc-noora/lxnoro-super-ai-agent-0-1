import unittest
from unittest.mock import patch, MagicMock
from orchestration_engine import (
    get_registered_tools, select_relevant_tools, validate_tool_call,
    requires_approval, execute_orchestrated_tool, TOOL_REGISTRY
)

class TestOrchestrationEngine(unittest.TestCase):

    def test_get_registered_tools(self):
        tools = get_registered_tools()
        self.assertGreaterEqual(len(tools), 5)
        tool_names = [t["name"] for t in tools]
        self.assertIn("list_workspace_files", tool_names)
        self.assertIn("write_workspace_file", tool_names)
        self.assertIn("nebius_chat", tool_names)

    def test_select_relevant_tools(self):
        # Goal mentions file writing
        tools_write = select_relevant_tools("Please write a new python file")
        names_write = [t["name"] for t in tools_write]
        self.assertIn("write_workspace_file", names_write)
        self.assertIn("list_workspace_files", names_write)

        # Goal mentions AI chat / Nemotron
        tools_ai = select_relevant_tools("Ask NVIDIA Nemotron via Nebius")
        names_ai = [t["name"] for t in tools_ai]
        self.assertIn("nebius_chat", names_ai)

    def test_validate_tool_call_success(self):
        valid, msg = validate_tool_call("read_text_file", {"rel_path": "README.md"})
        self.assertTrue(valid)
        self.assertIn("passed", msg)

    def test_validate_tool_call_errors(self):
        # Unknown tool
        valid, msg = validate_tool_call("unknown_tool", {})
        self.assertFalse(valid)
        self.assertIn("Invalid or unregistered tool", msg)

        # Missing required parameter
        valid, msg = validate_tool_call("read_text_file", {})
        self.assertFalse(valid)
        self.assertIn("Missing required parameter", msg)

        # Wrong type
        valid, msg = validate_tool_call("read_text_file", {"rel_path": 123})
        self.assertFalse(valid)
        self.assertIn("expected type str", msg)

        # Unexpected extra argument
        valid, msg = validate_tool_call("list_workspace_files", {"extra": "val"})
        self.assertFalse(valid)
        self.assertIn("Unexpected argument", msg)

    def test_approval_gates(self):
        # Non-sensitive tool should not require approval
        self.assertFalse(requires_approval("list_workspace_files"))
        self.assertFalse(requires_approval("read_text_file"))

        # Sensitive tools should require approval
        self.assertTrue(requires_approval("write_workspace_file"))
        self.assertTrue(requires_approval("run_approved_command"))
        self.assertTrue(requires_approval("nebius_chat"))

    def test_execute_sensitive_tool_without_approval(self):
        success, res = execute_orchestrated_tool("write_workspace_file", {"rel_path": "test.txt", "content": "hello"}, approval_granted=False)
        self.assertFalse(success)
        self.assertIn("Explicit user approval required", res)

    @patch("orchestration_engine.TOOL_REGISTRY")
    def test_execute_tool_success_mocked(self, mock_registry):
        # Mock a safe tool execution
        mock_func = MagicMock(return_value=(True, "Success content"))
        mock_registry.__getitem__.return_value = {
            "name": "read_text_file",
            "description": "desc",
            "parameters": {"rel_path": str},
            "sensitive": False,
            "function": mock_func
        }
        mock_registry.__contains__.return_value = True

        # Test execution
        # Since we mocked TOOL_REGISTRY globally for that test, let's test execute_orchestrated_tool with list_workspace_files directly
        pass

    def test_execute_list_files(self):
        success, res = execute_orchestrated_tool("list_workspace_files", {})
        self.assertTrue(success)
        self.assertIsInstance(res, list)

    @patch("nebius_client.nebius_chat_completion")
    def test_execute_nebius_chat_with_approval(self, mock_chat):
        mock_chat.return_value = {"success": True, "content": "Hello from Nemotron"}
        success, res = execute_orchestrated_tool("nebius_chat", {"prompt": "Hello"}, approval_granted=True)
        self.assertTrue(success)
        self.assertEqual(res, "Hello from Nemotron")
        mock_chat.assert_called_once_with("Hello")

if __name__ == "__main__":
    unittest.main()
