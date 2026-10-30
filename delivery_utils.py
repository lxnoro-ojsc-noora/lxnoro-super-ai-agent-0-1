import os
import io
import zipfile
import subprocess
import requests
import base64
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
        res = subprocess.run("git remote -v", shell=True, capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            lines = res.stdout.strip().split('\n')
            info["remote"] = lines[0].split()[1] if len(lines) > 0 else "Configured"
    except Exception:
        pass
        
    try:
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
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith('.')]
            
            for file in filenames:
                if file in EXCLUDED_FILES or file.startswith('.'):
                    continue
                if any(file.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
                    continue
                    
                full_path = os.path.join(dirpath, file)
                rel_path = os.path.relpath(full_path, root_dir).replace('\\', '/')
                
                if rel_path.startswith('../') or rel_path.startswith('/') or '..' in rel_path.split('/'):
                    continue
                    
                try:
                    zipf.write(full_path, rel_path)
                except Exception:
                    pass
                    
    memory_buffer.seek(0)
    return memory_buffer.getvalue()

def publish_to_github(repo_name: str, token: str, commit_message: str = "LXNORO Autonomous Agent Delivery") -> Dict[str, Any]:
    """
    Publish project workspace files to a GitHub repository using GitHub REST API with user token authorization.
    repo_name: e.g. 'username/repository'
    token: GitHub Personal Access Token with repo permissions
    """
    if not repo_name or not token:
        return {"success": False, "error": "Repository name and GitHub token are required."}
        
    root_dir = os.path.abspath(os.getcwd())
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Handle owner/repo format
    repo_slug = repo_name.strip()
    if "/" not in repo_slug:
        return {"success": False, "error": "Repository name must be in 'owner/repository' format."}
        
    api_base = f"https://api.github.com/repos/{repo_slug}"
    
    try:
        r = requests.get(api_base, headers=headers, timeout=10)
        if r.status_code == 404:
            create_url = "https://api.github.com/user/repos"
            c_resp = requests.post(create_url, headers=headers, json={"name": repo_slug.split('/')[-1], "private": False}, timeout=10)
            if c_resp.status_code not in [200, 201]:
                return {"success": False, "error": f"Failed to create GitHub repository (HTTP {c_resp.status_code}): {c_resp.text}"}
        elif r.status_code != 200:
            return {"success": False, "error": f"GitHub API authorization error (HTTP {r.status_code}): {r.text}"}
    except Exception as e:
        return {"success": False, "error": f"GitHub network error: {str(e)}"}
        
    pushed_count = 0
    errors = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith('.')]
        for file in filenames:
            if file in EXCLUDED_FILES or file.startswith('.'):
                continue
            if any(file.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
                continue
                
            full_path = os.path.join(dirpath, file)
            rel_path = os.path.relpath(full_path, root_dir).replace('\\', '/')
            
            try:
                with open(full_path, 'rb') as f:
                    content_bytes = f.read()
                content_encoded = base64.b64encode(content_bytes).decode('utf-8')
                
                file_url = f"{api_base}/contents/{rel_path}"
                existing_resp = requests.get(file_url, headers=headers, timeout=5)
                sha = None
                if existing_resp.status_code == 200:
                    sha = existing_resp.json().get("sha")
                    
                payload = {
                    "message": f"{commit_message} - {rel_path}",
                    "content": content_encoded
                }
                if sha:
                    payload["sha"] = sha
                    
                put_resp = requests.put(file_url, headers=headers, json=payload, timeout=10)
                if put_resp.status_code in [200, 201]:
                    pushed_count += 1
                else:
                    errors.append(f"{rel_path}: HTTP {put_resp.status_code}")
            except Exception as ex:
                errors.append(f"{rel_path}: {str(ex)}")
                
    return {
        "success": pushed_count > 0,
        "pushed_count": pushed_count,
        "errors": errors
    }
