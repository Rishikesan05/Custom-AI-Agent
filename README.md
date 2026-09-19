# Custom AI Agent with Long-Term Memory

A conversational AI assistant that **remembers you** across sessions. Unlike standard chatbots that forget everything when you close the tab, this agent stores important facts about you using vector-based semantic memory and recalls them in future conversations.

## What Makes This Different

| Feature | Standard Chatbot | This Agent |
|---------|-----------------|------------|
| Memory | Forgets after session | Remembers across sessions |
| Context | Only current chat | Past conversations + current |
| Personalization | None | Learns your preferences |
| Voice Input | Rarely supported | Built-in speech recognition |

## How It Works

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

**Memory Flow:**
1. You ask a question
2. Agent searches FAISS vector store for relevant past memories
3. Relevant memories are injected into the AI prompt as context
4. Gemini generates a personalized response
5. Agent automatically extracts new facts about you and saves them

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python** | Core language |
| **Streamlit** | Web UI framework |
| **Google Gemini 3.5 Flash** | LLM for conversation |
| **FAISS** (Facebook AI Similarity Search) | Vector database for memory |
| **Google Gemini Embedding** | Text → vector conversion |
| **LangChain** | LLM orchestration framework |
| **SpeechRecognition** | Voice → text conversion |

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
# Edit .env and add your Google API Key
```

### Run

```bash
streamlit run app.py
```

## Project Structure

```
Custom-AI-Agent/
├── app.py              # Main Streamlit application (UI + chat logic)
├── memory.py           # FAISS-based long-term memory store
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Features

- **🧠 Long-Term Memory** — Automatically extracts and stores facts about users
- **🔍 Semantic Recall** — Uses vector similarity to find relevant past memories
- **🎙️ Voice Input** — Speak to the agent using your microphone
- **⚡ Streaming Responses** — Real-time token-by-token response display
- **📥 Export Chat** — Download conversation as clean, human-readable text
- **🗑️ Clear Chat** — Reset conversation with one click
- **⚠️ Error Handling** — Graceful handling of rate limits and API errors

## License

MIT

## Author

Built by [Rishikesan](https://rishiware.com)
