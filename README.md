# Custom AI Agent with Long-Term Memory

A production-grade conversational AI assistant that **remembers you** across sessions. Unlike standard chatbots that forget everything when you close the tab, this agent stores important facts about you using FAISS vector-based semantic memory and recalls them in future conversations — delivering a personalized, context-aware experience every time.

## What Makes This Different

| Feature | Standard Chatbot | This Agent |
|---------|-----------------|------------|
| Memory | Forgets after session | Remembers across sessions |
| Context | Only current chat | Past conversations + current |
| Personalization | None | Learns your preferences |
| Voice Input | Rarely supported | Built-in speech recognition |
| Multi-Session | Single chat thread | Multiple named conversations |
| Memory Management | No control | Full CRUD (add, view, delete) |
| Theming | Fixed | Obsidian Dark / Studio Light toggle |

## Architecture

```
You speak or type
       │
       ▼
┌──────────────┐     ┌─────────────────┐
│   Gemini AI  │◄────│  FAISS Memory   │
│  (Generate)  │     │  (Recall past   │
│              │     │   interactions) │
└──────┬───────┘     └─────────────────┘
       │                      ▲
       ▼                      │
  AI Response ────────► Extract & Save
  (personalized)        new memories
```

**Memory Flow (RAG-like Pipeline):**
1. User sends a question (text or voice)
2. Agent searches FAISS vector store for semantically relevant past memories
3. Top-K memories are injected into the system prompt as context
4. Gemini 3.5 Flash generates a personalized, grounded response
5. Agent automatically extracts new facts from the exchange and saves them
6. Memory citations are displayed so the user can see what was recalled

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.10+** | Core language |
| **Streamlit** | Web UI framework with custom CSS design system |
| **Google Gemini 3.5 Flash** | LLM for conversation and fact extraction |
| **FAISS** (Meta) | Local vector database for semantic memory |
| **Google Gemini Embedding** | Text-to-vector conversion (`gemini-embedding-2`) |
| **LangChain** | LLM orchestration (messages, prompts, streaming) |
| **SpeechRecognition** | Voice-to-text via Google Web Speech API |

## Features

### Core AI
- **Long-Term Semantic Memory** — Automatically extracts and stores facts about you using FAISS vector similarity search
- **RAG Architecture** — Retrieval-Augmented Generation: recalls relevant memories before generating each response
- **Memory Citations** — Expandable citation chip shows exactly which facts were recalled for each answer
- **Streaming Responses** — Real-time token-by-token response display with latency metrics

### Memory Vault (Full CRUD)
- **Auto-Extract** — AI automatically identifies and saves important facts from conversations
- **Add Custom Facts** — Manually add knowledge to the memory store
- **View & Manage** — Browse all stored facts with indexed listing
- **Individual Delete** — Remove specific facts with one-click deletion and automatic FAISS re-indexing
- **Bulk Reset** — Clear entire memory store when needed

### Multi-Session Chat
- **Named Conversations** — Auto-generated titles from the first user query
- **Session Switching** — Navigate between conversations in the sidebar or bottom dock popover
- **Per-Session Delete** — Remove individual conversation threads
- **Export** — Download any conversation as a clean text file

### Interface
- **Unified Bottom Dock** — Single-line layout: `[+] [Chat Input] [Voice Pill]`
- **Voice Input** — Native microphone recording with speech-to-text transcription
- **Theme Toggle** — Obsidian Dark Mode (`#090d16`) / Studio Light Mode (`#ffffff`)
- **Responsive Design** — Adapts to desktop and mobile viewports
- **GSAP Animations** — Smooth entry animations on page load
- **Material Symbols** — Clean icon system (no emoji)

## Getting Started

### Prerequisites
- Python 3.10+
- Google API Key ([Get one free](https://aistudio.google.com/apikey))

### Installation

```bash
git clone https://github.com/Rishikesan05/Custom-AI-Agent.git
cd Custom-AI-Agent
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env and add your Google API Key:
# GOOGLE_API_KEY=your_key_here
```

### Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Project Structure

```
Custom-AI-Agent/
├── app.py              # Main application (UI, chat logic, CSS design system)
├── memory.py           # FAISS vector memory store (save, recall, delete, clear)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .streamlit/
│   └── config.toml     # Streamlit theme configuration
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## How the Memory System Works

```python
# memory.py provides 4 core operations:

memory.save_memory("User likes Python and AI")   # Add fact to FAISS
memory.recall_memories("favorite language", k=3)  # Semantic search top-3
memory.delete_memory("User likes Python and AI")  # Remove specific fact
memory.clear_memory()                              # Reset entire store
```

- **Embeddings**: Text is converted to dense vectors using `gemini-embedding-2`
- **Similarity Search**: FAISS finds semantically similar memories (not keyword matching)
- **Persistence**: Index is saved to disk (`memory_index/`) and survives app restarts
- **Privacy**: All data stays local — no cloud database required

## License

MIT

## Author

Built by [Rishikesan](https://rishiware.com) | [LinkedIn](https://linkedin.com/in/rishikesan05) | [GitHub](https://github.com/Rishikesan05)
