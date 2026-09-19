import streamlit as st
import time
from dotenv import load_dotenv
import speech_recognition as sr
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from memory import MemoryStore

load_dotenv()

st.set_page_config(
    page_title="AI Agent",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS Design System ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&family=Roboto+Mono:wght@400;500&display=swap');
    
    :root {
        --bg-color: #ffffff;
        --card-bg: #f8f9fa;
        --text-main: #1f2937;
        --text-muted: #6b7280;
        --accent: #2563eb;
        --accent-hover: #1d4ed8;
        --border: #e5e7eb;
        --user-msg: #f3f4f6;
        --ai-msg: #ffffff;
    }
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: var(--bg-color);
        color: var(--text-main);
    }
    
    .stApp {
        max-width: 900px;
        margin: 0 auto;
    }
    
    .header-container {
        text-align: center;
        padding: 40px 0 20px 0;
        animation: fadeInDown 0.8s ease-out;
    }
    
    .main-title {
        font-weight: 600;
        font-size: 2.5rem;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #1f2937, #4b5563);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    
    .sub-title {
        color: var(--text-muted);
        font-size: 1.1rem;
        font-weight: 300;
    }
    
    .memory-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #ecfdf5;
        color: #059669;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        border: 1px solid #d1fae5;
        margin-top: 15px;
    }
    
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── JS to remove '· Streamlit' suffix from title ──
import streamlit.components.v1 as components
components.html(
    """
    <script>
        const target = window.parent.document.querySelector('title');
        if(target) {
            target.innerText = "Custom AI Agent";
            const observer = new MutationObserver(() => {
                if (target.innerText !== "Custom AI Agent") {
                    target.innerText = "Custom AI Agent";
                }
            });
            observer.observe(target, { childList: true, characterData: true, subtree: true });
        }
    </script>
    """,
    height=0,
    width=0,
)

# ── Initialize State ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory_store" not in st.session_state:
    st.session_state.memory_store = MemoryStore()

# ── Header ──
st.markdown("""
<div class="header-container">
    <div class="main-title">Custom AI Agent</div>
    <div class="sub-title">A smart assistant with long-term memory & voice capabilities.</div>
    <div class="memory-badge">🧠 Memory Active</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Audio Processing ──
def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    try:
        # st.audio_input returns a BytesIO object (wav file format)
        with sr.AudioFile(audio_bytes) as source:
            audio = r.record(source)
        text = r.recognize_google(audio)
        return text
    except Exception as e:
        return f"Error transcribing audio: {e}"

audio_val = st.audio_input("Or speak to the agent", label_visibility="collapsed")
voice_query = None
if audio_val and "last_audio" not in st.session_state or st.session_state.get("last_audio") != audio_val:
    with st.spinner("Transcribing..."):
        voice_query = transcribe_audio(audio_val)
        st.session_state.last_audio = audio_val

# ── Chat Interface ──
for msg in st.session_state.messages:
    with st.chat_message(msg.type):
        st.markdown(msg.content)

user_query = st.chat_input("Message the agent...")

query = voice_query if voice_query else user_query

if query:
    st.session_state.messages.append(HumanMessage(content=query))
    with st.chat_message("human"):
        st.markdown(query)
        
    with st.chat_message("ai"):
        start_time = time.time()
        
        # 1. Recall memory
        with st.spinner("Recalling memory..."):
            past_context = st.session_state.memory_store.recall_memories(query)
            
        # 2. Build prompt
        system_prompt = "You are a helpful, intelligent AI assistant with long-term memory capabilities. "
        if past_context:
            system_prompt += f"\n\nHere are some relevant memories from past interactions:\n<memories>\n{past_context}\n</memories>\n\nUse these memories to personalize your response if they are relevant."
            
        llm = ChatGoogleGenerativeAI(model="models/gemini-3.5-flash", temperature=0.7)
        
        messages = [SystemMessage(content=system_prompt)] + st.session_state.messages
        
        # 3. Stream Response
        response_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Thinking..."):
            for chunk in llm.stream(messages):
                full_response += chunk.content
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
        
        st.session_state.messages.append(AIMessage(content=full_response))
        
        # 4. Extract & Save new memory (in background/sync)
        # Ask LLM if there's an important fact to remember about the user
        extract_prompt = f"Based on this conversation, extract a concise, single-sentence fact about the user to remember for the future. If there is no specific personal fact, preference, or important detail to remember, reply with 'NONE'.\n\nUser: {query}\nAI: {full_response}\n\nFact:"
        fact = llm.invoke(extract_prompt).content.strip()
        
        if fact and fact != "NONE" and "NONE" not in fact:
            st.session_state.memory_store.save_memory(fact)
            st.toast(f"🧠 Learned a new memory: {fact}")
            
        latency = time.time() - start_time
        st.markdown(f"<p style='font-size: 11px; color: var(--text-muted); margin-top: 8px;'>⚡ Responded in {latency:.2f}s</p>", unsafe_allow_html=True)
