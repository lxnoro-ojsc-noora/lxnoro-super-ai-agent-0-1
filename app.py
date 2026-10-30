import os
import streamlit as st
from dotenv import load_dotenv
from agent_memory import (
    init_db, create_task, get_tasks, get_task, 
    get_steps, update_step_status, get_memory_logs,
    get_long_term_memories, modify_project
)
from workspace_tools import (
    list_workspace_files, read_text_file, write_workspace_file,
    search_workspace
)
from execution_engine import (
    get_next_eligible_step, execute_step, recover_interrupted_steps
)
from delivery_utils import get_git_status_info, generate_project_zip
from nebius_client import get_nebius_api_key, get_nebius_model

load_dotenv()
init_db()

st.set_page_config(
    page_title="LXNORO Super AI Agent 0-1",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Professional Command-Center Aesthetic CSS
st.markdown("""
<style>
.stApp {
    background-color: #0b0e14 !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #07090d !important;
    border-right: 1px solid #1e2633 !important;
}
[data-testid="stHeader"] {
    background-color: rgba(11, 14, 20, 0.95) !important;
}
h1, h2, h3, h4, h5, h6, p, span, label, div {
    color: #f1f5f9 !important;
}
div.stMarkdown, div.stExpander, div.stForm, div[data-testid="stVerticalBlock"] > div {
    background-color: #121720 !important;
    border: 1px solid #1e2633 !important;
    border-radius: 6px !important;
    padding: 1rem !important;
    margin-bottom: 1rem !important;
    color: #f1f5f9 !important;
}
.stButton>button {
    background: #1e2633 !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
}
.stButton>button:hover {
    background: #334155 !important;
    border-color: #4f46e5 !important;
    color: #ffffff !important;
}
input, textarea, select, div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    background-color: #0f131a !important;
    color: #f1f5f9 !important;
    border: 1px solid #27303f !important;
    border-radius: 6px !important;
}
input::placeholder, textarea::placeholder {
    color: #64748b !important;
}
.stTextInput input, .stTextArea textarea {
    color: #f1f5f9 !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div, div[data-baseweb="select"] svg {
    color: #f1f5f9 !important;
    fill: #f1f5f9 !important;
}
.stRadio label, .stCheckbox label {
    color: #e2e8f0 !important;
    font-weight: 500 !important;
}
table {
    background-color: #121720 !important;
    color: #f1f5f9 !important;
}
th {
    background-color: #1a2230 !important;
    color: #f8fafc !important;
    font-weight: 600 !important;
}
td {
    color: #cbd5e1 !important;
    border-bottom: 1px solid #1e2633 !important;
}
.stAlert {
    background-color: #121720 !important;
    color: #f1f5f9 !important;
    border: 1px solid #334155 !important;
}
.brand-container {
    padding: 0.75rem 0 1rem 0;
    border-bottom: 1px solid #1e2633;
    margin-bottom: 1rem;
}
.brand-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: #f8fafc;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 0;
}
.brand-subtitle {
    font-size: 0.7rem;
    color: #94a3b8;
    margin-top: 0.2rem;
    letter-spacing: 0.5px;
}
.metric-card {
    background-color: #121720;
    border: 1px solid #1e2633;
    padding: 1rem;
    border-radius: 6px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state for active task
if "active_task_id" not in st.session_state:
    tasks = get_tasks()
    st.session_state.active_task_id = tasks[0]["id"] if tasks else None

# Sidebar Navigation & Command Center Controls
with st.sidebar:
    st.markdown("""
        <div class="brand-container">
            <div class="brand-title">LXNORO SUPER AI AGENT</div>
            <div class="brand-subtitle">Autonomous Dev Command Center • v0.1</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🗂️ Project Workspace")
    tasks = get_tasks()
    task_options = {t['id']: f"#{t['id']}: {t['goal'][:35]}... ({t['status']})" for t in tasks} if tasks else {}
    
    if task_options:
        selected_task_id = st.selectbox(
            "Switch Active Project",
            options=list(task_options.keys()),
            format_func=lambda x: task_options[x],
            key="sidebar_task_selectbox"
        )
        if selected_task_id != st.session_state.active_task_id:
            st.session_state.active_task_id = selected_task_id
            st.rerun()
    else:
        st.markdown("*No projects found.*")

    st.markdown("---")
    st.markdown("### ⚙️ System Status")
    nebius_status = "🟢 Active" if get_nebius_api_key() else "⚪ Smart Local Fallback"
    st.markdown(f"- **Nemotron/Nebius:** {nebius_status}")
    st.markdown(f"- **Model:** `{get_nebius_model()}`")
    st.markdown(f"- **Database:** `data/agent_memory.db`")

    st.markdown("---")
    st.markdown("### 🧭 Command Center Navigation")
    nav_mode = st.radio(
        "Select View",
        [
            "🚀 Autonomous Pipeline & Execution",
            "📂 Workspace Files & Code Editor",
            "📊 Execution Logs & Memory"
        ],
        key="command_center_nav"
    )

# Main Header Banner
st.markdown("""
    <div style="padding: 0.2rem 0 1rem 0;">
        <h1 style="margin-bottom: 0px; font-size: 1.8rem; color: #f8fafc;">⚡ LXNORO SUPER AI AGENT</h1>
        <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">Autonomous Software Development Agent — Natural Language to Runnable Project</p>
    </div>
""", unsafe_allow_html=True)

# Route based on navigation selection
if "Autonomous Pipeline" in nav_mode:
    st.subheader("🚀 Autonomous Software Development Pipeline")
    
    # New Project Creation Form
    with st.form("new_project_form"):
        st.markdown("**Initialize New Autonomous Project**")
        project_idea = st.text_area(
            "Software Project Idea (Natural Language)", 
            placeholder="e.g., Build a full-stack REST API service with SQLite database and FastAPI in Python",
            height=90,
            key="new_project_idea_input"
        )
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            step_count = st.slider("Implementation Plan Steps", min_value=3, max_value=12, value=5, key="new_project_steps_slider")
        with col_f2:
            st.markdown("<br>", unsafe_allow_html=True)
            submit_idea = st.form_submit_button("🚀 START BUILDING PROJECT")
            
        if submit_idea:
            if project_idea.strip():
                with st.spinner("Initializing autonomous planning engine & workspace..."):
                    new_id = create_task(project_idea.strip(), step_count)
                    st.session_state.active_task_id = new_id
                st.success(f"Project initialized successfully! Task #{new_id} created.")
                st.rerun()
            else:
                st.error("Please enter a software project idea.")

    st.markdown("---")
    
    # Active Task Live Monitor & Execution
    if st.session_state.active_task_id:
        recover_interrupted_steps(st.session_state.active_task_id)
        task = get_task(st.session_state.active_task_id)
        steps = get_steps(st.session_state.active_task_id)
        files = list_workspace_files(st.session_state.active_task_id)
        
        if task:
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.markdown(f"**Project ID:** #{task['id']}")
            with col_m2:
                st.markdown(f"**Status:** `{task['status']}`")
            with col_m3:
                completed_count = sum(1 for s in steps if s['status'] == 'COMPLETED')
                st.markdown(f"**Progress:** {completed_count}/{len(steps)} Steps")
            with col_m4:
                st.markdown(f"**Workspace Files:** {len(files)}")
                
            st.markdown(f"**Active Goal:** {task['goal']}")
            
            # Step execution controls
            next_step = get_next_eligible_step(task['id'])
            if next_step:
                st.info(f"**Next Eligible Step:** Step {next_step['step_number']} — {next_step['title']} (Status: `{next_step['status']}`)")
                
                col_ex1, col_ex2 = st.columns(2)
                with col_ex1:
                    if st.button("▶️ Run Next Step", key="exec_next_step_btn"):
                        success, msg = execute_step(next_step['id'])
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                with col_ex2:
                    if st.button("⚡ Auto-Run All Remaining Steps", key="exec_all_steps_btn"):
                        curr = next_step
                        while curr:
                            succ, msg = execute_step(curr['id'])
                            if not succ:
                                st.error(f"Execution halted on Step {curr['step_number']}: {msg}")
                                break
                            curr = get_next_eligible_step(task['id'])
                        st.success("All remaining steps executed successfully!")
                        st.rerun()
            else:
                st.success("🎉 All project implementation steps completed successfully! Review source files below or download delivery package.")

            st.markdown("#### 📋 Implementation Plan & Steps Breakdown")
            for s in steps:
                with st.expander(f"Step {s['step_number']}: {s['title']} [{s['status']}]"):
                    st.markdown(f"**Objective:** {s['objective']}")
                    st.markdown(f"**Execution Result:** {s['result'] or 'Pending execution.'}")

            st.markdown("#### 📂 Workspace Files Generated")
            if files:
                for f_path in files:
                    st.markdown(f"- `{f_path}`")
            else:
                st.info("No files generated in workspace yet.")

            st.markdown("---")
            st.markdown("#### 🔄 Continuous Project Modification (Natural Language Follow-up)")
            with st.form("continuous_modification_form"):
                mod_prompt = st.text_input(
                    "Follow-up Instructions / Feature Request",
                    placeholder="e.g., Add unit tests for the core modules and enhance error logging",
                    key="mod_prompt_input"
                )
                submit_mod = st.form_submit_button("Apply In-Place Modification")
                if submit_mod:
                    if mod_prompt.strip():
                        with st.spinner("Modifying project in place using orchestrated workspace tools..."):
                            success, msg, changed = modify_project(task['id'], mod_prompt.strip())
                        if success:
                            st.success(f"{msg} Changed files: {', '.join(changed)}")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter modification instructions.")

            st.markdown("---")
            st.markdown("#### 📦 Delivery & Export Center")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("Prepare Project ZIP Archive", key="prep_zip_btn"):
                    zip_data = generate_project_zip()
                    st.download_button(
                        "📥 Download Runnable Project ZIP",
                        data=zip_data,
                        file_name=f"LXNORO-Project-{task['id']}.zip",
                        mime="application/zip",
                        key="download_zip_action"
                    )
            with col_d2:
                git_info = get_git_status_info()
                st.text_input("Git Status Summary", value=git_info['status_output'].split('\n')[0] if git_info['status_output'] else "Clean", disabled=True, key="git_status_display")
    else:
        st.info("No active project selected. Initialize a project above or select one from the sidebar.")

elif "Workspace Files & Code Editor" in nav_mode:
    st.subheader("📂 Workspace Files & Code Editor")
    
    if not st.session_state.active_task_id:
        st.warning("No active project selected.")
    else:
        files = list_workspace_files(st.session_state.active_task_id)
        
        col_fe1, col_fe2 = st.columns([1, 2])
        with col_fe1:
            st.markdown("**Workspace File Tree**")
            selected_file = st.selectbox("Select File to Inspect", options=files if files else ["No files"], key="editor_file_select")
            
            search_q = st.text_input("Search Codebase", placeholder="Enter keyword...", key="editor_search_input")
            if search_q.strip():
                matches = search_workspace(search_q.strip(), st.session_state.active_task_id)
                st.markdown("**Search Results:**")
                for m in matches:
                    st.markdown(f"- `{m}`")
                    
        with col_fe2:
            st.markdown("**File Content & Editor**")
            if selected_file and selected_file != "No files":
                success, content = read_text_file(selected_file, st.session_state.active_task_id)
                if success:
                    edited_content = st.text_area("File Source Code", value=content, height=350, key="editor_content_textarea")
                    if st.button("Save File Changes", key="editor_save_btn"):
                        ok, msg = write_workspace_file(selected_file, edited_content, st.session_state.active_task_id)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                else:
                    st.error(content)
            else:
                st.info("Select a file from the left to view or edit.")

elif "Execution Logs & Memory" in nav_mode:
    st.subheader("📊 Execution Logs & Persistent Memory")
    
    if not st.session_state.active_task_id:
        st.warning("No active project selected.")
    else:
        task_id = st.session_state.active_task_id
        logs = get_memory_logs(task_id)
        memories = get_long_term_memories()
        
        tab_l1, tab_l2 = st.tabs(["📝 Task Execution & Audit Logs", "🧠 Long-Term Memories"])
        with tab_l1:
            st.markdown(f"**Audit & Memory Trail for Task #{task_id}**")
            if logs:
                for log in logs:
                    st.text(f"[{log['timestamp']}] {log['summary']}")
            else:
                st.info("No execution logs recorded yet.")
                
        with tab_l2:
            st.markdown("**Global Long-Term Agent Memories**")
            if memories:
                for mem in memories:
                    st.markdown(f"- **[{mem['category']}] `{mem['memory_key']}`**: {mem['content']} *(Importance: {mem['importance']})*")
            else:
                st.info("No long-term memories stored.")
