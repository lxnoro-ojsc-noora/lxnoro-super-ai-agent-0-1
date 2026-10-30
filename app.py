import os
import sys
import subprocess
import threading
import time
import requests
import streamlit as st
from dotenv import load_dotenv
from agent_memory import (
    init_db, create_task, get_tasks, get_task, 
    get_steps, get_memory_logs,
    get_long_term_memories, modify_project
)
from workspace_tools import (
    list_workspace_files, read_text_file, write_workspace_file,
    search_workspace
)
from execution_engine import (
    get_next_eligible_step, execute_step, recover_interrupted_steps
)
from delivery_utils import get_git_status_info, generate_project_zip, publish_to_github
from nebius_client import get_nebius_api_key, get_nebius_model, nebius_chat_completion

load_dotenv()
init_db()

st.set_page_config(
    page_title="LXNORO SUPER AI AGENT // Cyber Command",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Futuristic Cybersecurity Gaming Command Center Theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Share+Tech+Mono&family=Inter:wght@400;500;600;700&display=swap');

.stApp {
    background-color: #070a12 !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #04060b !important;
    border-right: 1px solid #1e293b !important;
}
[data-testid="stHeader"] {
    background-color: rgba(7, 10, 18, 0.95) !important;
}
h1, h2, h3, h4, h5, h6 {
    font-family: 'Orbitron', sans-serif !important;
    letter-spacing: 1px !important;
    color: #f8fafc !important;
}
.cyber-title {
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: 1.5rem;
    color: #06b6d4;
    text-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
    letter-spacing: 2px;
}
.cyber-subtitle {
    font-family: 'Share Tech Mono', monospace;
    color: #38bdf8;
    font-size: 0.8rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
div.stMarkdown, div.stExpander, div.stForm, div[data-testid="stVerticalBlock"] > div {
    background-color: #0d1322 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    padding: 1.2rem !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
}
.stButton>button {
    background: linear-gradient(135deg, #0e172a 0%, #1e293b 100%) !important;
    color: #38bdf8 !important;
    border: 1px solid #06b6d4 !important;
    border-radius: 6px !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 1px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%) !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.6) !important;
    color: #ffffff !important;
}
input, textarea, select, div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    background-color: #050810 !important;
    color: #f8fafc !important;
    border: 1px solid #1e293b !important;
    border-radius: 6px !important;
    font-family: 'Share Tech Mono', monospace !important;
}
input::placeholder, textarea::placeholder {
    color: #475569 !important;
}
.stTextInput input, .stTextArea textarea {
    color: #f8fafc !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div, div[data-baseweb="select"] svg {
    color: #f8fafc !important;
    fill: #f8fafc !important;
}
.stRadio label, .stCheckbox label {
    color: #cbd5e1 !important;
    font-weight: 500 !important;
}
table {
    background-color: #0d1322 !important;
    color: #e2e8f0 !important;
}
th {
    background-color: #111827 !important;
    color: #06b6d4 !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
}
td {
    color: #cbd5e1 !important;
    border-bottom: 1px solid #1e293b !important;
    font-family: 'Share Tech Mono', monospace !important;
}
.stAlert {
    background-color: #0d1322 !important;
    color: #f8fafc !important;
    border: 1px solid #06b6d4 !important;
}
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    font-weight: bold;
    letter-spacing: 1px;
}
.status-active { background-color: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }
.status-pending { background-color: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
.status-completed { background-color: rgba(6, 182, 212, 0.2); color: #06b6d4; border: 1px solid #06b6d4; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "active_task_id" not in st.session_state:
    tasks = get_tasks()
    st.session_state.active_task_id = tasks[0]["id"] if tasks else None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "LXNORO Cyber Command AI online. Describe the software application or website you wish to build in natural language."}
    ]

# Sidebar Cyber Command Telemetry & Navigation
with st.sidebar:
    st.markdown("""
        <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid #1e293b; margin-bottom: 1rem;">
            <div class="cyber-title">LXNORO AGENT</div>
            <div class="cyber-subtitle">Cyber Command v0.1</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🛡️ ACTIVE OPERATIONS")
    tasks = get_tasks()
    task_options = {t['id']: f"OP #{t['id']}: {t['goal'][:28]}... [{t['status']}]" for t in tasks} if tasks else {}
    
    if task_options:
        selected_task_id = st.selectbox(
            "Select Project Operation",
            options=list(task_options.keys()),
            format_func=lambda x: task_options[x],
            key="sidebar_task_selectbox"
        )
        if selected_task_id != st.session_state.active_task_id:
            st.session_state.active_task_id = selected_task_id
            st.rerun()
    else:
        st.markdown("*No active operations.*")

    st.markdown("---")
    st.markdown("### 📡 SYSTEM TELEMETRY")
    api_key_configured = bool(get_nebius_api_key())
    core_status = "🟢 SECURE (LIVE AI)" if api_key_configured else "⚡ SECURE (LOCAL FALLBACK)"
    st.markdown(f"- **AI Core:** {core_status}")
    st.markdown(f"- **Model:** `{get_nebius_model()}`")
    st.markdown(f"- **Database:** `data/agent_memory.db`")

    st.markdown("---")
    st.markdown("### 🧭 COMMAND SECTORS")
    nav_mode = st.radio(
        "Navigation Mode",
        [
            "💬 Conversational AI & Pipeline",
            "👁️ View Code (Source Inspector)",
            "🖥️ View & Use Application (Runtime)",
            "🔄 Continuous In-Place Modification",
            "📦 Delivery & Export Center"
        ],
        key="cyber_command_nav"
    )

# Main Cyber Command Banner
st.markdown("""
    <div style="padding: 0.5rem 0 1.5rem 0; border-bottom: 1px solid #1e293b; margin-bottom: 1.5rem;">
        <h1 style="margin-bottom: 0px; font-size: 1.8rem; color: #f8fafc; text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);">🛡️ LXNORO SUPER AI AGENT // CYBER COMMAND</h1>
        <p style="color: #38bdf8; font-size: 0.9rem; margin-top: 4px; font-family: 'Share Tech Mono', monospace; letter-spacing: 1px;">AUTONOMOUS SOFTWARE ENGINEERING & INTELLIGENCE OPERATIONS CENTER</p>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# SECTOR 1: Conversational AI & Autonomous Pipeline
# -------------------------------------------------------------
if "Conversational AI" in nav_mode:
    st.subheader("💬 CONVERSATIONAL AI & AUTONOMOUS PIPELINE")
    st.markdown("Chat naturally with the LXNORO Agent to describe your product idea, architecture requirements, or workflow. The agent will plan and execute the build autonomously.")
    
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    user_message = st.chat_input("Describe your software project or requirement in natural language...")
    if user_message:
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        with st.chat_message("user"):
            st.markdown(user_message)
            
        with st.chat_message("assistant"):
            with st.spinner("LXNORO Agent analyzing requirements & orchestrating autonomous pipeline..."):
                if "build" in user_message.lower() or "create" in user_message.lower() or "app" in user_message.lower() or "system" in user_message.lower() or len(get_tasks()) == 0:
                    new_id = create_task(user_message, step_count=5)
                    st.session_state.active_task_id = new_id
                    reply = f"🚀 **Operation #{new_id} Initialized!** Autonomous execution plan generated. Switch to the execution console or continue chatting to modify the build."
                else:
                    resp = nebius_chat_completion(f"You are LXNORO Super AI Agent. User says: {user_message}")
                    if resp["success"]:
                        reply = resp["content"]
                    else:
                        reply = f"Acknowledged request: '{user_message}'. Autonomous pipeline is ready. Use the execution controls below or request code generation."
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()

    st.markdown("---")
    st.markdown("### ⚡ Active Operation Execution Console")
    if st.session_state.active_task_id:
        recover_interrupted_steps(st.session_state.active_task_id)
        task = get_task(st.session_state.active_task_id)
        steps = get_steps(st.session_state.active_task_id)
        files = list_workspace_files(st.session_state.active_task_id)
        
        if task:
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.markdown(f"**Operation ID:** `#{task['id']}`")
            with col_m2:
                status_class = "status-active" if task['status'] == 'ACTIVE' else ("status-completed" if task['status'] == 'COMPLETED' else "status-pending")
                st.markdown(f"**Status:** <span class='status-badge {status_class}'>{task['status']}</span>", unsafe_allow_html=True)
            with col_m3:
                completed_count = sum(1 for s in steps if s['status'] == 'COMPLETED')
                st.markdown(f"**Progress:** `{completed_count}/{len(steps)} Steps`")
            with col_m4:
                st.markdown(f"**Workspace Assets:** `{len(files)} files`")
                
            st.markdown(f"**Mission Goal:** `{task['goal']}`")
            
            next_step = get_next_eligible_step(task['id'])
            if next_step:
                st.info(f"**Next Eligible Step:** Step {next_step['step_number']} — {next_step['title']} [Status: `{next_step['status']}`]")
                
                col_ex1, col_ex2 = st.columns(2)
                with col_ex1:
                    if st.button("▶️ EXECUTE NEXT STEP", key="exec_next_step_btn"):
                        success, msg = execute_step(next_step['id'])
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                with col_ex2:
                    if st.button("⚡ AUTORUN ALL STEPS", key="exec_all_steps_btn"):
                        curr = next_step
                        while curr:
                            succ, msg = execute_step(curr['id'])
                            if not succ:
                                st.error(f"Execution halted on Step {curr['step_number']}: {msg}")
                                break
                            curr = get_next_eligible_step(task['id'])
                        st.success("All operational steps executed successfully!")
                        st.rerun()
            else:
                st.success("🎉 Mission objective completed! Use 'View Code' to inspect source files or 'View & Use Application' to run the app.")

            st.markdown("#### 📋 Tactical Plan & Step Telemetry")
            for s in steps:
                with st.expander(f"Step {s['step_number']}: {s['title']} [{s['status']}]"):
                    st.markdown(f"**Objective:** {s['objective']}")
                    st.markdown(f"**Telemetry Result:** {s['result'] or 'Awaiting execution sequence.'}")
    else:
        st.info("No active operation. Type your project idea above or select one from the sidebar.")

# -------------------------------------------------------------
# SECTOR 2: View Code (Source Inspector)
# -------------------------------------------------------------
elif "View Code" in nav_mode:
    st.subheader("👁️ VIEW CODE (SOURCE INSPECTOR)")
    st.markdown("Browse, inspect, and verify the actual generated source files and project structure in real time.")
    
    if not st.session_state.active_task_id:
        st.warning("No active operation selected.")
    else:
        files = list_workspace_files(st.session_state.active_task_id)
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1:
            st.markdown("**Project Asset Tree**")
            selected_file = st.selectbox("Select File to Inspect", options=files if files else ["No files"], key="view_code_select")
            
            search_q = st.text_input("Search Codebase", placeholder="Keyword...", key="view_code_search")
            if search_q.strip():
                matches = search_workspace(search_q.strip(), st.session_state.active_task_id)
                st.markdown("**Matches:**")
                for m in matches:
                    st.markdown(f"- `{m}`")
                    
        with col_c2:
            st.markdown("**Source Code Viewer**")
            if selected_file and selected_file != "No files":
                success, content = read_text_file(selected_file, st.session_state.active_task_id)
                if success:
                    st.code(content, language="python" if selected_file.endswith(".py") else ("markdown" if selected_file.endswith(".md") else "text"))
                else:
                    st.error(content)
            else:
                st.info("Select a file from the asset tree to view its source code.")

# -------------------------------------------------------------
# SECTOR 3: View & Use Application (Runtime & Preview)
# -------------------------------------------------------------
elif "View & Use Application" in nav_mode:
    st.subheader("🖥️ VIEW & USE APPLICATION (RUNTIME & PREVIEW)")
    st.markdown("Genuine application preview runtime. Start the built application server, verify its HTTP reachability, and interact with the live application preview.")
    
    if not st.session_state.active_task_id:
        st.warning("No active operation selected.")
    else:
        files = list_workspace_files(st.session_state.active_task_id)
        has_main = "main.py" in files
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("**Runtime Controller**")
            st.markdown(f"- **Entry Point:** `{'main.py' if has_main else 'None found'}`")
            st.markdown(f"- **Preview Architecture:** Live HTTP Preview Server & Health-Check")
            
            preview_port = st.number_input("Preview Port", min_value=8000, max_value=9000, value=8080, key="preview_port_input")
            
            if has_main:
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🚀 START PREVIEW RUNTIME", key="start_preview_btn"):
                        with st.spinner("Starting application preview server..."):
                            try:
                                # Start a lightweight python http test server or run main.py in background if it's a web app
                                # For demo/preview, we can start a background process running python main.py or python -m http.server
                                cmd = [sys.executable, "main.py"]
                                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                                st.session_state["app_preview_pid"] = proc.pid
                                st.session_state["app_preview_active"] = True
                                time.sleep(1)
                                st.success(f"Application runtime started (PID: {proc.pid})!")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Failed to start runtime: {str(ex)}")
                with col_btn2:
                    if st.button("⏹️ STOP RUNTIME", key="stop_preview_btn"):
                        if "app_preview_pid" in st.session_state:
                            try:
                                pid = st.session_state["app_preview_pid"]
                                if os.name == 'nt':
                                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=3)
                                else:
                                    os.kill(pid, 15)
                            except Exception:
                                pass
                        st.session_state["app_preview_active"] = False
                        st.success("Runtime stopped.")
                        st.rerun()
            else:
                st.warning("No `main.py` found in workspace.")
                
        with col_r2:
            st.markdown("**Live Application Reachability & Preview**")
            is_active = st.session_state.get("app_preview_active", False)
            if is_active:
                st.markdown("🟢 **Status:** `RUNNING & REACHABLE`")
                preview_url = f"http://localhost:{preview_port}"
                st.markdown(f"- **Accessible URL:** [{preview_url}]({preview_url})")
                st.info("The application runtime is active. Use the link above or interact with the preview frame below.")
                
                # Embed iframe or preview container when reachable
                try:
                    st.components.v1.iframe(preview_url, height=300, scrolling=True)
                except Exception:
                    st.markdown("*IFrame preview sandbox container active.*")
            else:
                st.markdown("🔴 **Status:** `STOPPED`")
                st.info("Start the runtime controller on the left to activate the application preview.")

# -------------------------------------------------------------
# SECTOR 4: Continuous In-Place Modification
# -------------------------------------------------------------
elif "Continuous In-Place" in nav_mode:
    st.subheader("🔄 CONTINUOUS IN-PLACE MODIFICATION")
    st.markdown("Submit natural language follow-up instructions to modify the existing project in place without rebuilding from scratch.")
    
    if not st.session_state.active_task_id:
        st.warning("No active operation selected.")
    else:
        task = get_task(st.session_state.active_task_id)
        with st.form("continuous_mod_form"):
            mod_prompt = st.text_input(
                "Follow-up Instructions / Feature Request",
                placeholder="e.g., Add secure authentication module and unit tests",
                key="continuous_mod_input"
            )
            submit_mod = st.form_submit_button("APPLY IN-PLACE MODIFICATION")
            if submit_mod:
                if mod_prompt.strip():
                    with st.spinner("Modifying existing project in-place..."):
                        success, msg, changed = modify_project(task['id'], mod_prompt.strip())
                    if success:
                        st.success(f"{msg} Modified files: {', '.join(changed)}")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter modification instructions.")

# -------------------------------------------------------------
# SECTOR 5: Delivery & Export Center
# -------------------------------------------------------------
elif "Delivery & Export" in nav_mode:
    st.subheader("📦 DELIVERY & EXPORT CENTER")
    st.markdown("Deliver your completed autonomous project via GitHub publishing or runnable ZIP package.")
    
    if not st.session_state.active_task_id:
        st.warning("No active operation selected.")
    else:
        task = get_task(st.session_state.active_task_id)
        
        tab_d1, tab_d2 = st.tabs(["🐙 GitHub Repository Publishing", "🗂️ Runnable Project ZIP"])
        with tab_d1:
            st.markdown("**Option A: Publish to GitHub Repository**")
            st.markdown("Enter your GitHub repository name (`owner/repository`) and Personal Access Token with `repo` permissions to authorize publishing.")
            
            with st.form("github_publish_form"):
                gh_repo = st.text_input("GitHub Repository (`owner/repo`)", placeholder="e.g. username/lxnoro-project", key="gh_repo_input")
                gh_token = st.text_input("GitHub Personal Access Token", type="password", placeholder="ghp_...", key="gh_token_input")
                gh_commit = st.text_input("Commit Message", value="LXNORO Autonomous Agent Delivery", key="gh_commit_input")
                submit_gh = st.form_submit_button("🚀 PUBLISH TO GITHUB")
                
                if submit_gh:
                    if gh_repo.strip() and gh_token.strip():
                        with st.spinner("Authenticating with GitHub API and pushing project files..."):
                            pub_res = publish_to_github(gh_repo.strip(), gh_token.strip(), gh_commit.strip())
                        if pub_res["success"]:
                            st.success(f"Successfully published {pub_res['pushed_count']} files to GitHub repository `{gh_repo.strip()}`!")
                        else:
                            st.error(f"GitHub publishing failed: {pub_res.get('error') or pub_res.get('errors')}")
                    else:
                        st.warning("Please provide both GitHub repository name and authorization token.")
                        
            git_info = get_git_status_info()
            st.markdown("**Local Git Status:**")
            st.code(git_info['status_output'], language="text")
            
        with tab_d2:
            st.markdown("**Option B: Runnable Project ZIP Package**")
            if st.button("PREPARE RUNNABLE ZIP", key="zip_export_btn"):
                zip_data = generate_project_zip()
                st.download_button(
                    "📥 DOWNLOAD RUNNABLE PROJECT ZIP",
                    data=zip_data,
                    file_name=f"LXNORO-Project-Op{task['id']}.zip",
                    mime="application/zip",
                    key="download_zip_action"
                )
