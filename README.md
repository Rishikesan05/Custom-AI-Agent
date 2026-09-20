# Custom AI Agent with Long-Term Semantic Memory & Device-Persistent Vaults

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://aiagent-rishiware.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/Orchestration-LangChain%20Core-green)](https://python.langchain.com/)
[![FAISS](https://img.shields.io/badge/Vector%20DB-FAISS%20Index-orange)](https://github.com/facebookresearch/faiss)
[![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini%203.6%20Flash-blue)](https://ai.google.dev/)

A production-grade conversational AI assistant engineered with **persistent semantic memory** and **device-level vault isolation**. While standard chatbots operate with ephemeral context that disappears once a tab is refreshed or closed, this agent autonomously extracts, vectorizes, and indexes user facts into an isolated local **FAISS Vector Store** using **gemini-embedding-2**. On subsequent interactions, it executes high-speed semantic similarity searches to recall relevant memories and augment its prompts—delivering a grounded, personalized experience across multiple sessions.

---

## 🏗️ Architecture Overview

```text
               User Input (Text or Voice)
                           │
                           ▼
                 ┌───────────────────┐
                 │  FAISS Vector DB  │ ◄── gemini-embedding-2 (Sub-millisecond Search)
                 └─────────┬─────────┘
                           │ (Top-K Recalled Facts)
                           ▼
                 ┌───────────────────┐
                 │   System Prompt   │ ◄── Context Augmentation (<memories>)
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Gemini 3.6 Flash  │ ◄── Real-time Token Streaming
                 └─────────┬─────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      Streaming Response         Background Fact Extraction
   (Citation Chip + Latency)     (via Gemini 3.5 Flash Lite)
                                         │
                                         ▼
                             Saved to Isolated Vault Index
                             (memory_index/<vault_id>/)
```

---

## ⚡ Technical Specifications

| Component | Technology | Role & Purpose |
|---|---|---|
| **Primary LLM** | **Google Gemini 3.6 Flash** | Ultra-low latency conversational generation and reasoning |
| **Fallback LLM** | **Google Gemini 3.5 Flash Lite** | High-availability fallback engine & quota-efficient fact extraction |
| **Vector Database** | **FAISS (Meta)** | Local dense vector indexing and sub-millisecond similarity retrieval |
| **Embeddings** | **gemini-embedding-2** | Text-to-dense-vector transformation (768+ dimensions) for semantic mapping |
| **Identity & Vaults** | **Browser `localStorage` Bridge** | Device-persistent, neutral Vault IDs (`user-xxxx`) with zero URL leakage |
| **Voice Interface** | **Web Speech API** | Client-side, zero-latency speech-to-text with animated floating recording dock |
| **Orchestration** | **LangChain Core** | Prompt schemas, structured message pipelines, and vector store integration |
| **Frontend Framework** | **Streamlit + Custom CSS** | Fluid Studio Light design system, mobile-responsive down to 390px |

---

## 🌟 Core Features

### 1. Long-Term Semantic Memory (RAG Pipeline)
- **Autonomous Fact Extraction:** After each conversation turn, the agent evaluates the exchange. If durable personal facts (name, career, preferences, projects) are detected, it extracts and commits them to the vector store.
- **Smart Two-Stage Deduplication:** Prevents duplicate memory accumulation via exact string matching and FAISS vector distance threshold checks ($\le 0.22$). If a fact is already known or paraphrased, it is automatically skipped.
- **Semantic Retrieval:** When queries are submitted, the agent runs cosine similarity against stored vectors. Even if queries share zero identical keywords (e.g., *"What do I do for work?"* matching *"Loves building AI agents"*), the relevant memories are accurately recalled.
- **Citation Transparency:** An expandable citation chip appears above responses, listing precisely which past facts were recalled to generate the answer.

### 2. Device-Persistent Vault & Multi-User Isolation (Zero URL Leakage)
- **Permanent Device Identity:** On first visit, a neutral unique Vault ID (`user-xxxx`) is generated and saved in browser `localStorage`.
- **Reload-Proof Persistence:** Refreshing the browser (F5) or closing and reopening the tab retains the exact same Vault ID and memory ledger.
- **Zero URL Leakage:** The address bar remains 100% clean (`https://aiagent-rishiware.streamlit.app/`), preventing accidental leak of private identifiers.
- **Rename & Migrate:** Users can rename their vault to any custom username (e.g., `alex`, `my-vault`). Past memories are seamlessly migrated without data loss.
- **Cross-Device Connect:** Sync memories from laptop to mobile by entering the target Vault ID and clicking **Connect Vault**.
- **Fresh Vault Creation:** Easily spin up a new clean, isolated memory space with one click on **➕ Create Fresh Vault**.

### 3. Full Memory Vault CRUD Ledger
- **Create:** Manually add custom knowledge facts through the expandable form with instant toast confirmation.
- **Read:** Browse all actively indexed facts in an enumerated visual ledger with fact count badges.
- **Delete:** Remove individual memories with one click. Deleting a fact automatically reconstructs and re-indexes the FAISS store on disk, preventing orphan vectors.
- **Reset All:** Instant global wipe capability for testing or fresh starts.

### 4. Multi-Session Conversational Management
- **ChatGPT-Style Workflow:** Click **New Chat** to start a draft conversation. The thread is only committed to the saved list once messages are exchanged.
- **Auto-Generated Titles:** Automatically creates concise, clean 3-4 word conversation headings based on your opening prompt.
- **Thread Switching & Deletion:** Effortlessly switch between multiple conversations in the sidebar or delete threads with instant cleanup.
- **Export Conversation:** One-click download of the complete chat transcript formatted in clean plain text.

### 5. Expanding Floating Voice Dock
- **Seamless Speech-to-Text:** Voice input is handled natively in the browser via Web Speech API—no audio files uploaded, no server latency.
- **Interactive Morphing:** Clicking the circular mic pill minimizes the text input and expands an animated recording bar with live pulse waves.
- **Dual-Control Actions:** Cancel or send voice inputs with unified grayscale action controls.

### 6. Multi-Model High-Availability Resilience
- **Automated Fallback Chain:** To protect against Google API rate limits (`429`) or server traffic spikes (`503 UNAVAILABLE`), requests dynamically fail over across model endpoints:
  $$\text{Gemini 3.6 Flash} \longrightarrow \text{Gemini 3.5 Flash Lite} \longrightarrow \text{Gemini Flash Latest}$$
- **Polite Service Notices:** If all upstream models are temporarily busy, the interface replaces raw technical exceptions with clean, polite notices and a dedicated **Retry** button.

### 7. Studio Light Design System & Mobile Responsiveness
- **Modern Minimalist Aesthetics:** Custom design tokens (`--surface-1`, `--ink`, `--hairline`) replace default Streamlit styling.
- **Zero Visual Banding:** All bottom bar wrappers feature transparent layering, allowing the floating input dock to rest cleanly on the canvas.
- **Certified Mobile Friendly:** Tested and verified on viewport sizes down to **390px** (iPhone / Android) with zero horizontal scrolling.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- A free **Google Gemini API Key** ([Get your API key](https://aistudio.google.com/apikey))

### 1. Clone the Repository
```bash
git clone https://github.com/Rishikesan05/Custom-AI-Agent.git
cd Custom-AI-Agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the example environment file and add your Google Gemini API key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

### 4. Run the Application
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## ☁️ Streamlit Cloud Deployment

This repository is pre-configured for instant **Streamlit Community Cloud** deployment:

1. Push your code to your GitHub repository.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/).
3. Click **New app**, select your repository, branch (`main`), and main file (`app.py`).
4. Under **Advanced settings &rarr; Secrets**, add your API key:
   ```toml
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```
5. Click **Deploy!** Your agent will be live with full memory isolation, speech input, and persistent vaults!

---

## 📁 Project Structure

```text
Custom-AI-Agent/
├── app.py                     # Main application entry point (UI, Streamlit, JS bridge)
├── memory.py                  # FAISS MemoryStore class (RAG pipeline, CRUD, vault migration)
├── requirements.txt           # Python dependencies (Streamlit, LangChain, FAISS, etc.)
├── .env.example               # Environment template for Gemini API keys
├── .streamlit/
│   └── config.toml            # Studio Light theme tokens & server settings
├── assets/
│   ├── assistant.svg          # Custom SVG avatar for AI Agent
│   └── user.svg               # Custom SVG avatar for User
└── memory_index/              # Isolated directory for local FAISS vector stores
```

---

## 👨‍💻 Author

Developed by **Rishikesan**
- **Portfolio:** [rishiware.com](https://rishiware.com)
- **LinkedIn:** [linkedin.com/in/rishikesan05](https://linkedin.com/in/rishikesan05)
- **GitHub:** [github.com/Rishikesan05](https://github.com/Rishikesan05)
