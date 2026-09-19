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
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS Design System (Linear.app Style) ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    :root {
        --canvas: #010102;
        --surface-1: #0f1011;
        --surface-2: #141516;
        --surface-3: #18191a;
        --hairline: #23252a;
        --primary: #5e6ad2;
        --primary-hover: #828fff;
        --ink: #f7f8f8;
        --ink-muted: #d0d6e0;
        --ink-subtle: #8a8f98;
        --radius: 8px;
        --radius-lg: 12px;
        --shadow-linear: 0 4px 12px rgba(0, 0, 0, 0.5);
    }

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        letter-spacing: -0.2px;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background-color: var(--canvas) !important;
        color: var(--ink) !important;
        overflow-x: hidden !important;
    }
    
    [data-testid="stMainBlockContainer"] {
        padding: 2rem 1rem 3rem 1rem !important;
        max-width: 800px !important;
        margin: 0 auto !important;
    }

    #MainMenu, [data-testid="stHeader"], [data-testid="stFooter"] { 
        display: none !important; 
    }
    a.header-anchor, [data-testid="stMarkdownContainer"] h1 a, [data-testid="stMarkdownContainer"] h2 a { display: none !important; }

    /* Chat Messages */
    .stChatMessage[data-testid="stChatMessage"] {
        border-radius: var(--radius) !important;
        padding: 16px 20px !important;
        margin-bottom: 12px !important;
        font-size: 14px;
        line-height: 1.6;
        border: 1px solid transparent !important;
    }

    /* User Message (Inset) */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid*="user"]) {
        background: transparent !important;
        border-color: var(--hairline) !important;
    }

    /* AI Message (Surface-1) */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid*="assistant"]) {
        background: var(--surface-1) !important;
        border-color: var(--hairline) !important;
        box-shadow: var(--shadow-linear) !important;
    }

    /* Chat Input submit button & icons */
    [data-testid="stChatInputSubmitButton"] {
        color: var(--primary) !important;
    }
    [data-testid="stChatInputSubmitButton"] svg {
        fill: var(--primary) !important;
        color: var(--primary) !important;
    }

    /* Chat Input Container */
    .stChatInput > div {
        border-radius: var(--radius-lg) !important;
        border: 1px solid var(--hairline) !important;
        background: var(--surface-1) !important;
        transition: all 0.2s ease;
        padding: 4px 8px !important;
        box-shadow: 0 12px 24px rgba(0,0,0,0.6) !important;
    }

    .stChatInput > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--primary) !important;
    }

    .stChatInput textarea {
        color: var(--ink) !important;
        font-size: 14px !important;
    }
    .stChatInput textarea::placeholder {
        color: var(--ink-subtle) !important;
    }

    /* Buttons */
    .stButton > button,
    [data-testid="stDownloadButton"] > button {
        border-radius: var(--radius) !important;
        padding: 6px 14px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        transition: all 0.2s ease;
        cursor: pointer;
        background: var(--surface-2) !important;
        color: var(--ink) !important;
        border: 1px solid var(--hairline) !important;
    }

    .stButton > button:hover,
    [data-testid="stDownloadButton"] > button:hover {
        background: var(--surface-3) !important;
        border-color: var(--ink-subtle) !important;
        color: #ffffff !important;
    }

    /* Hero Section */
    .hero {
        text-align: center;
        padding: 40px 24px;
        max-width: 640px;
        margin: 0 auto;
    }

    .hero-kicker {
        font-size: 13px;
        font-weight: 500;
        letter-spacing: 0.4px;
        color: var(--primary);
        margin: 0 0 16px 0 !important;
        display: inline-block;
        padding: 4px 12px;
        background: var(--surface-1);
        border: 1px solid var(--hairline);
        border-radius: 9999px;
    }

    .hero-title {
        font-size: clamp(32px, 5vw, 48px);
        font-weight: 600;
        line-height: 1.1;
        margin: 0 0 16px 0;
        letter-spacing: -1.5px;
        color: var(--ink);
    }

    .hero-desc {
        font-size: 16px;
        font-weight: 400;
        line-height: 1.5;
        color: var(--ink-muted);
        margin: 0;
    }

    /* Feature Cards Grid (Removed, but keeping generic grid styles for buttons if needed) */
    .stButton > button {
        width: 100%;
        text-align: left;
    }

    /* Sidebar fake history item */
    .sidebar-item {
        transition: all 0.2s ease;
    }
    .sidebar-item:hover {
        background: var(--surface-2) !important;
        color: var(--primary) !important;
    }

    /* Footer */
    .ft {
        text-align: center;
        padding: 60px 0 32px 0;
        font-size: 12px;
        color: var(--ink-subtle);
    }

    .ft-links {
        display: flex;
        justify-content: center;
        gap: 24px;
        margin-top: 12px;
    }

    .ft a {
        color: var(--ink-subtle);
        text-decoration: none;
        transition: color 0.2s ease;
    }

    .ft a:hover { 
        color: var(--ink);
    }

    /* Memory Badge */
    .mem-toast {
        font-size: 12px;
        color: var(--ink-muted);
        background: var(--surface-2);
        padding: 6px 12px;
        border-radius: var(--radius);
        border: 1px solid var(--hairline);
        margin-top: 12px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ── JS & GSAP Animations ──
import streamlit.components.v1 as components
components.html(
    """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <script>
        // 1. Rename Streamlit Title
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

        // 2. GSAP Stunning Entry Animations
        // We use setTimeout to ensure Streamlit's React DOM has fully rendered the elements
        setTimeout(() => {
            const parent = window.parent.document;
            
            // Prevent re-animating if already animated (st.rerun triggers this script again)
            if (parent.body.dataset.animated === "true") return;
            parent.body.dataset.animated = "true";
            
            // Main Canvas Empty State (Logo & H2)
            gsap.from(parent.querySelectorAll('h2, svg'), {
                y: 20,
                opacity: 0,
                duration: 1,
                stagger: 0.1,
                ease: "power2.out"
            });

            // Suggested Prompt Buttons
            gsap.from(parent.querySelectorAll('[data-testid="stMainBlockContainer"] .stButton button'), {
                y: 15,
                opacity: 0,
                duration: 0.8,
                stagger: 0.05,
                ease: "power2.out",
                delay: 0.3
            });
            
            // Sidebar Elements
            gsap.from(parent.querySelectorAll('[data-testid="stSidebar"] *'), {
                x: -10,
                opacity: 0,
                duration: 0.8,
                stagger: 0.02,
                ease: "power2.out",
                delay: 0.2
            });
            
            // Animate Chat Input Bar
            gsap.from(parent.querySelectorAll('.stChatInput'), {
                y: 20,
                opacity: 0,
                duration: 1,
                ease: "power3.out",
                delay: 0.5
            });
            
        }, 500); 
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
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ── Sidebar (ChatGPT Style) ──
with st.sidebar:
    # "New Chat" Button
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("<hr style='border-color: var(--hairline); margin: 16px 0;'>", unsafe_allow_html=True)
    
    # Fake History / Memory Controls to look like ChatGPT Sidebar
    st.markdown("""<div style='font-size: 12px; color: var(--ink-subtle); margin-bottom: 8px; padding-left: 8px; font-weight: 500;'>Today</div>""", unsafe_allow_html=True)
    st.markdown("""<div style='font-size: 14px; color: var(--ink); padding: 8px; border-radius: 6px; cursor: pointer;' class='sidebar-item'>Current Conversation</div>""", unsafe_allow_html=True)
    
    st.markdown("""<div style='font-size: 12px; color: var(--ink-subtle); margin-top: 24px; margin-bottom: 8px; padding-left: 8px; font-weight: 500;'>Agent Memory</div>""", unsafe_allow_html=True)
    
    if st.button("🧠 View Memory", use_container_width=True):
        st.session_state.quick_query = "What memories do you have stored about me? List them all."
        
    if st.button("🗑️ Clear Memory", use_container_width=True):
        st.session_state.memory_store.clear_memory()
        st.success("Memory Cleared!")

# ── Main Chat Area Header (Empty State) ──
if not st.session_state.messages:
    # Center container for ChatGPT empty state
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 50vh; text-align: center;">
        <div style="background: var(--surface-1); border: 1px solid var(--hairline); border-radius: 50%; width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; margin-bottom: 24px; box-shadow: var(--shadow-linear);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--ink)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"></path><path d="M12 12 2.1 7.1"></path><path d="M12 12l9.9 4.9"></path></svg>
        </div>
        <h2 style="font-weight: 600; color: var(--ink); font-size: 32px; margin: 0 0 40px 0;">How can I help you today?</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Suggested Prompts (ChatGPT style grid)
    # Using Streamlit columns for the grid
    st.markdown("<div style='max-width: 700px; margin: -20px auto 0 auto;'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✧ What do you remember about me?", use_container_width=True):
            st.session_state.quick_query = "What do you remember about me from our past conversations?"
        if st.button("💡 Brainstorm project ideas", use_container_width=True):
            st.session_state.quick_query = "Give me 3 unique project ideas using AI."
    with col2:
        if st.button("✎ Teach me something new", use_container_width=True):
            st.session_state.quick_query = "Teach me a highly useful but uncommon mental model."
        if st.button("🗣️ Start voice conversation", use_container_width=True):
            st.session_state.quick_query = "I want to practice my communication skills."
    st.markdown("</div>", unsafe_allow_html=True)

# ── Voice Input ──
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
    avatar = "🧑‍💻" if msg.type == "human" else "🤖"
    with st.chat_message(msg.type, avatar=avatar):
        st.markdown(msg.content)

# ── Chat Input ──
user_query = st.chat_input("Message the agent...")

if "quick_query" in st.session_state:
    user_query = st.session_state.quick_query
    del st.session_state.quick_query

query = voice_query if voice_query else user_query

if query:
    st.session_state.messages.append(HumanMessage(content=query))
    with st.chat_message("human", avatar="🧑‍💻"):
        st.markdown(query)

    with st.chat_message("ai", avatar="🤖"):
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
<div class="ft">
    <div class="ft-text">Built by <a href="https://rishiware.com" target="_blank">Rishikesan</a></div>
    <div class="ft-links">
        <a href="https://rishiware.com" target="_blank" title="Website">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
        </a>
        <a href="https://linkedin.com/in/rishikesan05" target="_blank" title="LinkedIn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>
        </a>
        <a href="https://github.com/Rishikesan05" target="_blank" title="GitHub">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)
