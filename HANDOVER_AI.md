# ⚓ MDTS: AI Assistant Handover Guide (v2.3)
**Target:** Senior AI Engineer / System Architect
**Date:** 2026-05-11
**Status:** Phase 4 (Remote DB Vitals Sync + RAG/MCP) Completed

---

## 1. 🏗️ System Architecture Overview
The MDTS system is a hybrid Edge-AI medical support platform designed for maritime environments (Offline-first, with Remote DB Sync).

- **Jetson Nano (AI Engine):** 192.168.219.110 (yahboom/yahboom)
  - Runs **Ollama (Llama 3.2 1B)** for medical reasoning.
  - Runs **MobileNetV3** (FastAPI) for wound classification.
  - Hosts the **Vite Dashboard** (Port 5173/5174).
  - Acts as the **ChromaDB (Vector DB)** query client.
- **Raspberry Pi (Data Hub):** 192.168.219.64 (pi/nasong)
  - Hosts **Local MariaDB** for structured patient history.
  - Runs the **Sensor Server (Flask :5000)** for live vitals.
  - Provides **NFS Export** for the Vector DB physical storage (USB Drive).
- **Remote Server (Cloud Hub):** `project-db-campus.smhrd.com:3307`
  - Hosts the **Central MDTS Database**.
  - Source for **Real-time Vitals** (`tb_vital`) used by the dashboard.

---

## 2. 🧠 AI & Knowledge Base (RAG/MCP)

### 2.1. Vector DB (RAG)
- **Path:** `/home/jetson/remote_vector_db` (NFS mounted from RPi USB)
- **Embedding:** `nomic-embed-text` (via Ollama API)
- **Engine:** `MedicalKnowledgeEngine` (`m_medic_knowledge_engine.py`)
- **Key Logic:** Bypasses `torch.load` security issues by using Ollama-native embeddings and ChromaDB direct API.

### 2.2. Relational DBs (MCP Bridge)
- **Local (`tb_patient_history`):** Stores temporal diagnosis trends.
- **Remote (`tb_vital`):** Provides the latest sensor readings from the ship.
- **Integration:** FastAPI fetches both historical context and live vitals to enable "Real-time Trend Reasoning."

### 2.3. Prompt Engineering
The AI receives a four-source context:
1.  **RAG:** Medical procedures from Vector DB.
2.  **History:** Time-series medical records from local MariaDB.
3.  **Real-time:** Live sensor data (HR, BP, SpO2, Temp) from remote DB.
4.  **Situation:** Patient metadata (allergies, chronic diseases).

---

## 3. 🛠️ Critical Dependencies & Fixes
- **Ollama API:** MUST include `"model": "llama3.2:1b"` in all requests.
- **FastAPI Port:** `8000`. Serving `/analyze/chat`, `/analyze/wound`, and `/vitals/live`.
- **Jetson Disk Space:** syslog truncated to free 1.2GB. Monitor `/` partition closely.

---

## 4. 🚀 Current Entry Points
- **Web Dashboard:** `http://192.168.219.110:5173` (Connected to live remote DB)
- **Backend API:** `http://192.168.219.110:8000/vitals/live` (JSON response)
- **PyQt5 GUI:** `python3 ~/main.py` (Local Jetson GUI)

---

## 5. 🚩 Next Tasks
1.  **Obsidian Sync:** Automate markdown-to-vector sync for medical notes.
2.  **Alert System:** Implement push notifications for critical vitals detected in `tb_vital`.
3.  **UI:** Add data visualization for the vital history stored in `tb_patient_history`.

**Handover Signature:** Gemini CLI (Architect)
