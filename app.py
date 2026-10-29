import os
import streamlit as st
from dotenv import load_dotenv
from agent_memory import (
    init_db, create_task, get_tasks, get_task, 
    get_steps, update_step_status, get_memory_logs,
    store_long_term_memory, get_long_term_memories,
    search_long_term_memories, update_long_term_memory,
    delete_long_term_memory, clear_long_term_memories,
    get_relevant_memory_context
)
from workspace_tools import (
    list_workspace_files, read_text_file, write_workspace_file,
    search_workspace, run_approved_command, APPROVED_COMMANDS
)
from execution_engine import (
    get_next_eligible_step, execute_step, recover_interrupted_steps
)
from delivery_utils import get_git_status_info, generate_project_zip
from nebius_client import nebius_chat_completion, get_nebius_api_key, get_nebius_model, NEBIUS_BASE_URL
from orchestration_engine import (
    get_registered_tools, select_relevant_tools, validate_tool_call,
    requires_approval, execute_orchestrated_tool
)

load_dotenv()
init_db()

st.set_page_config(
    page_title="LXNORO Super AI Agent 0-1",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Cyberpunk / Video-Game Inspired Tactical Theme CSS
st.markdown("""
<style>
/* Global Theme: Pure Black & Very Dark Purple Gamer Aesthetic */
.stApp {
    background-color: #0b0b0c;
    color: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #050507;
    border-right: 1px solid #1a0f24;
}
[data-testid="stHeader"] {
    background-color: rgba(11, 11, 12, 0.9);
}
/* Cards & Containers */
div.stMarkdown, div.stExpander, div.stForm {
    background-color: #121217;
    border: 1px solid #1f132e;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}
/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #2d1338 0%, #150922 100%);
    color: #ffffff;
    border: 1px solid #4a1d63;
    border-radius: 6px;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #4a1d63 0%, #2d1338 100%);
    border-color: #8a2be2;
    box-shadow: 0 0 12px rgba(138, 43, 226, 0.4);
}
/* Inputs & Textareas */
input, textarea, select {
    background-color: #0f0f14 !important;
    color: #ffffff !important;
    border: 1px solid #221233 !important;
    border-radius: 6px !important;
}
/* Headers & Titles */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.brand-container {
    padding: 0.5rem 0 1rem 0;
    border-bottom: 1px solid #1f132e;
    margin-bottom: 1rem;
}
.brand-title {
    font-size: 1.15rem;
    font-weight: 900;
    color: #bd00ff;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 0;
}
.brand-subtitle {
    font-size: 0.75rem;
    color: #8c8c9e;
    margin-top: 0.2rem;
    letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar Branding & Navigation
with st.sidebar:
    st.markdown("""
        <div class="brand-container">
            <div class="brand-title">LXNORO SUPER AI AGENT</div>
            <div class="brand-subtitle">Tactical Command Center • v0.1</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.header("Agent Configuration")
    api_key_input = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""), key="sidebar_gemini_key")

    st.markdown("---")
    st.subheader("Nebius Token Factory")
    nebius_key_status = "🟢 Configured" if get_nebius_api_key() else "🔴 Missing"
    st.markdown(f"- **API Key:** {nebius_key_status}")
    st.markdown(f"- **Model:** `{get_nebius_model()}`")

    st.markdown("---")
    st.subheader("Navigation Menu")
    nav_selection = st.radio(
        "Select Operation Mode",
        [
            "🚀 Dashboard & Roadmap (Phase 1)",
            "➕ Task Creation & Plan (Phase 2)",
            "🧠 Task Memory & Execution (Phase 4)",
            "🛠️ Safe Workspace Tools (Phase 3)",
            "📦 Dual Delivery Center (Phase 5)",
            "⚡ Nebius & Nemotron (Phase 6)",
            "🎯 Tool Orchestration (Phase 7)",
            "🧠 Persistent Long-Term Memory (Phase 8)"
        ],
        key="main_navigation_radio"
    )

# Main Header Banner
st.markdown("""
    <div style="padding: 0.5rem 0 1rem 0;">
        <h1 style="margin-bottom: 0px; font-size: 2rem;">🤖 LXNORO SUPER AI AGENT</h1>
        <p style="color: #a0a0b0; font-size: 0.95rem; margin-top: 4px;">Autonomous Multi-Modal Engineering & Orchestration Engine — Streamlit Community Cloud Edition</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state for active task
if "active_task_id" not in st.session_state:
    st.session_state.active_task_id = None

# Route based on navigation selection
if "Dashboard" in nav_selection:
    st.subheader("🚀 Operational Dashboard & Roadmap")
    st.info("System operational. Phase 1 through Phase 8 fully integrated with persistent SQLite storage, advanced tool orchestration, Nebius Token Factory API, and long-term memory curation.")
    
    tasks = get_tasks()
    st.markdown(f"### Active Tasks ({len(tasks)})")
    if tasks:
        for t in tasks:
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                st.markdown(f"**Task #{t['id']}**: {t['goal']}")
            with col_b:
                st.markdown(f"Status: `{t['status']}`")
            with col_c:
                if st.button(f"Inspect #{t['id']}", key=f"dash_inspect_{t['id']}"):
                    st.session_state.active_task_id = t['id']
                    st.success(f"Loaded Task #{t['id']}. Switch to 'Task Memory & Execution' mode.")
    else:
        st.warning("No tasks created yet. Use 'Task Creation & Plan' to initialize a new goal.")

    st.markdown("---")
    st.markdown("### 🗺️ Phased Implementation Roadmap")
    roadmap_data = [
        {"Phase": "Phase 1", "Focus": "Foundation, Streamlit App, Dependency Manifest, .gitignore, README", "Status": "Completed ✅"},
        {"Phase": "Phase 2", "Focus": "SQLite Persistent Task Memory & Dynamic 1–50 Step Plan Engine", "Status": "Completed ✅"},
        {"Phase": "Phase 3", "Focus": "Safe Workspace Tools (Inspection, File Editor, Search, Audit, Runner)", "Status": "Completed ✅"},
        {"Phase": "Phase 4", "Focus": "Execution & Recovery Engine (Resumable Steps, Retries, Validation)", "Status": "Completed ✅"},
        {"Phase": "Phase 5", "Focus": "Dual Delivery Center (GitHub Delivery & Secure ZIP Archive Export)", "Status": "Completed ✅"},
        {"Phase": "Phase 6", "Focus": "Nebius Token Factory + NVIDIA Nemotron Integration (OpenAI-compatible API)", "Status": "Completed ✅"},
        {"Phase": "Phase 7", "Focus": "Autonomous Tool Orchestration (Registry, Schema Validation, Approval Gates)", "Status": "Completed ✅"},
        {"Phase": "Phase 8", "Focus": "Persistent Long-Term Memory & Context Intelligence (Curation, Relevance, Injection)", "Status": "Completed ✅"}
    ]
    st.table(roadmap_data)

elif "Task Creation" in nav_selection:
    st.subheader("➕ Create a New Task & Dynamic Plan (1–50 Steps)")
    st.markdown("Define a complex engineering goal and automatically generate a structured, dependency-aware multi-step execution plan.")
    
    with st.form("task_form_unique"):
        goal_input = st.text_area("Task Goal / Objective", placeholder="e.g., Build and test project architecture with full security audit", key="new_task_goal_input")
        step_count_input = st.slider("Plan Step Count", min_value=1, max_value=50, value=5, key="new_task_step_slider")
        submit_task = st.form_submit_button("Generate Plan & Initialize Task")
        
        if submit_task:
            if goal_input.strip():
                new_id = create_task(goal_input.strip(), step_count_input)
                st.session_state.active_task_id = new_id
                st.success(f"Task #{new_id} created successfully with {step_count_input} steps!")
                st.rerun()
            else:
                st.error("Please provide a valid task goal.")

elif "Task Memory & Execution" in nav_selection:
    st.subheader("🧠 Persistent Task Memory & Execution Engine")
    st.markdown("Monitor execution progress, manage dependencies, execute retriable steps, and inspect operational logs.")
    
    tasks = get_tasks()
    if not tasks:
        st.warning("No tasks available. Please create a task first using 'Task Creation & Plan'.")
    else:
        task_options = {t['id']: f"Task #{t['id']}: {t['goal']} ({t['status']})" for t in tasks}
        current_selection = st.session_state.active_task_id
        selected_task_id = st.selectbox(
            "Select Active Task", 
            options=list(task_options.keys()), 
            format_func=lambda x: task_options[x],
            index=list(task_options.keys()).index(current_selection) if current_selection in task_options else 0,
            key="exec_task_selector"
        )
        st.session_state.active_task_id = selected_task_id
        
        # Run startup recovery for this task
        recover_interrupted_steps(selected_task_id)
        
        task = get_task(selected_task_id)
        steps = get_steps(selected_task_id)
        logs = get_memory_logs(selected_task_id)
        
        if task:
            st.markdown(f"**Goal:** {task['goal']}")
            st.markdown(f"**Status:** `{task['status']}` | **Total Steps:** {task['total_steps']}")
            
            # Execution Control Panel
            st.markdown("### ⚡ Execution Control Panel")
            next_step = get_next_eligible_step(selected_task_id)
            if next_step:
                st.info(f"**Next Eligible Step:** Step {next_step['step_number']} — {next_step['title']} (Status: `{next_step['status']}` | Retries: {next_step['retry_count']}/3)")
            else:
                st.success("All steps completed or no eligible pending steps remaining!")
                
            enable_runner_exec = st.checkbox("Enable Command Runner for Execution", value=False, key="exec_runner_checkbox")

            if st.button("▶️ Run Next Eligible Step", key="run_next_step_btn"):
                if next_step:
                    success, exec_msg = execute_step(next_step['id'], command_runner_enabled=enable_runner_exec)
                    if success:
                        st.success(f"Step {next_step['step_number']} executed successfully: {exec_msg}")
                        st.rerun()
                    else:
                        st.error(f"Step execution encountered an error: {exec_msg}")
                        st.rerun()
                else:
                    st.warning("No eligible step available to execute.")
            
            st.markdown("### 📋 Plan Steps & Status")
            for step in steps:
                with st.expander(f"Step {step['step_number']}: {step['title']} [{step['status']}] (Retries: {step['retry_count']})"):
                    st.markdown(f"**Objective:** {step['objective']}")
                    st.markdown(f"**Dependencies:** Step(s) `{step['dependencies']}`" if step['dependencies'] else "**Dependencies:** None")
                    st.markdown(f"**Current Result:** {step['result'] or 'No result recorded yet.'}")
                    
                    col_step1, col_step2 = st.columns(2)
                    with col_step1:
                        if st.button(f"Execute Step #{step['step_number']}", key=f"exec_single_{step['id']}"):
                            success, msg = execute_step(step['id'], command_runner_enabled=enable_runner_exec)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_step2:
                        if st.button(f"Reset to PENDING", key=f"reset_step_{step['id']}"):
                            update_step_status(step['id'], "PENDING", "Reset manually by user.")
                            st.success("Step reset to PENDING.")
                            st.rerun()
            
            st.markdown("### 🧠 Operational Feedback Memory Log")
            if logs:
                for log in logs:
                    st.text(f"[{log['timestamp']}] {log['summary']}")
            else:
                st.info("No memory logs recorded yet.")

elif "Safe Workspace Tools" in nav_selection:
    st.subheader("🛠️ Safe Workspace Tools & Audited Operations")
    st.markdown("Inspect, read, search, edit files, or run pre-approved diagnostic commands under strict sandbox safety constraints.")
    
    tool_sub1, tool_sub2, tool_sub3, tool_sub4 = st.tabs(["📂 File Inspection", "✏️ File Editor", "🔍 Search", "⚡ Command Runner"])
    
    with tool_sub1:
        st.markdown("#### Workspace Files")
        files = list_workspace_files(st.session_state.active_task_id)
        selected_file = st.selectbox("Select File to Read", options=files if files else ["No files found"], key="inspect_file_select")
        
        if selected_file and selected_file != "No files found":
            if st.button("Read File Content", key="read_file_btn"):
                success, content = read_text_file(selected_file, st.session_state.active_task_id)
                if success:
                    st.text_area("File Content (Read-Only)", value=content, height=300, key="read_file_textarea")
                else:
                    st.error(content)
                    
    with tool_sub2:
        st.markdown("#### Safe File Editor & Creator")
        edit_path = st.text_input("Relative File Path", placeholder="e.g., notes.txt or src/component.py", key="edit_file_path")
        edit_content = st.text_area("File Content", placeholder="Enter full file text content here...", height=250, key="edit_file_content")
        
        if st.button("Save / Write File", key="save_file_btn"):
            if edit_path.strip():
                success, msg = write_workspace_file(edit_path.strip(), edit_content, st.session_state.active_task_id)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("Please provide a valid relative file path.")
                
    with tool_sub3:
        st.markdown("#### Workspace Search")
        query = st.text_input("Search Query (Filename or content keyword)", placeholder="Enter keyword...", key="search_query_input")
        if st.button("Search Workspace", key="search_workspace_btn"):
            if query.strip():
                matches = search_workspace(query.strip(), st.session_state.active_task_id)
                if matches:
                    st.success(f"Found {len(matches)} match(es):")
                    for m in matches:
                        st.markdown(f"- `{m}`")
                else:
                    st.info("No matches found.")
            else:
                st.warning("Please enter a search query.")
                
    with tool_sub4:
        st.markdown("#### Strict Command Runner")
        st.warning("⚠️ **Streamlit Community Cloud Limitation**: Command execution runs locally in the container sandbox and is disabled by default. Only pre-approved diagnostic commands on the strict allowlist are permitted.")
        
        enable_runner = st.checkbox("Enable Command Runner (Disabled by default)", key="runner_tab_tool4")
        approved_list = list(APPROVED_COMMANDS)
        selected_cmd = st.selectbox("Select Approved Diagnostic Command", options=approved_list, key="approved_cmd_select")
        
        if st.button("Execute Command", key="execute_cmd_btn"):
            success, output = run_approved_command(selected_cmd, enabled=enable_runner, task_id=st.session_state.active_task_id)
            if success:
                st.success("Command executed successfully:")
                st.code(output, language="text")
            else:
                st.error(output)

elif "Dual Delivery Center" in nav_selection:
    st.subheader("📦 Dual Delivery Center")
    st.markdown("Export or prepare your project for distribution via GitHub (Option A) or direct ZIP archive (Option B). Streamlit Community Cloud filesystems are ephemeral; download a ZIP archive as your persistent portable copy.")
    
    del_sub1, del_sub2 = st.tabs(["🐙 Option A — GitHub Delivery", "🗂️ Option B — ZIP Archive Delivery"])
    
    with del_sub1:
        st.markdown("#### Option A — GitHub Repository Delivery")
        st.markdown("Review your local repository status and use the exact commands below to commit and push your project to GitHub.")
        
        git_info = get_git_status_info()
        st.markdown(f"- **Git Repository Detected:** `{'Yes ✅' if git_info['is_git_repo'] else 'No ❌'}`")
        st.markdown(f"- **Current Branch:** `{git_info['branch']}`")
        st.markdown(f"- **Remote URL:** `{git_info['remote']}`")
        st.markdown(f"- **Working Tree Uncommitted Changes:** `{'Yes (Changes present) ⚠️' if git_info['uncommitted'] else 'Clean 🟢'}`")
        
        st.markdown("##### Working Tree Status Output")
        st.code(git_info['status_output'], language="text")
        
        st.info("ℹ️ **Safety Guarantee**: Remote history, commits, and pushes are *never* executed automatically by this agent. You must run git commands locally.")
        
        st.markdown("##### Exact Local Git Workflow Commands")
        st.code("""
# 1. Initialize repository (if not already initialized)
git init

# 2. Check status and review changes safely
git status
git diff HEAD

# 3. Stage selected files explicitly (avoiding secrets or local data)
git add app.py agent_memory.py workspace_tools.py execution_engine.py delivery_utils.py nebius_client.py orchestration_engine.py requirements.txt .gitignore .env.example README.md test_*.py

# 4. Commit changes with a descriptive message
git commit -m "Implement Phase 8 & UI Polish"

# 5. Connect remote repository and push (requires user authentication)
# git remote add origin <your-github-repository-url>
# git push -u origin main
        """, language="bash")
        
    with del_sub2:
        st.markdown("#### Option B — Secure ZIP Archive Delivery")
        st.markdown("Generate and download a clean production ZIP archive containing all source code, manifests, and documentation while strictly excluding secrets (`.env`), database files (`data/`), caches, and virtual environments.")
        
        if st.button("Prepare Clean Project ZIP", key="prepare_zip_btn"):
            zip_data = generate_project_zip()
            st.session_state.zip_ready = True
            st.session_state.zip_bytes = zip_data
            st.success("ZIP archive prepared successfully!")
            
        if st.session_state.get("zip_ready", False):
            st.download_button(
                label="📥 Download LXNORO-Super-AI-Agent-0-1.zip",
                data=st.session_state.zip_bytes,
                file_name="LXNORO-Super-AI-Agent-0-1.zip",
                mime="application/zip",
                key="download_zip_btn"
            )
            st.markdown("✅ **ZIP Generated Successfully** (Distinct from GitHub push status).")
        else:
            st.info("Click 'Prepare Clean Project ZIP' above to generate your download package.")

elif "Nebius & Nemotron" in nav_selection:
    st.subheader("⚡ Nebius Token Factory + NVIDIA Nemotron Integration")
    st.markdown("Interact with NVIDIA Nemotron via the OpenAI-compatible Nebius Token Factory API (`https://api.tokenfactory.nebius.com/v1/`).")
    
    st.markdown("##### Configuration Status")
    col_nc1, col_nc2 = st.columns(2)
    with col_nc1:
        st.markdown(f"- **Base URL:** `{NEBIUS_BASE_URL}`")
        st.markdown(f"- **Configured Model (`NEBIUS_MODEL`):** `{get_nebius_model()}`")
    with col_nc2:
        api_key_present = bool(get_nebius_api_key())
        st.markdown(f"- **API Key Status (`NEBIUS_API_KEY`):** `{'Configured 🟢' if api_key_present else 'Missing 🔴'}`")
        if not api_key_present:
            st.warning("⚠️ `NEBIUS_API_KEY` is not set in environment. Set it in `.env` or environment variables to enable live requests.")
            
    st.markdown("---")
    st.markdown("##### Nebius Chat Completion Playground")
    st.info("ℹ️ Note: Live Nebius connectivity remains unverified unless tested with valid credentials. You can test error handling or mocked execution safely.")
    
    user_prompt = st.text_area("Prompt for NVIDIA Nemotron", placeholder="e.g., Explain the architecture of LXNORO Super AI Agent in 3 sentences.", value="Hello, NVIDIA Nemotron!", key="nebius_prompt_textarea")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        send_nebius = st.button("Send to Nebius API", key="send_nebius_btn")
        
    if send_nebius:
        if not user_prompt.strip():
            st.error("Please enter a prompt.")
        else:
            with st.spinner("Communicating with Nebius Token Factory..."):
                res = nebius_chat_completion(user_prompt.strip())
                if res["success"]:
                    st.success("Response received successfully from Nebius API!")
                    st.markdown("**Assistant Response:**")
                    st.markdown(res["content"])
                    with st.expander("Inspect Raw JSON Response"):
                        st.json(res["raw"])
                else:
                    st.error(f"Nebius API Error: {res['error']}")

elif "Tool Orchestration" in nav_selection:
    st.subheader("🎯 Phase 7: Autonomous Tool Orchestration & Execution Engine")
    st.markdown("Orchestrate registered workspace and AI tools with schema validation, sensitivity approval gates, and dependency-aware execution.")
    
    orch_sub1, orch_sub2, orch_sub3 = st.tabs(["📋 Tool Registry & Catalog", "🔍 Task Tool Selector", "⚡ Orchestrated Tool Executor"])
    
    with orch_sub1:
        st.markdown("#### Registered Tools & Schemas")
        tools = get_registered_tools()
        for t in tools:
            with st.expander(f"`{t['name']}` — {'Sensitive ⚠️ (Approval Required)' if t['sensitive'] else 'Safe 🟢 (Read-Only)'}"):
                st.markdown(f"**Description:** {t['description']}")
                st.markdown(f"**Parameters:** `{t['parameters']}`")
                st.markdown(f"**Sensitivity:** `{'Sensitive (Requires explicit user approval)' if t['sensitive'] else 'Safe'}`")
                
    with orch_sub2:
        st.markdown("#### Intelligent Tool Selector")
        st.markdown("Enter a task description or goal to see which tools the agent selects based on capability matching.")
        goal_query = st.text_input("Task Goal / Objective", placeholder="e.g., Read configuration file and ask NVIDIA Nemotron to summarize it", key="orch_goal_query")
        if st.button("Select Relevant Tools", key="select_tools_btn"):
            if goal_query.strip():
                selected_tools = select_relevant_tools(goal_query.strip())
                st.success(f"Selected {len(selected_tools)} relevant tool(s):")
                for st_tool in selected_tools:
                    st.markdown(f"- **`{st_tool['name']}`**: {st_tool['description']}")
            else:
                st.warning("Please enter a task goal.")
                
    with orch_sub3:
        st.markdown("#### Orchestrated Tool Execution Playground")
        st.markdown("Execute any registered tool with parameter validation and mandatory approval gates for sensitive actions.")
        
        reg_tools = get_registered_tools()
        tool_names = [t["name"] for t in reg_tools]
        chosen_tool = st.selectbox("Select Tool to Execute", options=tool_names, key="orch_tool_selectbox")
        
        tool_meta = {t["name"]: t for t in reg_tools}[chosen_tool]
        st.markdown(f"**Description:** {tool_meta['description']}")
        st.markdown(f"**Requires Approval:** `{'Yes ⚠️' if tool_meta['sensitive'] else 'No 🟢'}`")
        
        args_dict = {}
        if chosen_tool == "list_workspace_files":
            pass
        elif chosen_tool == "read_text_file":
            args_dict["rel_path"] = st.text_input("Relative File Path (e.g. README.md)", value="README.md", key="orch_arg_read_path")
        elif chosen_tool == "search_workspace":
            args_dict["query"] = st.text_input("Search Keyword / Query", value="agent", key="orch_arg_search_query")
        elif chosen_tool == "write_workspace_file":
            args_dict["rel_path"] = st.text_input("Relative File Path", value="notes.txt", key="orch_arg_write_path")
            args_dict["content"] = st.text_area("File Content", value="Autonomous orchestration note.", key="orch_arg_write_content")
        elif chosen_tool == "run_approved_command":
            args_dict["command"] = st.selectbox("Approved Diagnostic Command", options=["git status", "git diff HEAD"], key="orch_arg_cmd_select")
            args_dict["enabled"] = st.checkbox("Enable Command Runner", value=False, key="orch_arg_cmd_enabled")
        elif chosen_tool == "nebius_chat":
            args_dict["prompt"] = st.text_area("Nebius / Nemotron Prompt", value="Hello from LXNORO orchestration engine!", key="orch_arg_nebius_prompt")

        approval_checkbox = st.checkbox(
            "Grant Explicit User Approval for Sensitive Operation", 
            value=False,
            help="Mandatory for tools performing destructive changes, executing shell commands, or calling external APIs.",
            key="orch_approval_checkbox"
        )
        
        if st.button("Execute Orchestrated Tool Call", key="execute_orch_tool_btn"):
            with st.spinner("Validating schema and executing tool..."):
                success, result = execute_orchestrated_tool(chosen_tool, args_dict, approval_granted=approval_checkbox, task_id=st.session_state.active_task_id)
                if success:
                    st.success("Tool execution completed successfully!")
                    if isinstance(result, (list, dict)):
                        st.json(result)
                    else:
                        st.text_area("Tool Output", value=str(result), height=250, key="orch_tool_result_textarea")
                else:
                    st.error(f"Tool Execution Failed: {result}")

elif "Persistent Long-Term Memory" in nav_selection:
    st.subheader("🧠 Phase 8: Persistent Long-Term Memory & Context Intelligence")
    st.markdown("Curate, search, update, and inspect long-term memories across categories (Architecture, Security, Preferences, Lessons Learned) with automated relevance scoring and deduplication.")
    
    ltm_sub1, ltm_sub2, ltm_sub3 = st.tabs(["➕ Store & Manage Memory", "🔍 Semantic Search & Context", "📋 Full Memory Catalog"])
    
    with ltm_sub1:
        st.markdown("#### Store New Long-Term Memory")
        with st.form("store_memory_form"):
            mem_category = st.selectbox(
                "Memory Category", 
                options=["Architecture", "Security", "Workflow", "Preferences", "Lessons Learned"],
                key="store_mem_category"
            )
            mem_content = st.text_area(
                "Memory Content / Insight", 
                placeholder="e.g., Always use explicit error handling when invoking external APIs.",
                key="store_mem_content"
            )
            mem_relevance = st.slider(
                "Relevance Score (1-10)", 
                min_value=1, max_value=10, value=8,
                key="store_mem_relevance"
            )
            submit_mem = st.form_submit_button("Store Long-Term Memory")
            
            if submit_mem:
                if mem_content.strip():
                    mid = store_long_term_memory(mem_category, mem_content.strip(), mem_relevance)
                    st.success(f"Long-term memory stored successfully (ID: #{mid})!")
                    st.rerun()
                else:
                    st.error("Please enter memory content.")

    with ltm_sub2:
        st.markdown("#### Search & Context Retrieval")
        search_kw = st.text_input("Search Keyword", placeholder="e.g., security, architecture...", key="ltm_search_kw")
        if st.button("Search Memories", key="ltm_search_btn"):
            if search_kw.strip():
                matches = search_long_term_memories(search_kw.strip())
                if matches:
                    st.success(f"Found {len(matches)} matching memory/memories:")
                    for m in matches:
                        st.markdown(f"- **[#{m['id']}] ({m['category']})** (Score: {m['relevance_score']}): {m['content']}")
                else:
                    st.info("No matching memories found.")
            else:
                st.warning("Please enter a search keyword.")

        st.markdown("---")
        st.markdown("#### Relevant Context Injector Simulator")
        ctx_query = st.text_input("Simulate Agent Task / Query", placeholder="e.g., How do we handle security and API integration?", key="ltm_ctx_query")
        if st.button("Generate Relevant Context Prompt", key="ltm_ctx_btn"):
            if ctx_query.strip():
                context_block = get_relevant_memory_context(ctx_query.strip())
                st.success("Generated Context Block for Agent Prompt Injection:")
                st.code(context_block, language="markdown")
            else:
                st.warning("Please enter a query.")

    with ltm_sub3:
        st.markdown("#### Complete Long-Term Memory Catalog")
        memories = get_long_term_memories()
        if memories:
            st.markdown(f"Total stored memories: **{len(memories)}**")
            for m in memories:
                with st.expander(f"[#{m['id']}] {m['category']} — Score: {m['relevance_score']} (Updated: {m['updated_at']})"):
                    st.markdown(f"**Content:** {m['content']}")
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        if st.button(f"Delete Memory #{m['id']}", key=f"del_mem_{m['id']}"):
                            delete_long_term_memory(m['id'])
                            st.success(f"Memory #{m['id']} deleted.")
                            st.rerun()
                    with col_m2:
                        pass
            
            if st.button("⚠️ Clear All Long-Term Memories", key="clear_all_mem_btn"):
                clear_long_term_memories()
                st.warning("All long-term memories cleared.")
                st.rerun()
        else:
            st.info("No long-term memories stored yet.")
