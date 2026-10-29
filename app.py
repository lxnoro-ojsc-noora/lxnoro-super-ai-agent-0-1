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

load_dotenv()
init_db()

st.set_page_config(
    page_title="LXNORO Super AI Agent 0-1",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 LXNORO Super AI Agent 0-1")
st.markdown("### Streamlit Community Cloud Edition — Phase 4: Execution & Recovery Engine")

st.sidebar.header("Agent Configuration")
api_key_input = st.sidebar.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))

st.sidebar.markdown("---")
st.sidebar.subheader("Project Delivery Options")
st.sidebar.markdown("- **Option A:** GitHub Delivery")
st.sidebar.markdown("- **Option B:** ZIP Archive Delivery")

# Initialize session state for active task
if "active_task_id" not in st.session_state:
    st.session_state.active_task_id = None

# Main interface tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Dashboard & Roadmap", 
    "➕ Create Task & Plan", 
    "🧠 Task Memory & Steps", 
    "🛠️ Safe Workspace Tools", 
    "📦 Delivery Center"
])

with tab1:
    st.subheader("Welcome to LXNORO Super AI Agent 0-1")
    st.info("Phase 4 active: Resumable execution engine, dependency validation, bounded retries, and deterministic tool actions operational.")
    
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
        {"Phase": "Phase 4 (Current)", "Focus": "Execution & Recovery Engine (Resumable Steps, Retries, Validation)", "Status": "Completed ✅"},
        {"Phase": "Phase 5", "Focus": "Dual Delivery Center (GitHub Delivery & ZIP Archive Export)", "Status": "Pending ⏳"}
    ]
    st.table(roadmap_data)

with tab2:
    st.subheader("Create a New Task & Dynamic Plan (1–50 Steps)")
    with st.form("task_form"):
        goal_input = st.text_area("Task Goal / Objective", placeholder="e.g., Run automated diagnostics and validate workspace architecture")
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
    st.subheader("Project Delivery Center")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Option A — GitHub Delivery")
        st.markdown("Prepare for GitHub repository push with exact local git instructions.")
        st.code("git init\ngit add .\ngit commit -m 'Initial commit: Phase 4 Execution Engine'\n# git remote add origin <url>\n# git push -u origin main", language="bash")
    with col2:
        st.markdown("#### Option B — ZIP Delivery")
        st.markdown("Export cleaned project archive excluding secrets, temp files, and caches.")
        if st.button("Generate ZIP Export Manifest"):
            st.success("ZIP manifest ready. (Export functionality active in final phase). Note: SQLite database in `data/` and local temp files are excluded from ZIP production export as per ephemeral storage policy.")
