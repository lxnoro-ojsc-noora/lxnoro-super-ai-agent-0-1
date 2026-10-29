import os
import unittest
from workspace_tools import (
    is_safe_path, read_text_file, write_workspace_file, 
    run_approved_command, get_workspace_root
)

class TestWorkspaceTools(unittest.TestCase):

    def test_path_traversal_rejection(self):
        # Test traversal attempts
        for bad_path in ["../secret.txt", "foo/../../bar", "..\\windows\\win.ini"]:
            safe, msg = is_safe_path(bad_path)
            self.assertFalse(safe, f"Path '{bad_path}' should be rejected as traversal.")

    def test_absolute_path_rejection(self):
        # Test absolute paths
        for abs_path in ["C:/Windows/System32/cmd.exe", "/etc/passwd"]:
            safe, msg = is_safe_path(abs_path)
            self.assertFalse(safe, f"Absolute path '{abs_path}' should be rejected.")

    def test_protected_paths_rejection(self):
        # Test protected directories/files
        for prot_path in [".env", ".git/config", "data/agent_memory.db", "__pycache__/test.py"]:
            safe, msg = is_safe_path(prot_path)
            self.assertFalse(safe, f"Protected path '{prot_path}' should be rejected.")

    def test_safe_path_acceptance(self):
        # Test valid workspace relative paths
        for good_path in ["app.py", "README.md", "src/utils.py"]:
            safe, msg = is_safe_path(good_path)
            self.assertTrue(safe, f"Valid path '{good_path}' should be accepted: {msg}")

    def test_command_runner_default_disabled(self):
        # Command runner should be disabled by default
        success, output = run_approved_command("git status", enabled=False)
        self.assertFalse(success)
        self.assertIn("disabled by default", output.lower())

    def test_command_runner_disallows_unapproved(self):
        # Command runner should reject unapproved commands even when enabled
        success, output = run_approved_command("rm -rf /", enabled=True)
        self.assertFalse(success)
        self.assertIn("not allowed", output.lower())

    def test_file_read_write_flow(self):
        test_file = "test_temp_output.txt"
        content = "Hello, workspace tools test!"
        
        # Write test file
        success, msg = write_workspace_file(test_file, content)
        self.assertTrue(success, msg)
        
        # Read test file back
        success, read_content = read_text_file(test_file)
        self.assertTrue(success)
        self.assertEqual(read_content, content)
        
        # Cleanup
        abs_p = os.path.join(get_workspace_root(), test_file)
        if os.path.exists(abs_p):
            os.remove(abs_p)

if __name__ == "__main__":
    unittest.main()
