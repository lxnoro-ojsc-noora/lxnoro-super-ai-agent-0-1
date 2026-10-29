# LXNORO Super AI Agent 0-1

An autonomous Streamlit Community Cloud AI Agent designed for robust multi-step execution, workspace management, and dual delivery options (GitHub & ZIP).

## 🚀 Quick Start & Launch

1. **Clone or open the repository** in your local workspace or Streamlit Community Cloud.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables**:
   Copy `.env.example` to `.env` and add your API credentials:
   ```bash
   cp .env.example .env
   ```
4. **Launch the Streamlit App**:
   ```bash
   streamlit run app.py
   ```

---

## 🗺️ Phased Implementation Roadmap

- **Phase 1**: Foundation, Streamlit App (`app.py`), Dependency Manifest (`requirements.txt`), `.gitignore`, `.env.example`, and README with Roadmap. ✅
- **Phase 2**: SQLite Persistent Task Memory & Dynamic 1–50 Step Plan Engine. ✅
- **Phase 3**: Safe Workspace Tools (Inspection, File Editor, Search, Audit, Strict Command Runner). ✅
- **Phase 4**: Execution & Recovery Engine (Resumable Steps, Retries, Validation). ✅
- **Phase 5**: Dual Delivery Center (GitHub Delivery & Secure ZIP Archive Export). ✅
- **Phase 6 (Current)**: Nebius Token Factory + NVIDIA Nemotron Integration (OpenAI-compatible API, Chat Completions, Playground, Mocked Tests). ✅

---

## 🧠 Phase 2: Persistent Task Memory & Dynamic Plan Engine
- **SQLite Persistence**: Stored under `./data/agent_memory.db`. Note: Local Community Cloud storage is ephemeral and may not persist across restarts/redeployments.
- **Dynamic Plans**: Create tasks with 1 to 50 steps using a deterministic plan generator.
- **Dependency Enforcement**: Prerequisites must be completed before subsequent steps can be marked in progress or completed.
- **Operational Memory Logs**: Concise factual history of actions, results, and updates.

---

## 🛠️ Phase 3: Safe Workspace Tools & Security Constraints
- **Workspace Inspection & Search**: List files, inspect metadata, read bounded text files (<500KB), and search filenames/content.
- **Safe File Editing**: Create/update text files with strict path validation. Rejects absolute paths, path traversal (`..`), symlinks escaping workspace, and protected paths (`.env`, `.git`, `data/`, `__pycache__`).
- **Strict Command Runner**: Default disabled. Restricts execution to a pre-approved diagnostic allowlist (`git status`, `git diff`, `pytest`, `python -m py_compile ...`). Includes timeout (10s) and captured exit status.
- **Audited Operations**: Every tool operation is logged to the operational memory database with timestamps, target paths, and success/failure summaries.

---

## ⚡ Phase 4: Execution & Recovery Engine
- **Resumable Steps & States**: Tracks explicit execution states (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `BLOCKED`).
- **Startup Recovery**: Automatically reconciles interrupted `RUNNING` steps after an app restart, safely setting them to `PENDING` (or `FAILED` if retry limits are reached).
- **Bounded Retries**: Recoverable failures allow up to 3 retries (`MAX_RETRIES = 3`), recording attempt counts and results in operational memory.
- **Deterministic Tool Actions**: Maps steps to safe workspace tool operations (file listing, workspace searching, and allowlisted command compilation checks).
- **User-Triggered Control**: Users explicitly trigger execution via "Run Next Eligible Step" or individual step execution buttons in the Streamlit UI.

---

## 📦 Phase 5: Dual Delivery Center
- **Option A — GitHub Delivery**: Inspects local Git repository status (branch, remote, working tree status) and provides precise local Git workflow commands. Pushes and commits are never executed automatically.
- **Option B — ZIP Archive Delivery**: Generates a clean production-ready ZIP archive on the fly (`st.download_button`) containing all source code and documentation while strictly excluding secrets (`.env`), database files (`data/`), caches (`__pycache__`), and virtual environments.
- **Streamlit Community Cloud Limitation**: Local filesystem storage is ephemeral; users should download the portable ZIP copy as a reliable backup.

---

## ⚡ Phase 6: Nebius Token Factory + NVIDIA Nemotron Integration
- **OpenAI-Compatible API Client**: Connects to Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`) supporting chat completions.
- **Secure Credential Handling**: Reads API keys exclusively from `NEBIUS_API_KEY` with strict error handling, ensuring keys are never logged or exposed in errors/UI.
- **Configurable Model**: Defaults to `nvidia/nemotron-3-super-120b-a12b`, configurable via `NEBIUS_MODEL`.
- **Interactive Playground**: Integrated into the Streamlit workflow (`⚡ Nebius & Nemotron` tab and sidebar status) for prompt testing and raw JSON response inspection.
- **Mocked Testing**: Fully tested using offline unit tests (`test_nebius_client.py`) covering success, missing credentials, HTTP errors, timeouts, and malformed responses.
