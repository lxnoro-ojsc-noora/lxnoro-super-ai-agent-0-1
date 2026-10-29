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
    
    conn.commit()
    conn.close()

def create_task(goal: str, step_count: int) -> int:
    init_db()
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tasks (goal, total_steps, status, created_at, updated_at)
        VALUES (?, ?, 'ACTIVE', ?, ?)
    ''', (goal, step_count, now, now))
    task_id = cursor.lastrowid
    
    # Generate deterministic plan steps
    for i in range(1, step_count + 1):
        if i == 1:
            deps = ""
            title = f"Step 1: Initialize & Research"
            objective = f"Initialize workspace state and research requirements for: {goal}"
        elif i == step_count:
            deps = str(i - 1)
            title = f"Step {i}: Final Validation & Delivery"
            objective = f"Perform final verification and packaging for: {goal}"
        else:
            deps = str(i - 1)
            title = f"Step {i}: Core Processing & Implementation"
            objective = f"Execute core logic component {i} for: {goal}"
            
        cursor.execute('''
            INSERT INTO steps (task_id, step_number, title, objective, dependencies, status, result, updated_at)
            VALUES (?, ?, ?, ?, ?, 'PENDING', '', ?)
        ''', (task_id, i, title, objective, deps, now))
        
    # Log creation
    cursor.execute('''
        INSERT INTO memory_logs (task_id, summary, timestamp)
        VALUES (?, ?, ?)
    ''', (task_id, f"Task created with goal: '{goal}' and {step_count} steps.", now))
    
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
