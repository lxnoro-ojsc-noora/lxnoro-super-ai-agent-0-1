import os
import io
import zipfile
import unittest
from delivery_utils import get_git_status_info, generate_project_zip

class TestDeliveryCenter(unittest.TestCase):

    def test_git_status_inspection(self):
        info = get_git_status_info()
        self.assertIsInstance(info, dict)
        self.assertIn("is_git_repo", info)
        self.assertIn("branch", info)

    def test_zip_generation_and_exclusions(self):
        zip_bytes = generate_project_zip()
        self.assertIsInstance(zip_bytes, bytes)
        self.assertGreater(len(zip_bytes), 0)
        
        # Inspect ZIP contents
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zipf:
            namelist = zipf.namelist()
            
            # Check mandatory files are included
            self.assertIn("app.py", namelist)
            self.assertIn("requirements.txt", namelist)
            self.assertIn("README.md", namelist)
            
            # Check exclusions (no .env, no .git, no database files)
            for name in namelist:
                self.assertFalse(name.startswith(".git/"))
                self.assertFalse(name.startswith("data/"))
                self.assertNotEqual(name, ".env")
                self.assertFalse(name.endswith(".db"))
                self.assertFalse("__pycache__" in name)

if __name__ == "__main__":
    unittest.main()
