# ⚓ M-MEDIC: AI Assistant Handover Guide (v2.1)
**Target:** Senior AI Engineer / System Architect
**Date:** 2026-05-11
**Status:** Phase 3 (RAG + MCP + Real-time Sync) Completed

---

## 1. 🏗️ System Architecture Overview
The M-MEDIC system is a hybrid Edge-AI medical support platform designed for maritime environments (Offline-first).

- **Jetson Nano (AI Engine):** 192.168.219.110 (yahboom/yahboom)
  - Runs **Ollama (Llama 3.2 1B)** for medical reasoning.
  - Runs **MobileNetV3** (FastAPI) for wound classification.
  - Hosts the **Vite Dashboard** (Port 5173/5174).
  - Acts as the **ChromaDB (Vector DB)** query client.
- **Raspberry Pi (Data Hub):** 192.168.219.64 (pi/nasong)
  - Hosts **MariaDB (MySQL)** for structured patient history.
  - Runs the **Sensor Server (Flask :5000)** for live vitals.
  - Provides **NFS Export** for the Vector DB physical storage (USB Drive).

---

## 2. 🧠 AI & Knowledge Base (RAG/MCP)

### 2.1. Vector DB (RAG)
- **Path:** `/home/jetson/remote_vector_db` (NFS mounted from RPi USB)
- **Embedding:** `nomic-embed-text` (via Ollama API)
- **Engine:** `MedicalKnowledgeEngine` (`m_medic_knowledge_engine.py`)
- **Key Logic:** Directly uses ChromaDB native API to bypass `torch.load` security restrictions/conflicts.

### 2.2. Relational DB (MCP Bridge)
- **Table:** `MDTS.tb_patient_history`
- **Purpose:** Stores temporal diagnosis and vital trends.
- **Integration:** FastAPI fetches historical context before every AI chat response to enable "Trend-based Reasoning."

### 2.3. Prompt Engineering
The AI receives a multi-source context:
1.  **RAG Context:** Medical procedures extracted from Vector DB.
2.  **MCP Context:** Time-series medical history from MariaDB.
3.  **Real-time Context:** Live vitals passed from the React frontend.

---

## 3. 🛠️ Critical Dependencies & Fixes (MANDATORY READ)
- **FastAPI / Pydantic:** Reinstalled via `pip3 install --upgrade` due to previous environment corruption.
- **Ollama API:** MUST include `"model": "llama3.2:1b"` in all POST requests.
- **CORS:** Enabled in `m_medic_server.py` to allow cross-origin requests from the Windows dev machine.
- **Jetson Disk Space:** Currently at 100% (~1.2GB free). **DO NOT** let logs grow. Truncate `/var/log/syslog` if deployment fails.

---

## 4. 🚀 Current Entry Points
- **Web Dashboard:** `http://192.168.219.110:5173`
- **Backend API:** `http://192.168.219.110:8000/health`
- **Tunnel:** `https://m-medic-dashboard.loca.lt` (npx localtunnel)
- **PyQt5 GUI:** `python3 ~/main.py` (Jetson - X11 Forwarding)

---

## 5. 🚩 Next Tasks for Incoming Assistant
1.  **Obsidian MCP Integration:** Connect the team's Markdown notes to the existing RAG pipeline.
2.  **Sensor Calibration:** Address the MAX30100 IR threshold instability noted in `HANDOFF.md`.
3.  **UI/UX:** Add a "Temporal Graph" in the dashboard visualizing the data from `tb_patient_history`.

**Handover Signature:** Gemini CLI (Architect)
