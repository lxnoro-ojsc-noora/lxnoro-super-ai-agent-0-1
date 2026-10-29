import os
import streamlit as st
from dotenv import load_dotenv
from agent_memory import (
    init_db, create_task, get_tasks, get_task, 
    get_steps, update_step_status, get_memory_logs
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

st.title("🤖 LXNORO Super AI Agent 0-1")
st.markdown("### Streamlit Community Cloud Edition — Phase 7: Autonomous Tool Orchestration")

st.sidebar.header("Agent Configuration")
api_key_input = st.sidebar.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))

st.sidebar.markdown("---")
st.sidebar.subheader("Nebius Token Factory")
nebius_key_status = "🟢 Configured" if get_nebius_api_key() else "🔴 Missing"
st.sidebar.markdown(f"- **API Key:** {nebius_key_status}")
st.sidebar.markdown(f"- **Model:** `{get_nebius_model()}`")

st.sidebar.markdown("---")
st.sidebar.subheader("Project Delivery Options")
st.sidebar.markdown("- **Option A:** GitHub Delivery")
st.sidebar.markdown("- **Option B:** ZIP Archive Delivery")

# Initialize session state for active task
if "active_task_id" not in st.session_state:
    st.session_state.active_task_id = None

# Main interface tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🚀 Dashboard & Roadmap", 
    "➕ Create Task & Plan", 
    "🧠 Task Memory & Steps", 
    "🛠️ Safe Workspace Tools", 
    "📦 Dual Delivery Center",
    "⚡ Nebius & Nemotron",
    "🎯 Tool Orchestration"
])

with tab1:
    st.subheader("Welcome to LXNORO Super AI Agent 0-1")
    st.info("Phase 7 active: Autonomous Tool Orchestration operational (Registry, schema validation, approval gates, and dynamic tool execution).")
    
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
                if st.button(f"Inspect Task #{t['id']}", key=f"inspect_{t['id']}"):
                    st.session_state.active_task_id = t['id']
                    st.success(f"Loaded Task #{t['id']}. Go to 'Task Memory & Steps' tab.")
    else:
        st.warning("No tasks created yet. Use 'Create Task & Plan' to start.")

    st.markdown("---")
    st.markdown("### 🗺️ Phased Implementation Roadmap")
    roadmap_data = [
        {"Phase": "Phase 1", "Focus": "Foundation, Streamlit App, Dependency Manifest, .gitignore, README", "Status": "Completed ✅"},
        {"Phase": "Phase 2", "Focus": "SQLite Persistent Task Memory & Dynamic 1–50 Step Plan Engine", "Status": "Completed ✅"},
        {"Phase": "Phase 3", "Focus": "Safe Workspace Tools (Inspection, File Editor, Search, Audit, Runner)", "Status": "Completed ✅"},
        {"Phase": "Phase 4", "Focus": "Execution & Recovery Engine (Resumable Steps, Retries, Validation)", "Status": "Completed ✅"},
        {"Phase": "Phase 5", "Focus": "Dual Delivery Center (GitHub Delivery & Secure ZIP Archive Export)", "Status": "Completed ✅"},
        {"Phase": "Phase 6", "Focus": "Nebius Token Factory + NVIDIA Nemotron Integration (OpenAI-compatible API)", "Status": "Completed ✅"},
        {"Phase": "Phase 7 (Current)", "Focus": "Autonomous Tool Orchestration (Registry, Schema Validation, Approval Gates)", "Status": "Completed ✅"}
    ]
    st.table(roadmap_data)

with tab2:
    st.subheader("Create a New Task & Dynamic Plan (1–50 Steps)")
    with st.form("task_form"):
        goal_input = st.text_area("Task Goal / Objective", placeholder="e.g., Prepare complete project delivery package")
        step_count_input = st.slider("Plan Step Count", min_value=1, max_value=50, value=5)
        submit_task = st.form_submit_button("Generate Plan & Initialize Task")
        
        if submit_task:
            if goal_input.strip():
                new_id = create_task(goal_input.strip(), step_count_input)
                st.session_state.active_task_id = new_id
                st.success(f"Task #{new_id} created successfully with {step_count_input} steps!")
                st.rerun()
            else:
                st.error("Please provide a valid task goal.")

with tab3:
    st.subheader("Persistent Task Memory & Execution Engine")
    
    tasks = get_tasks()
    if not tasks:
        st.warning("No tasks available. Please create a task first.")
    else:
        task_options = {t['id']: f"Task #{t['id']}: {t['goal']} ({t['status']})" for t in tasks}
        current_selection = st.session_state.active_task_id
        selected_task_id = st.selectbox(
            "Select Task", 
            options=list(task_options.keys()), 
            format_func=lambda x: task_options[x],
            index=list(task_options.keys()).index(current_selection) if current_selection in task_options else 0
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
                
            col_exec1, col_exec2 = st.columns(2)
            with col_exec1:
                enable_runner_exec = st.checkbox("Enable Command Runner for Execution", value=False)
            with col_exec2:
                pass
                
            if st.button("▶️ Run Next Eligible Step"):
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
                        if st.button(f"Execute This Step #{step['step_number']}", key=f"exec_single_{step['id']}"):
                            success, msg = execute_step(step['id'], command_runner_enabled=enable_runner_exec)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_step2:
                        if st.button(f"Reset to PENDING", key=f"reset_{step['id']}"):
                            update_step_status(step['id'], "PENDING", "Reset manually by user.")
                            st.success("Step reset to PENDING.")
                            st.rerun()
            
            st.markdown("### 🧠 Operational Feedback Memory Log")
            if logs:
                for log in logs:
                    st.text(f"[{log['timestamp']}] {log['summary']}")
            else:
                st.info("No memory logs recorded yet.")

with tab4:
    st.subheader("🛠️ Safe Workspace Tools & Audited Operations")
    st.markdown("Inspect, read, search, edit files, or run pre-approved diagnostic commands under strict sandbox safety constraints.")
    
    tool_subtab1, tool_subtab2, tool_subtab3, tool_subtab4 = st.tabs(["📂 File Inspection & Read", "✏️ Safe File Editor", "🔍 Workspace Search", "⚡ Approved Command Runner"])
    
    with tool_subtab1:
        st.markdown("#### Workspace Files")
        files = list_workspace_files(st.session_state.active_task_id)
        selected_file = st.selectbox("Select File to Read", options=files if files else ["No files found"])
        
        if selected_file and selected_file != "No files found":
            if st.button("Read File Content"):
                success, content = read_text_file(selected_file, st.session_state.active_task_id)
                if success:
                    st.text_area("File Content (Read-Only)", value=content, height=300)
                else:
                    st.error(content)
                    
    with tool_subtab2:
        st.markdown("#### Safe File Editor & Creator")
        edit_path = st.text_input("Relative File Path", placeholder="e.g., notes.txt or src/component.py")
        edit_content = st.text_area("File Content", placeholder="Enter full file text content here...", height=250)
        
        if st.button("Save / Write File"):
            if edit_path.strip():
                success, msg = write_workspace_file(edit_path.strip(), edit_content, st.session_state.active_task_id)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("Please provide a valid relative file path.")
                
    with tool_subtab3:
        st.markdown("#### Workspace Search")
        query = st.text_input("Search Query (Filename or content keyword)", placeholder="Enter keyword...")
        if st.button("Search Workspace"):
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
                
    with tool_subtab4:
        st.markdown("#### Strict Command Runner")
        st.warning("⚠️ **Streamlit Community Cloud Limitation**: Command execution runs locally in the container sandbox and is disabled by default. Only pre-approved diagnostic commands on the strict allowlist are permitted.")
        
        enable_runner = st.checkbox("Enable Command Runner (Disabled by default)", key="runner_tab4")
        approved_list = list(APPROVED_COMMANDS)
        selected_cmd = st.selectbox("Select Approved Diagnostic Command", options=approved_list)
        
        if st.button("Execute Command"):
            success, output = run_approved_command(selected_cmd, enabled=enable_runner, task_id=st.session_state.active_task_id)
            if success:
                st.success("Command executed successfully:")
                st.code(output, language="text")
            else:
                st.error(output)

with tab5:
    st.subheader("📦 Dual Delivery Center")
    st.markdown("Export or prepare your project for distribution via GitHub (Option A) or direct ZIP archive (Option B). Streamlit Community Cloud filesystems are ephemeral; download a ZIP archive as your persistent portable copy.")
    
    delivery_tab1, delivery_tab2 = st.tabs(["🐙 Option A — GitHub Delivery", "🗂️ Option B — ZIP Archive Delivery"])
    
    with delivery_tab1:
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
git commit -m "Implement Phase 7: Autonomous Tool Orchestration"

# 5. Connect remote repository and push (requires user authentication)
# git remote add origin <your-github-repository-url>
# git push -u origin main
        """, language="bash")
        
    with delivery_tab2:
        st.markdown("#### Option B — Secure ZIP Archive Delivery")
        st.markdown("Generate and download a clean production ZIP archive containing all source code, manifests, and documentation while strictly excluding secrets (`.env`), database files (`data/`), caches, and virtual environments.")
        
        if st.button("Prepare Clean Project ZIP"):
            zip_data = generate_project_zip()
            st.session_state.zip_ready = True
            st.session_state.zip_bytes = zip_data
            st.success("ZIP archive prepared successfully!")
            
        if st.session_state.get("zip_ready", False):
            st.download_button(
                label="📥 Download LXNORO-Super-AI-Agent-0-1.zip",
                data=st.session_state.zip_bytes,
                file_name="LXNORO-Super-AI-Agent-0-1.zip",
                mime="application/zip"
            )
            st.markdown("✅ **ZIP Generated Successfully** (Distinct from GitHub push status).")
        else:
            st.info("Click 'Prepare Clean Project ZIP' above to generate your download package.")

with tab6:
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
    
    user_prompt = st.text_area("Prompt for NVIDIA Nemotron", placeholder="e.g., Explain the architecture of LXNORO Super AI Agent in 3 sentences.", value="Hello, NVIDIA Nemotron!")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        send_nebius = st.button("Send to Nebius API")
        
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

with tab7:
    st.subheader("🎯 Phase 7: Autonomous Tool Orchestration & Execution Engine")
    st.markdown("Orchestrate registered workspace and AI tools with schema validation, sensitivity approval gates, and dependency-aware execution.")
    
    orch_subtab1, orch_subtab2, orch_subtab3 = st.tabs(["📋 Tool Registry & Catalog", "🔍 Task Tool Selector", "⚡ Orchestrated Tool Executor"])
    
    with orch_subtab1:
        st.markdown("#### Registered Tools & Schemas")
        tools = get_registered_tools()
        for t in tools:
            with st.expander(f"`{t['name']}` — {'Sensitive ⚠️ (Approval Required)' if t['sensitive'] else 'Safe 🟢 (Read-Only)'}"):
                st.markdown(f"**Description:** {t['description']}")
                st.markdown(f"**Parameters:** `{t['parameters']}`")
                st.markdown(f"**Sensitivity:** `{'Sensitive (Requires explicit user approval)' if t['sensitive'] else 'Safe'}`")
                
    with orch_subtab2:
        st.markdown("#### Intelligent Tool Selector")
        st.markdown("Enter a task description or goal to see which tools the agent selects based on capability matching.")
        goal_query = st.text_input("Task Goal / Objective", placeholder="e.g., Read configuration file and ask NVIDIA Nemotron to summarize it")
        if st.button("Select Relevant Tools"):
            if goal_query.strip():
                selected_tools = select_relevant_tools(goal_query.strip())
                st.success(f"Selected {len(selected_tools)} relevant tool(s):")
                for st_tool in selected_tools:
                    st.markdown(f"- **`{st_tool['name']}`**: {st_tool['description']}")
            else:
                st.warning("Please enter a task goal.")
                
    with orch_subtab3:
        st.markdown("#### Orchestrated Tool Execution Playground")
        st.markdown("Execute any registered tool with parameter validation and mandatory approval gates for sensitive actions.")
        
        reg_tools = get_registered_tools()
        tool_names = [t["name"] for t in reg_tools]
        chosen_tool = st.selectbox("Select Tool to Execute", options=tool_names)
        
        tool_meta = {t["name"]: t for t in reg_tools}[chosen_tool]
        st.markdown(f"**Description:** {tool_meta['description']}")
        st.markdown(f"**Requires Approval:** `{'Yes ⚠️' if tool_meta['sensitive'] else 'No 🟢'}`")
        
        args_dict = {}
        if chosen_tool == "list_workspace_files":
            pass
        elif chosen_tool == "read_text_file":
            args_dict["rel_path"] = st.text_input("Relative File Path (e.g. README.md)", value="README.md")
        elif chosen_tool == "search_workspace":
            args_dict["query"] = st.text_input("Search Keyword / Query", value="agent")
        elif chosen_tool == "write_workspace_file":
            args_dict["rel_path"] = st.text_input("Relative File Path", value="notes.txt")
            args_dict["content"] = st.text_area("File Content", value="Autonomous orchestration note.")
        elif chosen_tool == "run_approved_command":
            args_dict["command"] = st.selectbox("Approved Diagnostic Command", options=["git status", "git diff HEAD"])
            args_dict["enabled"] = st.checkbox("Enable Command Runner", value=False)
        elif chosen_tool == "nebius_chat":
            args_dict["prompt"] = st.text_area("Nebius / Nemotron Prompt", value="Hello from LXNORO orchestration engine!")
            
        approval_checkbox = st.checkbox(
            "Grant Explicit User Approval for Sensitive Operation", 
            value=False,
            help="Mandatory for tools performing destructive changes, executing shell commands, or calling external APIs."
        )
        
        if st.button("Execute Orchestrated Tool Call"):
            with st.spinner("Validating schema and executing tool..."):
                success, result = execute_orchestrated_tool(chosen_tool, args_dict, approval_granted=approval_checkbox, task_id=st.session_state.active_task_id)
                if success:
                    st.success("Tool execution completed successfully!")
                    if isinstance(result, (list, dict)):
                        st.json(result)
                    else:
                        st.text_area("Tool Output", value=str(result), height=250)
                else:
                    st.error(f"Tool Execution Failed: {result}")

with tab6:
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
    
    user_prompt = st.text_area("Prompt for NVIDIA Nemotron", placeholder="e.g., Explain the architecture of LXNORO Super AI Agent in 3 sentences.", value="Hello, NVIDIA Nemotron!")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        send_nebius = st.button("Send to Nebius API")
        
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
