# Custom AI Agent with Memory

A voice and text-based intelligent assistant with long-term memory capabilities, leveraging vector databases to recall past interactions and maintain personalized context across sessions.

## Features

- **Long-Term Memory**: Saves and recalls important information from past conversations using a persistent memory store
- **ReAct Architecture**: Uses a reasoning + acting loop for intelligent decision-making
- **User-Scoped Memory**: Memories are scoped per user, enabling personalized interactions
- **Voice Support**: Integrates with OpenAI Whisper for speech-to-text input
- **Configurable Models**: Supports multiple LLM providers (OpenAI, Anthropic Claude)
- **LangGraph Powered**: Built on LangGraph for robust state management and workflow orchestration

## Tech Stack

- **Backend**: Python, LangChain, LangGraph
- **AI**: OpenAI GPT-4, Anthropic Claude, Whisper
- **Memory**: Redis / ChromaDB (vector store)
- **Frontend**: Streamlit / Next.js
- **Testing**: pytest

## Architecture

```
User Input (Text/Voice)
       │
       ▼
┌──────────────┐
│  LangGraph   │
│  ReAct Agent │
│              │
│  ┌────────┐  │    ┌─────────────┐
│  │ Reason │──┼───>│ Memory Tool │
│  │  +Act  │  │    │  (Save/     │
│  └────────┘  │    │   Recall)   │
│              │    └─────────────┘
└──────┬───────┘
       │
       ▼
  AI Response
(with context from
 past conversations)
```

## Getting Started

### Prerequisites

- Python 3.11+
- OpenAI API key (or Anthropic API key)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Rishikesan05/Custom-AI-Agent.git
cd Custom-AI-Agent
```

2. Set up the environment:

```bash
cp .env.example .env
```

3. Add your API keys to `.env`:

```
OPENAI_API_KEY=your-openai-api-key
# OR
ANTHROPIC_API_KEY=your-anthropic-api-key
```

4. Install dependencies:

```bash
pip install -e .
# OR using uv:
uv sync
```

### Running the Agent

```bash
python -m memory_agent
```

Or via LangGraph Studio for a visual interface.

## Configuration

The default model can be configured in `langgraph.json`:

```yaml
model: anthropic/claude-3-5-sonnet-20240620
```

You can change this to any supported model (e.g., `openai/gpt-4`, `openai/gpt-4o`).

## Project Structure

```
├── src/
│   └── memory_agent/
│       ├── __init__.py       # Package initialization
│       ├── graph.py          # LangGraph agent definition
│       ├── state.py          # Agent state management
│       ├── tools.py          # Memory save/recall tools
│       ├── prompts.py        # System prompts
│       ├── context.py        # Context management
│       └── utils.py          # Utility functions
├── tests/
│   ├── unit_tests/           # Unit tests
│   └── integration_tests/    # Integration tests
├── static/                   # Documentation images
├── langgraph.json            # LangGraph configuration
├── pyproject.toml            # Python project config
└── .env.example              # Environment template
```

## Testing

```bash
# Run unit tests
make test

# Run integration tests
make integration_test
```

## How Memory Works

The agent uses a simple but effective memory system:

1. **Save Memory**: When the agent identifies important information (preferences, facts, context), it saves it to a vector store scoped to the user
2. **Recall Memory**: Before responding, the agent searches its memory for relevant past interactions
3. **Context Enrichment**: Retrieved memories are injected into the conversation context, enabling personalized responses
