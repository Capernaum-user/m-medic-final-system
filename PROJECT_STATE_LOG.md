# ⚓ MDTS Project: Technical State & Implementation Log
**Last Updated:** 2026-05-11
**Status:** AI Integration Active, Hybrid Vector DB Established

---

## 1. 🖥️ Hardware & Connection Matrix

| Device | Internal IP | External/Gateway IP | ID / PW | Key Role |
| :--- | :--- | :--- | :--- | :--- |
| **Jetson Nano** | `192.168.10.2` | `192.168.219.110` | `jetson` / `yahboom` | AI Inference, Dashboard Host, GUI |
| **Raspberry Pi** | `192.168.10.1` | `192.168.219.64` | `pi` / `nasong` | MariaDB, Sensor Server, USB Storage |

---

## 2. 🧠 AI System Architecture

### 2.1. Inference Engines (Jetson Nano)
- **Ollama (LLM):** `llama3.2:1b` (Active on port 11434).
- **Vision (Wound Classification):** MobileNetV3 Large (Standard).
- **Backend Server:** FastAPI (`m_medic_server.py`) on port 8000.
  - *Patch:* API requests now specify the model name explicitly.
  - *Patch:* `GATEWAY_IP` set to `127.0.0.1` for local Ollama usage.

### 2.2. User Interfaces
- **PyQt5 GUI:** `~/main.py` (Jetson Nano). 
  - Integrated with live AI wound analysis and Ollama medical advice.
  - Sensor polling remains connected to Raspberry Pi (`:5000/vitals`).
- **Web Dashboard:** Vite/React on port 5173.
  - *Critical Fix:* Frontend now dynamically detects Jetson Nano's IP for API calls (`window.location.hostname`).
  - *Tunnel:* [https://m-medic-dashboard.loca.lt](https://m-medic-dashboard.loca.lt)

---

## 3. 🗄️ Database & Storage Strategy

### 3.1. Relational DB (MariaDB)
- **Host:** Raspberry Pi (`192.168.219.64`)
- **Credentials:** `mdts` / `12345`
- **DB Name:** `MDTS`

### 3.2. Hybrid Vector DB (ChromaDB)
- **Physical Storage:** Raspberry Pi USB Drive (`/media/pi/5391-20791/m_medic_vector_db`).
- **Access Method:** Shared via **NFS** to Jetson Nano.
- **Mount Point (Jetson):** `~/remote_vector_db`.
- **Logic:** Jetson Nano runs the ChromaDB client/engine for performance, while data is persisted on the RPi's high-capacity USB.

---

## 4. 🛠️ Recent Critical Fixes (2026-05-11)
1. **Dependency Repair:** Reinstalled broken `fastapi`, `uvicorn`, `pydantic`, and `annotated-doc` libraries on Jetson Nano.
2. **AI Protocol Sync:** Fixed Ollama API calls to include mandatory `model` parameter.
3. **Network Transparency:** Replaced hardcoded RPi IPs in frontend code with dynamic hostname detection to allow seamless access from Windows PCs.
4. **Storage Integration:** Configured NFS between RPi and Jetson for remote Vector DB hosting.

---

## 5. 🚀 Future Roadmap
- [ ] **RAG Implementation:** Populate `medical_docs_v2` collection with maritime medical guidelines.
- [ ] **Obsidian MCP Integration:** Connect external knowledge base via MCP protocol.
- [ ] **Sensor Stability:** Improve MAX30100 IR threshold monitoring.

---
**Note:** This document serves as a "Source of Truth" for system re-initialization.
