# Custom AI Agent with Long-Term Semantic Memory & Device-Persistent Vaults

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://aiagent-rishiware.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/Orchestration-LangChain%20Core-green)](https://python.langchain.com/)
[![FAISS](https://img.shields.io/badge/Vector%20DB-FAISS%20Index-orange)](https://github.com/facebookresearch/faiss)
[![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini%203.6%20Flash-blue)](https://ai.google.dev/)
[![Mobile Responsive](https://img.shields.io/badge/Mobile-86vw%20Native%20Drawer-purple)](#-mobile-responsiveness--studio-light-design-system)

A production-grade conversational AI assistant engineered with **persistent semantic memory**, **two-stage smart deduplication**, and **device-level vault isolation**. While conventional chatbots operate on ephemeral context that vanishes the moment a browser tab is closed, this agent autonomously extracts, vectorizes, and indexes user facts into an isolated local **FAISS Vector Store** using **gemini-embedding-2**. 

On subsequent interactions, the agent executes sub-millisecond semantic similarity searches to recall relevant facts and augment its system prompts—delivering a permanently personalized, grounded conversation across sessions. To guarantee privacy on shared cloud servers (e.g., Streamlit Cloud), the system implements a **client-side `localStorage` vault bridge** that delivers multi-user isolation with **zero URL credential leakage**.

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
                 │   System Prompt   │ ◄── Augmented Context (<memories>)
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Gemini 3.6 Flash  │ ◄── Real-time Token Streaming
                 └─────────┬─────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      Streaming Response         Context-Aware Fact Extraction
   (Citation Chip + Latency)     (Lightweight Flash Lite Model)
                                         │
                                         ▼
                                 [Two-Stage Deduplication]
                                 • Stage 1: Extraction Prompt Filter
                                 • Stage 2: FAISS L2 Distance <= 0.22
                                         │
                                         ▼
                             Saved to Isolated Vault Index
                             (memory_index/<vault_id>/)
```

---

## ⚡ Technical Specifications

| Component | Technology | Role & Purpose |
|---|---|---|
| **Primary LLM** | **Google Gemini 3.6 Flash** | Ultra-low latency conversational generation and complex reasoning |
| **Fallback LLM** | **Google Gemini 3.5 Flash Lite** | High-availability fallback engine & quota-efficient fact extraction |
| **Vector Database** | **FAISS (Meta)** | Local dense vector indexing and sub-millisecond L2 similarity retrieval |
| **Embeddings** | **gemini-embedding-2** | 768+ dimensional vector transformations capturing semantic proximity |
| **Identity & Vaults** | **Browser `localStorage` Bridge** | Device-persistent, neutral Vault IDs (`user-xxxx`) with zero URL leakage |
| **Deduplication** | **Two-Stage Deduplication Engine** | Known-memory prompt awareness + FAISS vector distance filter ($\le 0.22$) |
| **Voice Interface** | **Web Speech API** | Client-side, zero-latency speech-to-text with morphing voice dock |
| **Orchestration** | **LangChain Core** | Prompt schemas, structured message pipelines, and vector store integration |
| **Frontend Framework** | **Streamlit + Custom CSS** | Fluid Studio Light aesthetic, 86vw mobile drawer, 40px circular trigger |

---

## 🌟 Core Features

### 1. Long-Term Semantic Memory (RAG Pipeline)
- **Autonomous Fact Extraction:** After each conversation turn, the agent analyzes the exchange. If durable personal facts (name, career, tech stack, preferences) are stated, it extracts and commits them to the vector store.
- **Sub-Millisecond Semantic Retrieval:** On each prompt, FAISS computes vector similarity against stored memories. Even if the user's prompt shares zero identical keywords (e.g., *"What is my tech stack?"* matching *"User builds with Python and FastAPI"*), the relevant memories are retrieved.
- **Citation Transparency:** Whenever past memories are utilized to formulate an answer, an expandable **Citation Chip** appears directly above the response, displaying the exact recalled facts and generation latency.

### 2. Two-Stage Smart Memory Deduplication
- **Stage 1: Context-Aware Prompt Filter:** The extraction prompt dynamically receives all active memories for the user. If an incoming statement is already known, the model returns `NONE`, conserving token usage.
- **Stage 2: FAISS L2 Distance Semantic Filter:** Before committing vectors to disk, `MemoryStore.save_memory()` runs an L2 Euclidean distance check against existing vectors. With a threshold of $\text{distance} \le 0.22$ (equivalent to $> 97.5\%$ cosine similarity), paraphrased repetitions (e.g., *"I work as a Python engineer"* vs *"I am a Python developer"*) are automatically discarded, preventing memory bloat.

### 3. Device-Persistent Vaults (Zero URL Leakage)
- **Permanent Device Identity:** On first visit, a neutral unique Vault ID (`user-xxxx`) is generated and securely saved in the browser's `localStorage`.
- **Reload-Proof:** Full page refreshes (F5) or closing and reopening browser tabs maintain the exact same Vault ID and memory ledger.
- **Zero URL Leakage:** The browser address bar remains clean (`https://aiagent-rishiware.streamlit.app/`). Private identifiers are never exposed in the URL, preventing credential hijacking via copy-pasted links.
- **Cross-Device Connect:** Seamlessly sync your personal vault across devices by inputting your target Vault ID and clicking **Connect**.

### 4. Single-Row Compact Vault Switcher & Inline Renaming
- **All-in-One Compact Header:** A unified, space-efficient control row:
  - Row 1: `Vault: <active_id>` badge with inline `[✏️]` (single-click popover/expander for rename) and `[➕]` (create fresh vault).
  - Row 2: Streamlined `[ Connect to Vault ID... ] [ 🔗 ]` pair.
- **Atomic Index Renaming:** Renaming a vault atomically copies `index.faiss` and `index.pkl` to the new target folder on disk, guaranteeing zero data loss.

### 5. Full Memory Vault CRUD Ledger
- **Create:** Manually add custom knowledge facts through the expandable form with instant toast confirmation.
- **Read:** Browse all actively indexed facts in an enumerated visual ledger with live count badges.
- **Delete:** Remove individual memories with one click. Deleting a fact automatically reconstructs and re-indexes the FAISS store on disk, preventing orphan vectors.
- **Reset All:** Instant global wipe capability for testing or fresh starts.

### 6. Multi-Session Conversational Management
- **ChatGPT-Style Workflow:** Click **New Chat** to initialize a draft session. The thread is only committed to the saved list once messages are exchanged.
- **Auto-Generated Titles:** Concise 3-4 word conversation headings are autonomously generated from the user's opening prompt.
- **Thread Switching & Deletion:** Switch between saved conversations or delete individual threads with instant memory garbage collection.
- **Export Conversation:** One-click download of the complete chat transcript formatted in clean plain text.

### 7. Expanding Floating Voice Dock
- **In-Browser Speech-to-Text:** Powered natively by the browser's Web Speech API—no audio files uploaded, zero server latency, and no third-party audio costs.
- **Interactive Morphing:** Clicking the circular mic pill smoothly minimizes the text input and expands an animated recording bar with live pulse waves.
- **Dual-Control Actions:** Cancel or send voice inputs with unified grayscale action controls.

### 8. Multi-Model High-Availability Resilience
- **Automated Fallback Chain:** To protect against Google API rate limits (`429`) or server traffic spikes (`503 UNAVAILABLE`), requests dynamically fail over across model endpoints:
  $$\text{Gemini 3.6 Flash} \longrightarrow \text{Gemini 3.5 Flash Lite} \longrightarrow \text{Gemini Flash Latest}$$
- **Polite Service Notices:** If all upstream models are temporarily busy, the interface replaces raw technical exceptions with clean, polite notices and a dedicated **Retry** button.

### 9. Mobile Responsiveness & Studio Light Design System
- **86vw Native Slide Drawer:** On mobile viewports (down to 390px), the sidebar transforms into an off-canvas drawer with smooth backdrop blur and soft shadow.
- **Dynamic Container Sizing:** Automatically applies unconstrained auto-height for $\le 4$ conversations, eliminating the 140px empty white void bug common in default Streamlit layouts.
- **Circular Floating Hamburger:** Replaced the desktop pill with a 40px circular floating trigger at top-left.
- **Zero Horizontal Overflow:** All horizontal layouts strictly enforce flex-nowrap to prevent action buttons from breaking into multi-line wraps.

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

### 2. Set Up a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment template and add your Google Gemini API key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

### 5. Run the Application
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
├── app.py                     # Main application entry point (UI, Streamlit, JS bridge, CSS)
├── memory.py                  # FAISS MemoryStore class (RAG pipeline, deduplication, CRUD)
├── requirements.txt           # Python dependencies (Streamlit, LangChain, FAISS, etc.)
├── .env.example               # Environment template for Gemini API keys
├── .streamlit/
│   └── config.toml            # Studio Light theme tokens & server settings
├── assets/
│   ├── assistant.svg          # Custom SVG avatar for AI Agent
│   └── user.svg               # Custom SVG avatar for User
└── memory_index/              # Isolated directory for local FAISS vector stores (git-ignored)
```

---

## 👨‍💻 Author

Developed by **Rishikesan**
- **Portfolio:** [rishiware.com](https://rishiware.com)
- **LinkedIn:** [linkedin.com/in/rishikesan05](https://linkedin.com/in/rishikesan05)
- **GitHub:** [github.com/Rishikesan05](https://github.com/Rishikesan05)
