import os
import shutil
import subprocess
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from agent_memory import init_db

# Protected paths and extensions that cannot be read or modified by workspace tools
PROTECTED_PATHS = {'.env', '.git', 'data', '__pycache__', '.streamlit', 'agent_memory.db'}
MAX_FILE_SIZE_BYTES = 500 * 1024  # 500 KB limit for reading/writing

def get_workspace_root() -> str:
    return os.path.abspath(os.getcwd())

def is_safe_path(rel_path: str) -> tuple[bool, str]:
    """Validate that rel_path is contained within workspace root and not protected."""
    if not rel_path or not isinstance(rel_path, str):
        return False, "Invalid path."
    
    # Normalize and check for absolute path or traversal
    clean_path = rel_path.strip().replace('\\', '/')
    if clean_path.startswith('/') or ':' in clean_path:
        return False, "Absolute paths are prohibited."
    
    parts = clean_path.split('/')
    if '..' in parts:
        return False, "Path traversal ('..') is prohibited."
        
    # Check against protected root parts
    if parts[0] in PROTECTED_PATHS:
        return False, f"Access to protected path '{parts[0]}' is prohibited."
        
    abs_path = os.path.abspath(os.path.join(get_workspace_root(), clean_path))
    workspace_root = get_workspace_root()
    
    if not abs_path.startswith(workspace_root):
        return False, "Path resolves outside workspace root."
        
    return True, abs_path

def log_audit(task_id: Optional[int], tool_type: str, target_path: str, success: bool, summary: str):
    """Log audit record to memory database."""
    try:
        init_db()
        import sqlite3
        conn = sqlite3.connect("data/agent_memory.db")
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        # Use memory_logs or create audit table if needed. memory_logs supports task_id.
        # If task_id is None, use task_id = 1 or store in memory_logs with task_id = 1.
        t_id = task_id if task_id else 1
        cursor.execute('''
            INSERT INTO memory_logs (task_id, summary, timestamp)
            VALUES (?, ?, ?)
        ''', (t_id, f"[TOOL:{tool_type}] Target: {target_path} | Success: {success} | {summary}", now))
        conn.commit()
        conn.close()
    except Exception:
        pass

def list_workspace_files(task_id: Optional[int] = None) -> List[str]:
    root = get_workspace_root()
    files_list = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune protected directories
        dirnames[:] = [d for d in dirnames if d not in PROTECTED_PATHS and not d.startswith('.')]
        for f in filenames:
            if f.startswith('.'):
                continue
            full_p = os.path.join(dirpath, f)
            rel_p = os.path.relpath(full_p, root).replace('\\', '/')
            files_list.append(rel_p)
    log_audit(task_id, "LIST", "workspace", True, f"Listed {len(files_list)} files.")
    return sorted(files_list)

def read_text_file(rel_path: str, task_id: Optional[int] = None) -> tuple[bool, str]:
    safe, res = is_safe_path(rel_path)
    if not safe:
        log_audit(task_id, "READ", rel_path, False, res)
        return False, f"Error: {res}"
        
    abs_path = res
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        log_audit(task_id, "READ", rel_path, False, "File not found.")
        return False, "Error: File not found."
        
    if os.path.getsize(abs_path) > MAX_FILE_SIZE_BYTES:
        log_audit(task_id, "READ", rel_path, False, "File exceeds size limit.")
        return False, "Error: File size exceeds 500KB limit."
        
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        log_audit(task_id, "READ", rel_path, True, f"Read {len(content)} characters.")
        return True, content
    except Exception as e:
        log_audit(task_id, "READ", rel_path, False, str(e))
        return False, f"Error reading file: {str(e)}"

def write_workspace_file(rel_path: str, content: str, task_id: Optional[int] = None) -> tuple[bool, str]:
    safe, res = is_safe_path(rel_path)
    if not safe:
        log_audit(task_id, "WRITE", rel_path, False, res)
        return False, f"Error: {res}"
        
    abs_path = res
    if len(content.encode('utf-8')) > MAX_FILE_SIZE_BYTES:
        log_audit(task_id, "WRITE", rel_path, False, "Content exceeds size limit.")
        return False, "Error: Content size exceeds 500KB limit."
        
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_audit(task_id, "WRITE", rel_path, True, f"Wrote {len(content)} characters.")
        return True, f"Successfully wrote to {rel_path}."
    except Exception as e:
        log_audit(task_id, "WRITE", rel_path, False, str(e))
        return False, f"Error writing file: {str(e)}"

def search_workspace(query: str, task_id: Optional[int] = None) -> List[str]:
    if not query or len(query.strip()) < 2:
        return []
    matches = []
    root = get_workspace_root()
    q_lower = query.lower()
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in PROTECTED_PATHS and not d.startswith('.')]
        for f in filenames:
            if f.startswith('.'):
                continue
            full_p = os.path.join(dirpath, f)
            rel_p = os.path.relpath(full_p, root).replace('\\', '/')
            # Search filename or content if text file
            if q_lower in rel_p.lower():
                matches.append(f"{rel_p} (Filename match)")
                continue
            try:
                if os.path.getsize(full_p) < 100 * 1024:
                    with open(full_p, 'r', encoding='utf-8', errors='ignore') as file_obj:
                        if q_lower in file_obj.read().lower():
                            matches.append(f"{rel_p} (Content match)")
            except Exception:
                pass
    log_audit(task_id, "SEARCH", query, True, f"Found {len(matches)} matches.")
    return matches

# Approved command allowlist for strict execution runner (default disabled)
APPROVED_COMMANDS = {
    "git status",
    "git diff",
    "pytest",
    "python -m py_compile app.py agent_memory.py workspace_tools.py"
}

def run_approved_command(command: str, enabled: bool = False, task_id: Optional[int] = None) -> tuple[bool, str]:
    if not enabled:
        log_audit(task_id, "EXEC", command, False, "Command execution is disabled by default.")
        return False, "Error: Command execution is disabled by default. Enable explicitly in settings."
        
    clean_cmd = command.strip()
    if clean_cmd not in APPROVED_COMMANDS:
        log_audit(task_id, "EXEC", clean_cmd, False, "Command not on strict allowlist.")
        return False, f"Error: Command '{clean_cmd}' is not allowed. Only pre-approved diagnostic commands are permitted."
        
    try:
        result = subprocess.run(
            clean_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=get_workspace_root()
        )
        output = f"Exit Code: {result.returncode}\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
        success = (result.returncode == 0)
        log_audit(task_id, "EXEC", clean_cmd, success, f"Exit code {result.returncode}")
        return success, output
    except subprocess.TimeoutExpired:
        log_audit(task_id, "EXEC", clean_cmd, False, "Command timed out.")
        return False, "Error: Command execution timed out after 10 seconds."
    except Exception as e:
        log_audit(task_id, "EXEC", clean_cmd, False, str(e))
        return False, f"Error executing command: {str(e)}"
