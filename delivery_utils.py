import os
import io
import zipfile
import subprocess
from typing import Dict, Any, List

EXCLUDED_DIRS = {'.git', 'data', '__pycache__', '.streamlit', '.venv', 'venv', 'dist', 'build'}
EXCLUDED_FILES = {'.env', '.DS_Store', 'agent_memory.db'}
EXCLUDED_EXTENSIONS = {'.pyc', '.pyo', '.pyd'}

def get_git_status_info() -> Dict[str, Any]:
    """Inspect local git repository status safely."""
    info = {
        "is_git_repo": False,
        "branch": "Unknown",
        "remote": "None",
        "status_output": "",
        "uncommitted": False
    }
    
    if not os.path.exists(".git"):
        return info
        
    info["is_git_repo"] = True
    
    try:
        # Branch
        res = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            info["branch"] = res.stdout.strip()
        else:
            res_tag = subprocess.run("git describe --tags --always", shell=True, capture_output=True, text=True, timeout=3)
            if res_tag.returncode == 0:
                info["branch"] = res_tag.stdout.strip()
    except Exception:
        pass
        
    try:
        # Remote
        res = subprocess.run("git remote -v", shell=True, capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            lines = res.stdout.strip().split('\n')
            info["remote"] = lines[0].split()[1] if len(lines) > 0 else "Configured"
    except Exception:
        pass
        
    try:
        # Status
        res = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            status_lines = res.stdout.strip()
            info["status_output"] = status_lines if status_lines else "Working tree clean."
            info["uncommitted"] = bool(status_lines)
    except Exception as e:
        info["status_output"] = f"Error reading git status: {str(e)}"
        
    return info

def generate_project_zip() -> bytes:
    """Generate a clean project ZIP archive excluding secrets, databases, and caches."""
    memory_buffer = io.BytesIO()
    root_dir = os.path.abspath(os.getcwd())
    
    with zipfile.ZipFile(memory_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Prune excluded directories
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith('.')]
            
            for file in filenames:
                if file in EXCLUDED_FILES or file.startswith('.'):
                    continue
                if any(file.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
                    continue
                    
                full_path = os.path.join(dirpath, file)
                rel_path = os.path.relpath(full_path, root_dir).replace('\\', '/')
                
                # Path traversal safety check
                if rel_path.startswith('../') or rel_path.startswith('/') or '..' in rel_path.split('/'):
                    continue
                    
                try:
                    zipf.write(full_path, rel_path)
                except Exception:
                    pass
                    
    memory_buffer.seek(0)
    return memory_buffer.getvalue()
