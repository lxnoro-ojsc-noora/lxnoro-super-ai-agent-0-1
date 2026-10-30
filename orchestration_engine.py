import os
from typing import List, Dict, Any, Optional
from workspace_tools import (
    list_workspace_files, read_text_file, write_workspace_file,
    search_workspace, run_approved_command
)
import nebius_client
from agent_memory import init_db, DB_PATH
import sqlite3
from datetime import datetime

# Define Tool Registry with Schemas and Sensitivity Flags
TOOL_REGISTRY = {
    "list_workspace_files": {
        "name": "list_workspace_files",
        "description": "List all non-protected files in the workspace.",
        "parameters": {},
        "sensitive": False,
        "function": list_workspace_files
    },
    "read_text_file": {
        "name": "read_text_file",
        "description": "Read the text content of a specified workspace file.",
        "parameters": {"rel_path": str},
        "sensitive": False,
        "function": read_text_file
    },
    "search_workspace": {
        "name": "search_workspace",
        "description": "Search for keywords across workspace filenames and file contents.",
        "parameters": {"query": str},
        "sensitive": False,
        "function": search_workspace
    },
    "write_workspace_file": {
        "name": "write_workspace_file",
        "description": "Write or create a text file with content in the workspace (destructive file change).",
        "parameters": {"rel_path": str, "content": str},
        "sensitive": True,
        "function": write_workspace_file
    },
    "run_approved_command": {
        "name": "run_approved_command",
        "description": "Execute a pre-approved diagnostic command on the allowlist.",
        "parameters": {"command": str, "enabled": bool},
        "sensitive": True,
        "function": run_approved_command
    },
    "nebius_chat": {
        "name": "nebius_chat",
        "description": "Send a chat completion prompt to Nebius Token Factory (NVIDIA Nemotron).",
        "parameters": {"prompt": str},
        "sensitive": True,
        "function": lambda prompt: nebius_client.nebius_chat_completion(prompt)
    },
    "nebius_plan_generator": {
        "name": "nebius_plan_generator",
        "description": "Generate a structured implementation plan using Nebius Token Factory (NVIDIA Nemotron).",
        "parameters": {"prompt": str},
        "sensitive": True,
        "function": lambda prompt: nebius_client.nebius_chat_completion(prompt)
    }
}

def get_registered_tools() -> List[Dict[str, Any]]:
    """Return list of all registered tools with their schemas and sensitivity."""
    tools = []
    for t_name, t_meta in TOOL_REGISTRY.items():
        param_desc = {p_name: p_type.__name__ for p_name, p_type in t_meta["parameters"].items()}
        tools.append({
            "name": t_meta["name"],
            "description": t_meta["description"],
            "parameters": param_desc,
            "sensitive": t_meta["sensitive"]
        })
    return tools

def select_relevant_tools(task_goal: str) -> List[Dict[str, Any]]:
    """
    Select relevant registered tools based on the user's task goal and tool descriptions.
    Uses keyword matching and semantic heuristics.
    """
    if not task_goal:
        return get_registered_tools()
        
    goal_lower = task_goal.lower()
    selected = []
    
    # Always include basic inspectors
    always_include = {"list_workspace_files", "search_workspace"}
    
    for t_name, t_meta in TOOL_REGISTRY.items():
        if t_name in always_include:
            selected.append(t_meta)
            continue
            
        match = False
        if "file" in goal_lower and ("read" in goal_lower or "inspect" in goal_lower) and t_name == "read_text_file":
            match = True
        elif ("write" in goal_lower or "create" in goal_lower or "update" in goal_lower or "fix" in goal_lower) and t_name == "write_workspace_file":
            match = True
        elif ("command" in goal_lower or "test" in goal_lower or "compile" in goal_lower or "run" in goal_lower) and t_name == "run_approved_command":
            match = True
        elif ("ai" in goal_lower or "chat" in goal_lower or "nemotron" in goal_lower or "nebius" in goal_lower or "llm" in goal_lower) and t_name == "nebius_chat":
            match = True
            
        if match and t_meta not in selected:
            selected.append(t_meta)
            
    # If no specific match, return all tools
    if not selected:
        return list(TOOL_REGISTRY.values())
        
    return [{
        "name": t["name"],
        "description": t["description"],
        "parameters": {p_name: p_type.__name__ for p_name, p_type in t["parameters"].items()},
        "sensitive": t["sensitive"]
    } for t in selected]

def validate_tool_call(tool_name: str, arguments: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate every tool name and argument against its registered schema before execution.
    """
    if not tool_name or tool_name not in TOOL_REGISTRY:
        return False, f"Invalid or unregistered tool name: '{tool_name}'."
        
    tool_meta = TOOL_REGISTRY[tool_name]
    expected_params = tool_meta["parameters"]
    
    if not isinstance(arguments, dict):
        return False, "Arguments must be a dictionary."
        
    # Check for missing required parameters
    for param_name, param_type in expected_params.items():
        if param_name not in arguments:
            return False, f"Missing required parameter '{param_name}' for tool '{tool_name}'."
        val = arguments[param_name]
        if not isinstance(val, param_type):
            return False, f"Parameter '{param_name}' expected type {param_type.__name__}, got {type(val).__name__}."
            
    # Check for unexpected extra arguments
    for arg_name in arguments:
        if arg_name not in expected_params:
            return False, f"Unexpected argument '{arg_name}' for tool '{tool_name}'."
            
    return True, "Tool call schema validation passed."

def requires_approval(tool_name: str) -> bool:
    """Determine if a tool requires explicit user approval due to sensitivity."""
    if tool_name in TOOL_REGISTRY:
        return TOOL_REGISTRY[tool_name]["sensitive"]
    return True

def execute_orchestrated_tool(
    tool_name: str, 
    arguments: Dict[str, Any], 
    approval_granted: bool = False, 
    task_id: Optional[int] = None
) -> tuple[bool, Any]:
    """
    Execute a validated tool with approval gating, security enforcement, and error handling.
    """
    # 1. Validate schema
    valid, val_msg = validate_tool_call(tool_name, arguments)
    if not valid:
        return False, f"Schema Validation Error: {val_msg}"
        
    # 2. Check approval gates for sensitive operations
    if requires_approval(tool_name) and not approval_granted:
        return False, f"Explicit user approval required for sensitive tool '{tool_name}' (destructive file changes, shell command, or network action)."
        
    tool_meta = TOOL_REGISTRY[tool_name]
    func = tool_meta["function"]
    
    try:
        # Execute underlying function
        if tool_name == "list_workspace_files":
            res = func(task_id)
            return True, res
        elif tool_name == "read_text_file":
            success, content = func(arguments["rel_path"], task_id)
            return success, content
        elif tool_name == "search_workspace":
            res = func(arguments["query"], task_id)
            return True, res
        elif tool_name == "write_workspace_file":
            success, msg = func(arguments["rel_path"], arguments["content"], task_id)
            return success, msg
        elif tool_name == "run_approved_command":
            success, output = func(arguments["command"], arguments.get(arguments.get("enabled", False), False), task_id)
            return success, output
        elif tool_name == "nebius_chat":
            # If prompt provided
            res = func(arguments["prompt"])
            if isinstance(res, dict):
                return res.get("success", False), res.get("content", res.get("error", "Unknown Nebius response"))
            return True, res
        else:
            return False, f"Executor not implemented for tool '{tool_name}'."
    except Exception as e:
        return False, f"Tool execution exception: {str(e)}"
