import os
import streamlit as st
from dotenv import load_dotenv
from agent_memory import (
    init_db, create_task, get_tasks, get_task, 
    get_steps, update_step_status, get_memory_logs,
    store_long_term_memory, get_long_term_memories,
    search_long_term_memories, update_long_term_memory,
    delete_long_term_memory, clear_long_term_memories,
    get_relevant_memory_context, modify_project
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

# Comprehensive High-Contrast Cyberpunk / Video-Game Tactical Theme CSS
st.markdown("""
<style>
.stApp {
    background-color: #07050b !important;
    color: #ffffff !important;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #040208 !important;
    border-right: 1px solid #1c0f2e !important;
}
[data-testid="stHeader"] {
    background-color: rgba(7, 5, 11, 0.95) !important;
}
h1, h2, h3, h4, h5, h6, p, span, label, div, .stMarkdown, .stText, stMarkdown p {
    color: #ffffff !important;
}
div.stMarkdown, div.stExpander, div.stForm, div[data-testid="stVerticalBlock"] > div {
    background-color: #11091d !important;
    border: 1px solid #2b144a !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    margin-bottom: 1rem !important;
    color: #ffffff !important;
}
.stButton>button {
    background: linear-gradient(135deg, #2c144a 0%, #130a21 100%) !important;
    color: #ffffff !important;
    border: 1px solid #7b2cbf !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #7b2cbf 0%, #2c144a 100%) !important;
    border-color: #c084fc !important;
    box-shadow: 0 0 15px rgba(168, 85, 247, 0.5) !important;
    color: #ffffff !important;
}
input, textarea, select, div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    background-color: #0b0514 !important;
    color: #ffffff !important;
    border: 1px solid #3b1d63 !important;
    border-radius: 6px !important;
}
input::placeholder, textarea::placeholder {
    color: #a0a0b8 !important;
}
.stTextInput input, .stTextArea textarea {
    color: #ffffff !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div, div[data-baseweb="select"] svg {
    color: #ffffff !important;
    fill: #ffffff !important;
}
.stRadio label, .stCheckbox label {
    color: #ffffff !important;
    font-weight: 600 !important;
}
table {
    background-color: #11091d !important;
    color: #ffffff !important;
}
th {
    background-color: #1f0f35 !important;
    color: #ffffff !important;
    font-weight: bold !important;
}
td {
    color: #f3f4f6 !important;
    border-bottom: 1px solid #2b144a !important;
}
.stAlert {
    background-color: #11091d !important;
    color: #ffffff !important;
    border: 1px solid #581c87 !important;
}
.brand-container {
    padding: 0.75rem 0 1rem 0;
    border-bottom: 1px solid #2b144a;
    margin-bottom: 1rem;
}
.brand-title {
    font-size: 1.25rem;
    font-weight: 900;
    color: #d8b4fe;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 0;
    text-shadow: 0 0 10px rgba(168, 85, 247, 0.4);
}
.brand-subtitle {
    font-size: 0.75rem;
    color: #c084fc;
    margin-top: 0.3rem;
    letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation & Branding
with st.sidebar:
    st.markdown("""
        <div class="brand-container">
            <div class="brand-title">LXNORO SUPER AI AGENT</div>
            <div class="brand-subtitle">Autonomous Pipeline • v0.1</div>
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
            "🚀 Start Building (Autonomous Pipeline)",
            "🧠 Task Memory & Execution Engine",
            "🛠️ Safe Workspace Tools",
            "📦 Dual Delivery Center",
            "⚡ Nebius & Nemotron",
            "🎯 Tool Orchestration",
            "🧠 Persistent Long-Term Memory",
            "🚀 Dashboard & Roadmap"
        ],
        key="main_navigation_radio"
    )

# Main Header Banner
st.markdown("""
    <div style="padding: 0.5rem 0 1rem 0;">
        <h1 style="margin-bottom: 0px; font-size: 2rem; color: #ffffff;">🤖 LXNORO SUPER AI AGENT</h1>
        <p style="color: #e2e8f0; font-size: 0.95rem; margin-top: 4px;">Autonomous Software Development Pipeline — Natural Language Idea to Runnable Project</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state for active task
if "active_task_id" not in st.session_state:
    st.session_state.active_task_id = None

# Route based on navigation selection
if "Start Building" in nav_selection:
    st.subheader("🚀 Autonomous Software Development Pipeline")
    st.markdown("Enter a natural-language software project request. The agent will autonomously generate a dynamic plan using Nemotron (with smart fallback), orchestrate workspace tools, create/modify actual project files, and persist progress.")
    
    # Single idea input & START BUILDING action
    with st.form("start_building_form"):
        project_idea = st.text_area(
            "Natural-Language Software Project Idea", 
            placeholder="e.g., Build a real-time collaborative task management web app with Python and Streamlit",
            height=120,
            key="start_building_idea_input"
        )
        step_slider = st.slider("Implementation Plan Steps", min_value=3, max_value=20, value=5, key="start_building_steps_slider")
        submit_build = st.form_submit_button("🚀 START BUILDING")
        
        if submit_build:
            if project_idea.strip():
                with st.spinner("Nemotron planning engine generating architectural plan and initializing workspace..."):
                    new_id = create_task(project_idea.strip(), step_slider)
                    st.session_state.active_task_id = new_id
                st.success(f"Project initialized successfully! Task #{new_id} created with {step_slider} autonomous steps.")
                st.rerun()
            else:
                st.error("Please enter a software project idea.")

    # If an active task is loaded, show live execution progress and files
    if st.session_state.active_task_id:
        st.markdown("---")
        st.markdown("### 📊 Live Execution Monitor & Progress")
        
        task = get_task(st.session_state.active_task_id)
        steps = get_steps(st.session_state.active_task_id)
        files = list_workspace_files(st.session_state.active_task_id)
        
        if task:
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.markdown(f"**Task ID:** #{task['id']}")
            with col_m2:
                st.markdown(f"**Status:** `{task['status']}`")
            with col_m3:
                st.markdown(f"**Total Files Created:** {len(files)}")
                
            st.markdown(f"**Current Goal:** {task['goal']}")
            
            # Execution Control
            next_step = get_next_eligible_step(task['id'])
            if next_step:
                st.info(f"**Next Eligible Step:** Step {next_step['step_number']} — {next_step['title']} (Status: `{next_step['status']}`)")
                
                col_ex1, col_ex2 = st.columns(2)
                with col_ex1:
                    if st.button("▶️ Run Next Step", key="live_run_next_btn"):
                        success, msg = execute_step(next_step['id'])
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                with col_ex2:
                    if st.button("⚡ Auto-Run All Remaining Steps", key="live_run_all_btn"):
                        curr_step = next_step
                        while curr_step:
                            s_success, s_msg = execute_step(curr_step['id'])
                            if not s_success:
                                st.error(f"Execution halted on Step {curr_step['step_number']}: {s_msg}")
                                break
                            curr_step = get_next_eligible_step(task['id'])
                        st.success("All remaining steps executed successfully!")
                        st.rerun()
            else:
                st.success("🎉 All project implementation steps completed successfully! Review project files below or download delivery ZIP.")

            st.markdown("#### 📋 Plan Steps Breakdown")
            for s in steps:
                with st.expander(f"Step {s['step_number']}: {s['title']} [{s['status']}]"):
                    st.markdown(f"**Objective:** {s['objective']}")
                    st.markdown(f"**Result:** {s['result'] or 'Pending execution.'}")

            st.markdown("#### 📂 Workspace Files Created / Modified")
            if files:
                for f_path in files:
                    st.markdown(f"- `{f_path}`")
            else:
                st.info("No files created in workspace yet.")

            st.markdown("---")
            st.markdown("#### 🔄 Continuous Modification (Modify Existing Project)")
            with st.form("continuous_mod_form"):
                mod_request = st.text_input("Request Project Modification / Follow-up Feature", placeholder="e.g., Add dark mode toggle and user authentication module", key="mod_request_input")
                submit_mod = st.form_submit_button("Apply Targeted Modification")
                if submit_mod:
                    if mod_request.strip():
                        with st.spinner("Applying in-place project modification using orchestrated workspace tools..."):
                            success, msg, changed_files = modify_project(task['id'], mod_request.strip())
                        if success:
                            st.success(f"{msg} Changed file(s): {', '.join(changed_files)}")
                            st.rerun()
                        else:
                            st.error(f"Modification failed: {msg}")
                    else:
                        st.warning("Please enter a modification request.")

elif "Task Memory & Execution" in nav_selection:
    st.subheader("🧠 Persistent Task Memory & Execution Engine")
    tasks = get_tasks()
    if not tasks:
        st.warning("No tasks available. Use 'Start Building' to create a project.")
    else:
        task_options = {t['id']: f"Task #{t['id']}: {t['goal']} ({t['status']})" for t in tasks}
        selected_task_id = st.selectbox("Select Task", options=list(task_options.keys()), format_func=lambda x: task_options[x], key="exec_task_sel")
        st.session_state.active_task_id = selected_task_id
        
        recover_interrupted_steps(selected_task_id)
        task = get_task(selected_task_id)
        steps = get_steps(selected_task_id)
        logs = get_memory_logs(selected_task_id)
        
        if task:
            st.markdown(f"**Goal:** {task['goal']}")
            st.markdown(f"**Status:** `{task['status']}`")
            next_step = get_next_eligible_step(selected_task_id)
            if next_step and st.button("Run Next Eligible Step", key="exec_engine_run_btn"):
                succ, msg = execute_step(next_step['id'])
                if succ:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
                    
            st.markdown("### Steps")
            for s in steps:
                st.markdown(f"- Step {s['step_number']}: {s['title']} [`{s['status']}`] — {s['result']}")

            st.markdown("### Memory Logs")
            for l in logs:
                st.text(f"[{l['timestamp']}] {l['summary']}")

elif "Safe Workspace Tools" in nav_selection:
    st.subheader("🛠️ Safe Workspace Tools")
    tool_sub1, tool_sub2, tool_sub3 = st.tabs(["📂 File Inspection", "✏️ File Editor", "🔍 Search"])
    with tool_sub1:
        files = list_workspace_files(st.session_state.active_task_id)
        sel = st.selectbox("Select File", options=files if files else ["No files"], key="tools_file_sel")
        if sel and sel != "No files" and st.button("Read File", key="tools_read_btn"):
            ok, content = read_text_file(sel, st.session_state.active_task_id)
            if ok:
                st.text_area("Content", value=content, height=250, key="tools_content_area")
            else:
                st.error(content)
    with tool_sub2:
        path = st.text_input("File Path", value="notes.txt", key="tools_edit_path")
        content = st.text_area("Content", value="New content", key="tools_edit_content")
        if st.button("Save File", key="tools_save_btn"):
            ok, msg = write_workspace_file(path, content, st.session_state.active_task_id)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
    with tool_sub3:
        q = st.text_input("Search Query", key="tools_search_q")
        if st.button("Search", key="tools_search_btn") and q.strip():
            matches = search_workspace(q.strip(), st.session_state.active_task_id)
            for m in matches:
                st.markdown(f"- `{m}`")

elif "Dual Delivery Center" in nav_selection:
    st.subheader("📦 Dual Delivery Center")
    del_sub1, del_sub2 = st.tabs(["🐙 GitHub Delivery", "🗂️ ZIP Archive Delivery"])
    with del_sub1:
        git_info = get_git_status_info()
        st.code(git_info['status_output'], language="text")
    with del_sub2:
        if st.button("Prepare Project ZIP", key="delivery_zip_btn"):
            zip_bytes = generate_project_zip()
            st.download_button("📥 Download Project ZIP", data=zip_bytes, file_name="LXNORO-Autonomous-Project.zip", mime="application/zip", key="delivery_download_btn")

elif "Nebius & Nemotron" in nav_selection:
    st.subheader("⚡ Nebius Token Factory + NVIDIA Nemotron Integration")
    prompt = st.text_area("Prompt for Nemotron", value="Hello Nemotron", key="nebius_prompt_box")
    if st.button("Send to Nebius", key="nebius_send_btn") and prompt.strip():
        res = nebius_chat_completion(prompt.strip())
        if res["success"]:
            st.success(res["content"])
        else:
            st.error(res["error"])

elif "Tool Orchestration" in nav_selection:
    st.subheader("🎯 Autonomous Tool Orchestration")
    tools = get_registered_tools()
    for t in tools:
        st.markdown(f"- **`{t['name']}`**: {t['description']}")

elif "Persistent Long-Term Memory" in nav_selection:
    st.subheader("🧠 Persistent Long-Term Memory")
    mems = get_long_term_memories()
    st.markdown(f"Total memories: {len(mems)}")
    for m in mems:
        st.markdown(f"- **[{m['category']}] {m['memory_key']}**: {m['content']}")

elif "Dashboard & Roadmap" in nav_selection:
    st.subheader("🚀 Operational Dashboard & Roadmap")
    tasks = get_tasks()
    st.markdown(f"Total tasks: {len(tasks)}")
    roadmap = [
        {"Phase": "Phase 1-8", "Focus": "Autonomous Software Development Pipeline & Integration", "Status": "Completed ✅"}
    ]
    st.table(roadmap)
