import streamlit as st
import time
import re
import speech_recognition as sr
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from memory import MemoryStore

load_dotenv()

st.set_page_config(
    page_title="Custom AI Agent",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS Design System (rishiware.com style) ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500;600&display=swap');

    :root {
        --bg: #ffffff;
        --text1: #111111;
        --text2: #555555;
        --text3: #999999;
        --border: #e0e0e0;
        --card: #f7f7f7;
        --accent: #111111;
        --success: #059669;
        --success-bg: #ecfdf5;
        --success-border: #d1fae5;
    }

    html, body, [class*="css"] {
        font-family: 'Roboto Mono', monospace;
        background: var(--bg);
        color: var(--text1);
    }

    .stApp {
        max-width: 860px;
        margin: 0 auto;
    }

    /* Hero */
    .hero {
        text-align: center;
        padding: 50px 20px 10px;
    }
    .hero-kicker {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        color: var(--text3);
        margin-bottom: 12px;
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 600;
        line-height: 1.3;
        color: var(--text1);
        margin-bottom: 14px;
    }
    .hero-desc {
        font-size: 0.85rem;
        color: var(--text2);
        max-width: 500px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* Memory Badge */
    .mem-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: var(--success-bg);
        color: var(--success);
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        border: 1px solid var(--success-border);
        margin-top: 18px;
    }

    /* Feature Cards */
    .features {
        display: flex;
        gap: 16px;
        margin: 30px 0;
        justify-content: center;
    }
    .feat {
        flex: 1;
        max-width: 220px;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
    }
    .feat-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: var(--bg);
        border: 1px solid var(--border);
        margin-bottom: 10px;
        color: var(--text1);
    }
    .feat-title {
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 4px;
    }
    .feat-desc {
        font-size: 0.72rem;
        color: var(--text2);
        line-height: 1.5;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 30px 0;
        border-top: 1px solid var(--border);
        margin-top: 40px;
    }
    .footer-text {
        font-size: 0.78rem;
        color: var(--text3);
    }
    .footer-text a { color: var(--text1); text-decoration: none; font-weight: 500; }
    .footer-icons { margin-top: 10px; display: flex; gap: 16px; justify-content: center; }
    .footer-icons a { color: var(--text3); text-decoration: none; transition: color 0.2s; }
    .footer-icons a:hover { color: var(--text1); }

    /* Memory Toast */
    .mem-toast {
        font-size: 0.75rem;
        color: var(--success);
        background: var(--success-bg);
        padding: 6px 14px;
        border-radius: 8px;
        border: 1px solid var(--success-border);
        margin-top: 8px;
        display: inline-block;
    }

    /* Quick Prompt Buttons */
    .stButton > button {
        font-family: 'Roboto Mono', monospace !important;
        font-size: 0.78rem !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        border: 1px solid var(--border) !important;
        background: var(--bg) !important;
        color: var(--text1) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: var(--card) !important;
        border-color: var(--text3) !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Initialize State ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory_store" not in st.session_state:
    st.session_state.memory_store = MemoryStore()
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


# ── Hero Section (only when no messages) ──
if not st.session_state.messages:
    st.markdown("""
    <div class="hero">
        <p class="hero-kicker">Memory Powered</p>
        <div class="hero-title">Your personal AI<br>that remembers you</div>
        <p class="hero-desc">
            Ask anything. This agent learns from your conversations
            and recalls context from past sessions using vector memory.
        </p>
        <div class="mem-badge">🧠 Long-Term Memory Active</div>
    </div>
    """, unsafe_allow_html=True)

    # Feature Cards
    st.markdown("""
    <div class="features">
        <div class="feat">
            <span class="feat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            </span>
            <p class="feat-title">Converse</p>
            <p class="feat-desc">Chat naturally. Powered by Google Gemini for fast, intelligent responses.</p>
        </div>
        <div class="feat">
            <span class="feat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
            </span>
            <p class="feat-title">Remember</p>
            <p class="feat-desc">Learns your preferences and facts. Recalls them in future conversations.</p>
        </div>
        <div class="feat">
            <span class="feat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
            </span>
            <p class="feat-title">Voice</p>
            <p class="feat-desc">Speak to the agent. Built-in speech recognition converts voice to text.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Prompts
    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        if st.button("✧ About Me", use_container_width=True):
            st.session_state.quick_query = "What do you remember about me from our past conversations?"
    with cols[1]:
        if st.button("◷ Recall", use_container_width=True):
            st.session_state.quick_query = "What memories do you have stored about me? List them all."
    with cols[2]:
        if st.button("✎ Teach Me", use_container_width=True):
            st.session_state.quick_query = "Teach me something interesting and useful today."


# ── Voice Input ──
st.markdown("<br>", unsafe_allow_html=True)
audio_val = st.audio_input("Speak to the agent", label_visibility="collapsed")
voice_query = None
if audio_val:
    audio_id = id(audio_val)
    if st.session_state.get("last_audio_id") != audio_id:
        with st.spinner("Transcribing..."):
            try:
                r = sr.Recognizer()
                with sr.AudioFile(audio_val) as source:
                    audio = r.record(source)
                voice_query = r.recognize_google(audio)
                st.session_state.last_audio_id = audio_id
            except Exception as e:
                st.warning(f"Could not transcribe: {e}")


# ── Chat Display ──
for msg in st.session_state.messages:
    with st.chat_message(msg.type):
        st.markdown(msg.content)

# ── Chat Input ──
user_query = st.chat_input("Message the agent...")

if "quick_query" in st.session_state:
    user_query = st.session_state.quick_query
    del st.session_state.quick_query

query = voice_query if voice_query else user_query

if query:
    st.session_state.messages.append(HumanMessage(content=query))
    with st.chat_message("human"):
        st.markdown(query)

    with st.chat_message("ai"):
        start_time = time.time()

        # 1. Recall relevant memories
        with st.spinner("Recalling memory..."):
            past_context = st.session_state.memory_store.recall_memories(query)

        # 2. Build system prompt with memory context
        system_prompt = "You are a helpful, intelligent AI assistant with long-term memory. Be concise, friendly, and personalized."
        if past_context:
            system_prompt += f"\n\nRelevant memories from past interactions:\n<memories>\n{past_context}\n</memories>\n\nUse these to personalize your response."

        llm = ChatGoogleGenerativeAI(model="models/gemini-3.5-flash", temperature=0.7)
        messages = [SystemMessage(content=system_prompt)] + st.session_state.messages

        # 3. Stream response
        response_placeholder = st.empty()
        full_response = ""

        try:
            for chunk in llm.stream(messages):
                full_response += chunk.content
                response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
            st.session_state.messages.append(AIMessage(content=full_response))

            # 4. Auto-extract and save new memory
            extract_prompt = f"Extract a concise single-sentence fact about the user to remember. If nothing specific, reply 'NONE'.\n\nUser: {query}\nAI: {full_response}\n\nFact:"
            fact = llm.invoke(extract_prompt).content.strip()

            if fact and "NONE" not in fact.upper():
                st.session_state.memory_store.save_memory(fact)
                st.markdown(f"<div class='mem-toast'>🧠 Learned: {fact}</div>", unsafe_allow_html=True)

            latency = time.time() - start_time
            st.markdown(f"<p style='font-size: 11px; color: var(--text3); margin-top: 8px;'>⚡ Responded in {latency:.2f}s</p>", unsafe_allow_html=True)

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "ResourceExhausted" in error_msg:
                st.error("**Rate Limit Exceeded:** Please wait 30 seconds and try again.")
            else:
                st.error(f"**Error:** {error_msg}")

    # ── Action Controls ──
    st.markdown("<br>", unsafe_allow_html=True)
    ctrl_cols = st.columns([2.5, 2.5, 5])

    with ctrl_cols[0]:
        chat_export = ""
        for m in st.session_state.messages:
            role = "You" if m.type == "human" else "AI"
            clean = re.sub(r'[*_#`]', '', m.content)
            chat_export += f"{role}: {clean}\n\n"
        st.download_button(
            label="⤓ Export",
            data=chat_export if chat_export else "No messages.",
            file_name="chat_history.txt",
            mime="text/plain",
            use_container_width=True
        )

    with ctrl_cols[1]:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


# ── Footer ──
st.markdown("""
<div class="footer">
    <p class="footer-text">Built by <a href="https://rishiware.com" target="_blank">Rishikesan</a></p>
    <div class="footer-icons">
        <a href="https://rishiware.com" target="_blank">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
        </a>
        <a href="https://linkedin.com/in/rishikesan05" target="_blank">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>
        </a>
        <a href="https://github.com/Rishikesan05" target="_blank">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)
