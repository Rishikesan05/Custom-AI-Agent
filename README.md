# Custom AI Agent with Long-Term Semantic Memory

A production-grade conversational AI agent engineered with **persistent semantic memory**. While standard chatbots operate with ephemeral context that vanishes once a tab is refreshed, this agent autonomously extracts, vectorizes, and indexes user facts into a local **FAISS Vector Store** using **gemini-embedding-2**. On subsequent conversations, it performs semantic similarity search to recall relevant memories and augment its prompts—delivering a grounded, personalized experience across multiple sessions.

---

## Architecture Overview

```text
               User Input (Text or Voice)
                           │
                           ▼
                 ┌───────────────────┐
                 │  FAISS Vector DB  │ ◄── gemini-embedding-2 Semantic Search
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
                                 Saved to FAISS Index
```

---

## Technical Specifications

| Component | Technology | Role & Purpose |
|---|---|---|
| **Primary LLM** | **Google Gemini 3.6 Flash** | Real-time conversational generation and reasoning |
| **Fallback LLM** | **Google Gemini 3.5 Flash Lite** | High-availability fallback engine & quota-efficient fact extraction |
| **Vector Database** | **FAISS (Meta)** | Local high-dimensional semantic indexing and sub-millisecond retrieval |
| **Embeddings** | **gemini-embedding-2** | Text-to-dense-vector transformation for semantic similarity mapping |
| **Voice Interface** | **Google Web Speech API** | Zero-latency client-side speech-to-text transcription |
| **Orchestration** | **LangChain Core** | Prompt schemas, structured message pipelines, and vector store integration |
| **Frontend Framework** | **Streamlit + Custom CSS** | Fluid Studio Light design system, mobile-responsive down to 390px |

---

## Key Features

### 1. Long-Term Semantic Memory (RAG Pipeline)
- **Automatic Fact Learning:** After each interaction, the agent analyzes the turn and extracts durable personal facts (name, career, preferences, projects) without user intervention.
- **Semantic Retrieval:** When queries are submitted, the agent runs cosine similarity against stored vectors. Even if queries share zero identical keywords (e.g. *"What do I do for work?"* matching *"Loves building AI agents"*), the relevant memories are accurately recalled.
- **Citation Transparency:** An expandable citation chip appears above responses, listing precisely which past facts were recalled to generate the answer.

### 2. Full Memory Vault CRUD
- **Create:** Manually add custom knowledge facts through the expandable form with instant feedback.
- **Read:** Browse all actively indexed facts in an enumerated visual ledger.
- **Delete:** Remove individual memories with one click. Deleting a fact automatically reconstructs and re-indexes the FAISS store on disk, preventing orphan vectors.

### 3. Multi-Session Conversational Management
- **ChatGPT-Style Workflow:** Click **New Chat** to start a draft conversation. The chat is only committed to the saved list once messages are exchanged.
- **Auto-Generated Titles:** Automatically creates concise, clean 3-4 word conversation headings based on your opening prompt.
- **Thread Switching & Deletion:** Effortlessly switch between multiple conversations in the sidebar or delete threads with instant cleanup.

### 4. Expanding Floating Voice Dock
- **Seamless Speech-to-Text:** Voice input is handled natively in the browser via Web Speech API—no audio files uploaded, no server latency.
- **Interactive Morphing:** Clicking the circular mic pill minimizes the text input and expands an animated recording bar with live pulse waves.
- **Dual-Control Actions:** Cancel or send voice inputs with unified grayscale action controls.

### 5. Multi-Model High-Availability Resilience
- **Automated Fallback Chain:** To protect against Google API rate limits (`429`) or server traffic spikes (`503 UNAVAILABLE`), requests dynamically fail over across model endpoints:
  $$\text{Gemini 3.6 Flash} \longrightarrow \text{Gemini 3.5 Flash Lite} \longrightarrow \text{Gemini Flash Latest}$$
- **Polite Service Notices:** If all upstream models are temporarily busy, the interface replaces raw technical exceptions with clean, polite notices and a dedicated **Retry** button.

### 6. Studio Light Design System & Mobile Responsiveness
- **Modern Minimalist Aesthetics:** Custom design tokens (`--surface-1`, `--ink`, `--hairline`) replace default Streamlit styling.
- **Zero Visual Banding:** All bottom bar wrappers feature transparent layering, allowing the floating input dock to rest cleanly on the canvas.
- **Certified Mobile Friendly:** Tested and verified on viewport sizes down to **390px** (iPhone / Android) with zero horizontal scrolling.

---

## Getting Started

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

## Project Structure

```text
Custom-AI-Agent/
├── app.py                  # Main application: Streamlit UI, multi-session logic, CSS design system
├── memory.py               # MemoryStore class: FAISS vector database integration & CRUD
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment template for GEMINI_API_KEY
├── .gitignore              # Git ignore rules (protects .env and memory_index)
├── assets/                 # Brand SVG icon assets
│   ├── assistant.svg       # Custom AI Agent brand logo avatar
│   └── user.svg            # Grayscale user avatar
└── memory_index/           # Local FAISS index files (created on runtime)
    ├── index.faiss         # Serialized vector embeddings
    └── index.pkl           # Document store metadata mapping
```

---

## Architectural Decisions

### Why FAISS over Cloud Vector Databases?
1. **Zero Latency:** FAISS executes in-process on the local machine with sub-millisecond similarity calculations.
2. **Privacy-First:** User memories never leave your machine to third-party vector clouds.
3. **Model-Agnostic Abstraction:** Built on LangChain's vector store interfaces, allowing effortless migration to Pinecone, Qdrant, or Chroma by modifying a single file (`memory.py`).

### Why RAG over Model Fine-Tuning?
- **Real-Time Updates:** New facts become immediately retrievable on the very next turn without fine-tuning delay.
- **Full Erasability:** Complies with privacy requirements—deleting a memory permanently removes it from the vector index instantly.
- **Zero Hallucination:** Memories are explicitly supplied in context tags, ensuring verifiable, grounded responses.

---

## Author

Developed by **Rishikesan**
- GitHub: [@Rishikesan05](https://github.com/Rishikesan05)
- Repository: [Custom-AI-Agent](https://github.com/Rishikesan05/Custom-AI-Agent)

---

## License

This project is open-source and available under the [MIT License](LICENSE).
