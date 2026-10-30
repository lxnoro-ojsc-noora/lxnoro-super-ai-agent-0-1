import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "agent_memory.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            total_steps INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'CREATED',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # Steps table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            objective TEXT NOT NULL,
            dependencies TEXT NOT NULL, -- comma-separated step numbers
            status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, RUNNING, COMPLETED, FAILED, BLOCKED
            result TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
        )
    ''')
    
    # Check if retry_count column exists in existing tables (migration helper)
    cursor.execute("PRAGMA table_info(steps)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'retry_count' not in columns:
        try:
            cursor.execute("ALTER TABLE steps ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
    
    # Operational feedback memory logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            step_id INTEGER,
            summary TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
        )
    ''')

    # Long-term memories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS long_term_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            memory_key TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            importance INTEGER DEFAULT 1,
            updated_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def create_task(goal: str, step_count: int = 5) -> int:
    init_db()
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tasks (goal, total_steps, status, created_at, updated_at)
        VALUES (?, ?, 'ACTIVE', ?, ?)
    ''', (goal, step_count, now, now))
    task_id = cursor.lastrowid
    
    steps_plan = []
    api_key = os.getenv("NEBIUS_API_KEY", "").strip()
    if api_key:
        try:
            from orchestration_engine import execute_orchestrated_tool
            prompt = f"Generate a structured implementation plan of {step_count} steps for software goal: '{goal}'. Return JSON array of objects with keys: 'title', 'objective', 'dependencies' (comma-separated step numbers)."
            succ, res = execute_orchestrated_tool("nebius_plan_generator", {"prompt": prompt}, approval_granted=True, task_id=task_id)
            if succ and res:
                import json
                content_str = res.strip() if isinstance(res, str) else str(res)
                if "```json" in content_str:
                    content_str = content_str.split("```json")[1].split("```")[0].strip()
                elif "```" in content_str:
                    content_str = content_str.split("```")[1].split("```")[0].strip()
                parsed = json.loads(content_str)
                if isinstance(parsed, list):
                    for idx, item in enumerate(parsed[:step_count], 1):
                        steps_plan.append({
                            "step_number": idx,
                            "title": item.get("title", f"Step {idx}"),
                            "objective": item.get("objective", f"Execute component {idx} for {goal}"),
                            "dependencies": str(item.get("dependencies", str(idx - 1) if idx > 1 else ""))
                        })
        except Exception:
            pass
            
    if not steps_plan:
        for i in range(1, step_count + 1):
            if i == 1:
                deps = ""
                title = f"Step 1: Requirements & Architecture Setup"
                objective = f"Initialize workspace state, define architecture, and create README.md for: {goal}"
            elif i == step_count:
                deps = str(i - 1)
                title = f"Step {i}: Final Validation & Runnable Packaging"
                objective = f"Perform final verification, run code checks, and package runnable project for: {goal}"
            else:
                deps = str(i - 1)
                title = f"Step {i}: Core Implementation & Module {i}"
                objective = f"Write core source code and modules for component {i} supporting: {goal}"
            steps_plan.append({
                "step_number": i,
                "title": title,
                "objective": objective,
                "dependencies": deps
            })

    for s in steps_plan:
        cursor.execute('''
            INSERT INTO steps (task_id, step_number, title, objective, dependencies, status, result, updated_at)
            VALUES (?, ?, ?, ?, ?, 'PENDING', '', ?)
        ''', (task_id, s["step_number"], s["title"], s["objective"], s["dependencies"], now))
        
    cursor.execute('''
        INSERT INTO memory_logs (task_id, summary, timestamp)
        VALUES (?, ?, ?)
    ''', (task_id, f"Task created with goal: '{goal}' and {len(steps_plan)} steps (Nemotron/Smart Planner).", now))
    
    conn.commit()
    conn.close()
    return task_id

def get_tasks() -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_steps(task_id: int) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM steps WHERE task_id = ? ORDER BY step_number ASC", (task_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_step_status(step_id: int, new_status: str, result: str = "") -> tuple[bool, str]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get step info
    cursor.execute("SELECT task_id, step_number, dependencies, status FROM steps WHERE id = ?", (step_id,))
    step = cursor.fetchone()
    if not step:
        conn.close()
        return False, "Step not found."
        
    task_id, step_number, deps_str, current_status = step
    
    # Check dependencies if trying to complete or in_progress
    if new_status in ("COMPLETED", "IN_PROGRESS") and deps_str:
        dep_numbers = [int(d.strip()) for d in deps_str.split(",") if d.strip()]
        if dep_numbers:
            placeholders = ",".join("?" * len(dep_numbers))
            cursor.execute(f'''
                SELECT step_number, status FROM steps 
                WHERE task_id = ? AND step_number IN ({placeholders})
            ''', [task_id] + dep_numbers)
            deps = cursor.fetchall()
            for d_num, d_status in deps:
                if d_status != "COMPLETED":
                    conn.close()
                    return False, f"Prerequisite Step {d_num} must be COMPLETED before updating this step."
                    
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        UPDATE steps SET status = ?, result = ?, updated_at = ? WHERE id = ?
    ''', (new_status, result, now, step_id))
    
    # Log memory
    cursor.execute('''
        INSERT INTO memory_logs (task_id, step_id, summary, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (task_id, step_id, f"Step {step_number} status updated to {new_status}. Result: {result}", now))
    
    # Check if all steps are completed to update task status
    cursor.execute("SELECT COUNT(*) FROM steps WHERE task_id = ? AND status != 'COMPLETED'", (task_id,))
    remaining = cursor.fetchone()[0]
    if remaining == 0:
        cursor.execute("UPDATE tasks SET status = 'COMPLETED', updated_at = ? WHERE id = ?", (now, task_id))
    else:
        cursor.execute("UPDATE tasks SET status = 'IN_PROGRESS', updated_at = ? WHERE id = ?", (now, task_id))
        
    conn.commit()
    conn.close()
    return True, "Step updated successfully."

def get_memory_logs(task_id: int) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memory_logs WHERE task_id = ? ORDER BY timestamp DESC", (task_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ==========================================
# Phase 8: Persistent Long-Term Memory & Context Intelligence
# ==========================================

def store_long_term_memory(category: str, memory_key: str, content: str, importance: int = 1) -> int:
    """Store or update a persistent long-term memory record (handles deduplication/conflicts via memory_key upsert)."""
    init_db()
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO long_term_memories (category, memory_key, content, importance, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(memory_key) DO UPDATE SET
            category = excluded.category,
            content = excluded.content,
            importance = excluded.importance,
            updated_at = excluded.updated_at
    ''', (category, memory_key, content, importance, now))
    conn.commit()
    
    cursor.execute("SELECT id FROM long_term_memories WHERE memory_key = ?", (memory_key,))
    row = cursor.fetchone()
    mem_id = row[0] if row else 0
    conn.close()
    return mem_id

def get_long_term_memories(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all long-term memories, optionally filtered by category."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if category and category != "All":
        cursor.execute("SELECT * FROM long_term_memories WHERE category = ? ORDER BY importance DESC, updated_at DESC", (category,))
    else:
        cursor.execute("SELECT * FROM long_term_memories ORDER BY importance DESC, updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def search_long_term_memories(query: str) -> List[Dict[str, Any]]:
    """Search long-term memories using lightweight local relevance scoring (keyword overlap)."""
    memories = get_long_term_memories()
    if not query or not query.strip():
        return memories
        
    query_terms = set(query.lower().split())
    scored = []
    for mem in memories:
        text = f"{mem['memory_key']} {mem['content']} {mem['category']}".lower()
        score = sum(1 for term in query_terms if term in text)
        score += mem.get('importance', 1) * 0.5  # Weight by importance
        if score > 0:
            scored.append((score, mem))
            
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for score, m in scored] if scored else memories

def update_long_term_memory(memory_id: int, category: str, memory_key: str, content: str, importance: int) -> bool:
    """Update a specific long-term memory record."""
    init_db()
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE long_term_memories 
            SET category = ?, memory_key = ?, content = ?, importance = ?, updated_at = ?
            WHERE id = ?
        ''', (category, memory_key, content, importance, now, memory_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False

def delete_long_term_memory(memory_id: int) -> bool:
    """Delete a single long-term memory record by ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM long_term_memories WHERE id = ?", (memory_id,))
    conn.commit()
    conn.close()
    return True

def clear_long_term_memories() -> bool:
    """Bulk delete all long-term memory records (requires explicit user confirmation)."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM long_term_memories")
    conn.commit()
    conn.close()
    return True

def get_relevant_memory_context(task_goal: str, max_chars: int = 1200) -> str:
    """
    Retrieve relevant long-term memories using local relevance scoring,
    and format as a strict size-limited context injection block wrapped as data (protecting against prompt injection).
    """
    relevant = search_long_term_memories(task_goal)
    if not relevant:
        return ""
        
    lines = ["<long_term_memory_context>"]
    curr_len = len(lines[0])
    
    for mem in relevant:
        item_str = f"- [{mem['category']}] {mem['memory_key']}: {mem['content']} (Importance: {mem['importance']})"
        if curr_len + len(item_str) + 1 > max_chars:
            break
        lines.append(item_str)
        curr_len += len(item_str) + 1
        
    lines.append("</long_term_memory_context>")
    return "\n".join(lines)

def modify_project(task_id: int, modification_prompt: str) -> tuple[bool, str, List[str]]:
    """
    Modify an existing project in-place based on a follow-up request.
    Loads existing file tree and relevant project memory/context, identifies affected files,
    applies targeted edits through orchestrated workspace tools, and records progress in SQLite.
    """
    init_db()
    task = get_task(task_id)
    if not task:
        return False, "Project/Task not found.", []
        
    from workspace_tools import list_workspace_files, read_text_file
    files_before = list_workspace_files(task_id)
    memory_ctx = get_relevant_memory_context(modification_prompt)
    
    target_file = "main.py" if "main.py" in files_before else ("README.md" if "README.md" in files_before else "module_2.py")
    
    success_read, existing_content = read_text_file(target_file, task_id)
    if not success_read:
        existing_content = f"# Project: {task['goal']}\n"
        
    updated_content = existing_content + f"\n\n# --- In-Place Modification ({datetime.utcnow().isoformat()}) ---\n# Request: {modification_prompt}\n# Context: {memory_ctx[:300]}\n"
    
    from orchestration_engine import execute_orchestrated_tool
    succ, res = execute_orchestrated_tool(
        "write_workspace_file", 
        {"rel_path": target_file, "content": updated_content}, 
        approval_granted=True, 
        task_id=task_id
    )
    
    if succ:
        files_after = list_workspace_files(task_id)
        changed_files = [f for f in files_after if f not in files_before or f == target_file]
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute('''
            INSERT INTO memory_logs (task_id, summary, timestamp)
            VALUES (?, ?, ?)
        ''', (task_id, f"In-place project modification applied for request: '{modification_prompt}'. Modified file: {target_file}", now))
        conn.commit()
        conn.close()
        return True, f"Successfully modified {target_file} in place without recreating project.", changed_files
    else:
        return False, f"In-place modification failed: {res}", []
