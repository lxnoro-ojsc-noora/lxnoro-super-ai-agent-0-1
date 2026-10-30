# LXNORO Super AI Agent — Project Instructions & Architecture

## Core Product Goal
LXNORO Super AI Agent is an **End-to-End Autonomous Software Development Pipeline**.
1. **Natural Language Conversational Interface:** Users describe project ideas in natural language. Zero API keys or technical setup requested from ordinary users. Owner credentials resolved server-side from `st.secrets` / environment variables.
2. **Autonomous Planning:** Live AI model (Nemotron via Nebius) analyzes requirements, generates dynamic dependency-aware execution plans, and persists state in SQLite (`agent_memory.db`).
3. **Real Autonomous Development:** Independent creation of project structure, source files, backend/frontend code, and dependency resolution.
4. **Two Working Preview Actions:**
   - **View Code:** Source file explorer and code viewer.
   - **View Application:** Live running HTTP application runtime preview with reachable preview URL and interactive iframe container.
5. **Continuous In-Place Modification:** Natural language follow-up instructions modifying the existing project in-place without rebuilding from scratch.
6. **Real Verification & Delivery:** GitHub repository publishing with user token authorization and runnable ZIP package export.
