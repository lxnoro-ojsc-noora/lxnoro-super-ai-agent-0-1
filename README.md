# LXNORO Super AI Agent — Autonomous Software Development Pipeline

Copyright (c) 2026 NOORA AL-MAOLAI — LXNORO OJSC. Licensed under the [MIT License](LICENSE).

---

## 1. Project Name and Overview
**LXNORO Super AI Agent** is a fully verified, end-to-end autonomous software development pipeline and cyber-command conversational interface built with Streamlit and powered by the Nebius Token Factory AI inference platform. It enables users to describe software project ideas in natural language, orchestrates dynamic execution plans stored in SQLite (`agent_memory.db`), executes code generation via live model calls, and delivers production-ready projects through source inspection, in-place modification, and runnable ZIP package export.

## 2. Problem Being Addressed
Building full-stack software applications from natural language prompts usually requires complex technical setup, manual dependency resolution, and deep boilerplate coding. Ordinary users lack streamlined interfaces to orchestrate high-performance open-weights AI models for multi-step software creation, code inspection, and secure repository delivery without exposing sensitive credentials.

## 3. Product Vision and Objectives
- **Zero-Setup Natural Language Interface:** Enable conversational software creation without asking end users for API keys or complex configuration.
- **Robust Autonomous Orchestration:** Translate natural language requirements into structured, dependency-aware execution plans.
- **Verified Live AI Provider Integration:** Connect directly to high-performance open-weights models hosted on Nebius Token Factory with proven live inference responses.
- **Secure Credential Handling:** Resolve server-side credentials exclusively via Streamlit Secrets (`st.secrets["NEBIUS_API_KEY"]`).
- **Verifiable Delivery & Export:** Support GitHub repository publishing and runnable ZIP package exports.

## 4. Core Capabilities and Workflow
1. **Conversational AI & Planning (`app.py` + `agent_memory.py`):** Chat interface to submit requirements and initialize multi-step project tasks.
2. **Autonomous Execution Engine (`execution_engine.py`):** Iterative step execution with prerequisite validation, retry logic, and error telemetry.
3. **Source Inspector (`workspace_tools.py`):** Safe file tree traversal and code viewing.
4. **Application Runtime Preview (`app.py`):** Python HTTP server controller and native React-error-free rendering cards.
5. **Continuous In-Place Modification (`agent_memory.py`):** Modify existing projects via follow-up natural language instructions.
6. **Delivery & Export Center (`delivery_utils.py`):** Local git status inspection, GitHub repository publishing, and ZIP archive generation and download.

## 5. AI Architecture and Nebius Token Factory Integration
The application interfaces with the Nebius Token Factory OpenAI-compatible API (`https://api.tokenfactory.nebius.com/v1/chat/completions`) using secure Bearer token authentication (`NEBIUS_API_KEY`). Live inference calls have been successfully executed and verified for both required models.

## 6. Supported & Verified Models
- **NVIDIA Nemotron 3 Super 120B:** `nvidia/nemotron-3-super-120b-a12b` (Live inference verified)
- **DeepSeek V4.1 Flash 1017:** `deepseek/deepseek-v4.1-flash-1017` (Live inference verified)

## 7. Server-Side Streamlit Secrets Configuration
Credentials are read directly from server-side Streamlit secrets (`st.secrets["NEBIUS_API_KEY"]`) or environment variables (`NEBIUS_API_KEY`), ensuring keys are never exposed in source code or client bundles.

## 8. Project Generation and Execution Architecture
- Projects are generated into an isolated local workspace directory backed by SQLite (`data/agent_memory.db`).
- Code files and documentation (e.g., `README.md`, `requirements.txt`, `main.py`, `module_*.py`) are created via validated workspace tools.

## 9. Runtime and Application Preview Mechanism
- **Local Runtime:** The application controller spawns local Python subprocesses (`main.py`) serving HTTP on port 8080.
- **Preview Mechanism:** Native rendering cards and direct download mechanisms provide robust, browser-accessible previews and complete ZIP packaging without React DOM unmount exceptions.

## 10. Technology Stack
- **Frontend / HUD:** Streamlit (Python) with custom futuristic cyber-command dark UI styling.
- **AI Backend:** Nebius Token Factory API (`requests`).
- **Database & State:** SQLite (`agent_memory.db`).
- **Delivery:** GitPython / PyGithub integrations, Python `zipfile`.

## 11. Installation and Deployment Instructions
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your Streamlit secrets (`.streamlit/secrets.toml`) or environment variables:
   ```toml
   NEBIUS_API_KEY = "your_nebius_api_key_here"
   NEBIUS_MODEL = "nvidia/nemotron-3-super-120b-a12b"
   ```
4. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

## 12. Required Environment Variables and Secrets
- `NEBIUS_API_KEY`: Required for live Nebius AI inference.
- `NEBIUS_MODEL`: Optional model identifier override.

## 13. Repository Structure
```text
├── .env.example
├── .gitignore
├── agent_memory.py
├── app.py
├── DELIVERY_REPORT.md
├── delivery_utils.py
├── execution_engine.py
├── GEMINI.md
├── HACKATHON_SUBMISSION.md
├── LICENSE
├── main.py
├── module_2.py
├── module_3.py
├── nebius_client.py
├── orchestration_engine.py
├── README.md
├── requirements.txt
├── test_delivery.py
├── test_execution_engine.py
├── test_long_term_memory.py
├── test_nebius_client.py
├── test_orchestration.py
├── test_workspace_tools.py
├── workspace_tools.py
└── data/
    └── agent_memory.db
```

## 14. Current Implementation Status & Verified Results
- **Status:** Fully implemented, verified, and operational end-to-end.
- **Evidence:** Successful live model invocations and responses recorded for both NVIDIA Nemotron and DeepSeek Flash; generated application workflows, ZIP packaging, and downloads fully tested and documented with operator screenshots and videos.

## 15. Security and Credential-Handling Notes
Credentials are never logged, printed, or committed to version control. `st.secrets` is treated as a read-only configuration source.

## 16. License
Copyright (c) 2026 NOORA AL-MAOLAI — LXNORO OJSC. Licensed under the [MIT License](LICENSE).
