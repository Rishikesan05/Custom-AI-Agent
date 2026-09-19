import streamlit as st
import time
import re
import speech_recognition as sr
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from memory import MemoryStore
import ast

load_dotenv()

def extract_text_content(content):
    """Extract clean readable text from langchain/gemini chunks or responses."""
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text"):
                parts.append(getattr(item, "text", ""))
        return "".join(parts)
    if isinstance(content, dict):
        return content.get("text", "")
    if hasattr(content, "text"):
        return getattr(content, "text", "")
    return str(content)

def clean_display_text(text):
    """Clean up and recover human-readable text from any stringified raw dict chunks."""
    if not isinstance(text, str):
        return extract_text_content(text)
    if "{'type':" in text or '{"type":' in text:
        parts = []
        for match in re.finditer(r"'text':\s*('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")", text):
            val = match.group(1)
            try:
                parts.append(ast.literal_eval(val))
            except Exception:
                parts.append(val[1:-1])
        if parts:
            return "".join(parts)
    return text


st.set_page_config(
    page_title="Custom AI Agent",
    page_icon=":material/smart_toy:",
    layout="wide",
    initial_sidebar_state="expanded"
)

from datetime import datetime

# ── CSS Design System ──
st.markdown("""
<style>
    :root {
        --surface-1: #ffffff;
        --surface-2: #f8fafc;
        --surface-3: #f1f5f9;
        --hairline: #e2e8f0;
        --primary: #111827;
        --ink: #0f172a;
        --ink-muted: #475569;
        --ink-subtle: #94a3b8;
        --radius: 14px;
        --radius-lg: 20px;
        --radius-pill: 9999px;
        --shadow-subtle: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-floating: 0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.02);
    }
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');

    /* Ambient Hero Aura */
    .hero-aura {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
    }
    .hero-aura::before {
        content: "";
        position: absolute;
        width: 140px;
        height: 140px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(148, 163, 184, 0.18) 0%, rgba(203, 213, 225, 0.06) 50%, transparent 70%);
        filter: blur(24px);
        z-index: 0;
        animation: auraFloat 5s ease-in-out infinite alternate;
    }
    @keyframes auraFloat {
        0% { transform: scale(0.9); opacity: 0.6; }
        100% { transform: scale(1.2); opacity: 0.9; }
    }
    .hero-logo-box {
        position: relative;
        z-index: 1;
        background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
        border-radius: 20px;
        width: 64px;
        height: 64px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.18);
    }

    /* Component Polish */
    input, textarea, select {
        color: var(--ink) !important;
    }
    [data-testid="stExpander"] {
        background: var(--surface-2) !important;
        border: 1px solid var(--hairline) !important;
        border-radius: var(--radius) !important;
    }
    [data-testid="stExpander"] summary {
        color: var(--ink) !important;
    }
    [data-testid="stTextInput"] input {
        background: var(--surface-1) !important;
        border: 1px solid var(--hairline) !important;
        color: var(--ink) !important;
        border-radius: 8px !important;
    }

    html, body, .stApp, p, h1, h2, h3, h4, h5, h6, input, textarea, label {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
        letter-spacing: -0.01em;
    }

    /* Target button text specifically without affecting icon font */
    .stButton button p,
    .stButton button div[data-testid="stMarkdownContainer"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif !important;
        letter-spacing: -0.01em;
    }

    /* Force Material Symbols Rounded on Streamlit icons */
    [data-testid="stIconMaterial"],
    [data-testid="stIconMaterial"] *,
    .material-symbols-rounded,
    .material-icons {
        font-family: "Material Symbols Rounded" !important;
        font-weight: normal !important;
        font-style: normal !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' 1 !important;
        font-feature-settings: 'liga' 1 !important;
        -webkit-font-smoothing: antialiased !important;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background-color: var(--surface-1) !important;
        color: var(--ink) !important;
    }
    
    [data-testid="stMainBlockContainer"] {
        padding: 2rem 1.5rem 160px 1.5rem !important;
        max-width: 860px !important;
        margin: 0 auto !important;
    }

    /* Header & Controls */
    [data-testid="stHeader"] { 
        background: transparent !important;
        z-index: 99 !important;
    }
    [data-testid="stDeployButton"], .stDeployButton, .stAppDeployButton, [data-testid="stHeaderActionElements"], [data-testid="stToolbarActions"], #MainMenu, [data-testid="stFooter"] { 
        display: none !important; 
    }

    /* Sidebar Expand Button (When Sidebar is Collapsed) */
    button[data-testid="stExpandSidebarButton"] {
        position: fixed !important;
        top: 14px !important;
        left: 14px !important;
        z-index: 9999 !important;
        background: var(--surface-1) !important;
        border: 1px solid var(--hairline) !important;
        border-radius: var(--radius-pill) !important;
        height: 38px !important;
        padding: 0 14px 0 10px !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        box-shadow: var(--shadow-floating) !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    button[data-testid="stExpandSidebarButton"]:hover {
        background: var(--surface-2) !important;
        border-color: var(--ink-subtle) !important;
        transform: scale(1.04) !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08) !important;
    }

    button[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
        color: var(--ink) !important;
        font-size: 20px !important;
    }

    button[data-testid="stExpandSidebarButton"]::after {
        content: "Open Sidebar";
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        color: var(--ink) !important;
        white-space: nowrap !important;
        margin-left: 2px !important;
    }

    /* Sidebar Collapse Button inside Sidebar */
    [data-testid="stSidebarCollapseButton"] button {
        border-radius: 8px !important;
        border: 1px solid var(--hairline) !important;
        background: var(--surface-1) !important;
        box-shadow: var(--shadow-subtle) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebarCollapseButton"] button:hover {
        background: var(--surface-3) !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: var(--surface-2) !important;
        border-right: 1px solid var(--hairline) !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    
    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1rem 0.75rem 190px 0.75rem !important;
        }
        h1 {
            font-size: 28px !important;
        }
        .suggestion-grid .stButton > button {
            padding: 12px 16px !important;
            font-size: 13.5px !important;
            min-height: 60px !important;
        }
    }

    /* Align Streamlit bottom bar */
    [data-testid="stBottom"] {
        background: transparent !important;
        padding: 0 0 20px 0 !important;
        pointer-events: auto !important;
    }
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {
        max-width: 760px !important;
        margin: 0 auto !important;
        padding: 0 16px !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        position: relative !important;
        box-sizing: border-box !important;
    }

    /* 1. Chat Input Field */
    .stChatInput {
        flex: 1 1 auto !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .stChatInput > div {
        position: relative !important;
        width: 100% !important;
        max-width: none !important;
        left: auto !important;
        right: auto !important;
        bottom: auto !important;
        height: 48px !important;
        min-height: 48px !important;
        margin: 0 !important;
        border-radius: var(--radius-pill) !important;
        border: 1px solid var(--hairline) !important;
        background: var(--surface-1) !important;
        box-shadow: var(--shadow-floating) !important;
        padding: 4px 10px 4px 18px !important;
        transition: all 0.2s ease !important;
        pointer-events: auto !important;
        display: flex !important;
        align-items: center !important;
        box-sizing: border-box !important;
    }
    .stChatInput > div:focus-within {
        border-color: var(--ink-subtle) !important;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08), 0 0 0 2px rgba(15, 23, 42, 0.06) !important;
    }

    .stChatInput textarea {
        color: var(--ink) !important;
        font-size: 14.5px !important;
        padding: 0 !important;
        height: 24px !important;
        min-height: 24px !important;
        line-height: 24px !important;
    }

    [data-testid="stChatInputSubmitButton"] {
        height: 34px !important;
        width: 34px !important;
        min-height: 34px !important;
        min-width: 34px !important;
        border-radius: 50% !important;
        background: #0f172a !important;
        color: #ffffff !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stChatInputSubmitButton"]:hover {
        background: #1e293b !important;
        transform: scale(1.05) !important;
    }

    /* 2. Unified Horizontal Dock Wrapper */
    #wa-dock-wrapper {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 10px !important;
        width: 100% !important;
        max-width: 760px !important;
        margin: 0 auto !important;
        position: relative !important;
        box-sizing: border-box !important;
    }

    #wa-chat-min-btn {
        display: none !important;
    }
    #wa-dock-wrapper.recording #wa-chat-min-btn {
        display: flex !important;
    }

    /* 3. Dock Circular Action Buttons (Mic & Minimized Chat) */
    .wa-dock-circle-btn {
        width: 48px;
        height: 48px;
        min-width: 48px;
        border-radius: 50%;
        background: var(--surface-1);
        border: 1px solid var(--hairline);
        box-shadow: var(--shadow-floating);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        color: var(--ink);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        flex-shrink: 0;
        box-sizing: border-box;
    }
    .wa-dock-circle-btn:hover {
        transform: scale(1.06);
        border-color: var(--ink-subtle);
        background: var(--surface-2);
        box-shadow: 0 12px 28px rgba(0,0,0,0.1);
    }

    /* 4. Long Expandable Voice Recording Bar */
    #wa-record-bar {
        display: none !important;
        flex: 1 1 auto;
        height: 48px;
        background: var(--surface-1);
        border: 1px solid var(--hairline);
        border-radius: var(--radius-pill);
        box-shadow: var(--shadow-floating);
        align-items: center;
        justify-content: space-between;
        padding: 0 12px;
        box-sizing: border-box;
        animation: waFadeIn 0.2s ease-out;
    }
    @keyframes waFadeIn {
        from { opacity: 0; transform: scale(0.98); }
        to { opacity: 1; transform: scale(1); }
    }

    #wa-dock-wrapper.recording #wa-record-bar {
        display: flex !important;
    }

    #wa-dock-wrapper.recording .stChatInput {
        display: none !important;
    }

    #wa-dock-wrapper.recording #wa-mic-btn {
        display: none !important;
    }

    /* Grayscale Recording Actions */
    .wa-action-btn {
        width: 34px;
        height: 34px;
        min-width: 34px;
        border-radius: 50%;
        border: 1px solid var(--hairline);
        background: var(--surface-2);
        color: var(--ink);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.15s ease;
        box-sizing: border-box;
    }
    .wa-action-btn:hover {
        background: var(--surface-3);
        border-color: var(--ink-subtle);
        transform: scale(1.06);
    }
    .wa-send-btn {
        background: #0f172a !important;
        color: #ffffff !important;
        border: none !important;
    }
    .wa-send-btn:hover {
        background: #1e293b !important;
        transform: scale(1.06) !important;
    }
    .wa-timer {
        font-size: 13.5px;
        font-weight: 600;
        color: var(--ink);
        font-variant-numeric: tabular-nums;
        min-width: 44px;
    }
    .wa-rec-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #e11d48;
        animation: waPulse 1.2s infinite;
    }
    @keyframes waPulse {
        0% { transform: scale(0.85); opacity: 0.6; }
        50% { transform: scale(1.3); opacity: 1; }
        100% { transform: scale(0.85); opacity: 0.6; }
    }
    .wa-waveform {
        display: flex;
        align-items: center;
        gap: 3px;
        height: 24px;
        flex: 1;
        max-width: 240px;
        justify-content: center;
    }
    .wa-wave-bar {
        width: 3px;
        height: 6px;
        border-radius: 3px;
        background: #475569;
        transition: height 0.08s ease;
    }

    /* SVG Icon Replacements for Buttons */
    [data-testid="stSidebar"] button[data-testid*="chat_nav_"] [data-testid="stIconMaterial"] {
        display: inline-block !important;
        width: 18px !important;
        height: 18px !important;
        mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7.9 20A9 9 0 1 0 4 16.1L2 22Z'/%3E%3C/svg%3E") no-repeat center / contain !important;
        -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7.9 20A9 9 0 1 0 4 16.1L2 22Z'/%3E%3C/svg%3E") no-repeat center / contain !important;
        background-color: currentColor !important;
        font-size: 0 !important;
    }

    [data-testid="stSidebar"] button[data-testid*="chat_del_"] [data-testid="stIconMaterial"] {
        display: inline-block !important;
        width: 16px !important;
        height: 16px !important;
        mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 6h18'/%3E%3Cpath d='M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6'/%3E%3Cpath d='M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2'/%3E%3C/svg%3E") no-repeat center / contain !important;
        -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 6h18'/%3E%3Cpath d='M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6'/%3E%3Cpath d='M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2'/%3E%3C/svg%3E") no-repeat center / contain !important;
        background-color: currentColor !important;
        font-size: 0 !important;
    }

    [data-testid="stSidebar"] button[data-testid*="new_chat_btn"] [data-testid="stIconMaterial"],
    [data-testid="stColumn"]:has(.action-btn-left) [data-testid="stPopover"] button [data-testid="stIconMaterial"] {
        display: inline-block !important;
        width: 20px !important;
        height: 20px !important;
        mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 5v14M5 12h14'/%3E%3C/svg%3E") no-repeat center / contain !important;
        -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 5v14M5 12h14'/%3E%3C/svg%3E") no-repeat center / contain !important;
        background-color: currentColor !important;
        font-size: 0 !important;
    }

        border-radius: 50% !important;
        width: 46px !important;
        height: 46px !important;
        min-height: 46px !important;
        min-width: 46px !important;
        padding: 0 !important;
        background: var(--surface-1) !important;
        box-shadow: var(--shadow-floating) !important;
        border: 1px solid var(--hairline) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    [data-testid="stColumn"]:has(.action-btn-left) [data-testid="stPopover"] button:hover {
        border-color: var(--ink-subtle) !important;
        transform: scale(1.05);
        box-shadow: 0 12px 28px rgba(0,0,0,0.1) !important;
    }

    /* Hide the second icon (chevron expand_more) inside popover button */
    [data-testid="stColumn"]:has(.action-btn-left) button div[aria-hidden="true"] {
        display: none !important;
    }

    [data-testid="stColumn"]:has(.action-btn-left) [data-testid="stPopover"] button [data-testid="stIconMaterial"] {
        color: var(--ink) !important;
        font-size: 22px !important;
        margin: 0 !important;
    }
    
    /* Ensure the popover content looks good */
    [data-testid="stPopoverBody"] {
        border-radius: 16px !important;
        border: 1px solid var(--hairline) !important;
        box-shadow: var(--shadow-floating) !important;
        padding: 12px !important;
        min-width: 200px !important;
    }

    /* Clean, harmonized Chat Container & Message Alignment */
    .stChatMessage[data-testid="stChatMessage"] {
        border-radius: var(--radius-lg) !important;
        margin-bottom: 24px !important;
        font-size: 15.5px !important;
        line-height: 1.6 !important;
        border: none !important;
        display: flex !important;
        align-items: flex-start !important;
        gap: 14px !important;
    }

    /* User Message: Clean right-aligned floating bubble */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid*="user"]),
    .stChatMessage[data-testid="stChatMessage"]:has([aria-label*="human"]),
    .stChatMessage[data-testid="stChatMessage"]:has([aria-label*="user"]) {
        background: var(--surface-2) !important;
        border: 1px solid var(--hairline) !important;
        color: var(--ink) !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        border-radius: 20px 20px 6px 20px !important;
        max-width: 80% !important;
        padding: 14px 20px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }

    /* Assistant Message: Clean left-aligned bubble matching user message */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid*="assistant"]),
    .stChatMessage[data-testid="stChatMessage"]:has([aria-label*="assistant"]),
    .stChatMessage[data-testid="stChatMessage"]:has([aria-label*="ai"]) {
        background: var(--surface-1) !important;
        border: 1px solid var(--hairline) !important;
        color: var(--ink) !important;
        margin-left: 0 !important;
        margin-right: auto !important;
        border-radius: 20px 20px 20px 6px !important;
        max-width: 85% !important;
        padding: 16px 22px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }
    
    [data-testid="stChatMessage"] [data-testid="stChatAvatar"],
    [data-testid="stChatMessage"] [data-testid*="stChatMessageAvatar"] {
        background: transparent !important;
        border-radius: 50% !important;
        margin: 0 !important;
        padding: 0 !important;
        flex-shrink: 0 !important;
    }

    [data-testid="stChatMessage"] img {
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        min-height: 38px !important;
        object-fit: contain !important;
        display: block !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: var(--ink) !important;
        font-size: 15px !important;
        line-height: 1.65 !important;
    }

    /* Clean Monochrome Grayscale Action Buttons (Retry, etc.) */
    .stChatMessage .stButton button {
        border-radius: var(--radius-pill) !important;
        font-size: 12.5px !important;
        font-weight: 500 !important;
        padding: 4px 14px !important;
        min-height: 30px !important;
        height: 30px !important;
        border: 1px solid var(--hairline) !important;
        background: var(--surface-1) !important;
        color: var(--ink) !important;
        box-shadow: var(--shadow-subtle) !important;
        transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        margin-top: 6px !important;
    }
    .stChatMessage .stButton button:hover {
        background: var(--surface-3) !important;
        border-color: var(--ink-subtle) !important;
        color: var(--ink) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }
    .stChatMessage .stButton button:active {
        transform: translateY(0) !important;
    }
    /* Grayscale SVG Icon Mask for Retry Button */
    .stChatMessage .stButton button [data-testid="stIconMaterial"] {
        display: inline-block !important;
        width: 14px !important;
        height: 14px !important;
        mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8'/%3E%3Cpath d='M21 3v5h-5'/%3E%3Cpath d='M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16'/%3E%3Cpath d='M8 16H3v5'/%3E%3C/svg%3E") no-repeat center / contain !important;
        -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8'/%3E%3Cpath d='M21 3v5h-5'/%3E%3Cpath d='M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16'/%3E%3Cpath d='M8 16H3v5'/%3E%3C/svg%3E") no-repeat center / contain !important;
        background-color: currentColor !important;
        font-size: 0 !important;
        color: var(--ink-muted) !important;
    }
    .stChatMessage .stButton button:hover [data-testid="stIconMaterial"] {
        color: var(--ink) !important;
    }

    /* Suggestion Grid */
    .suggestion-grid .stButton > button {
        border-radius: var(--radius) !important;
        padding: 18px 22px !important;
        font-weight: 500 !important;
        font-size: 14.5px !important;
        text-align: left !important;
        height: auto !important;
        min-height: 80px;
        background: var(--surface-1) !important;
        color: var(--ink) !important;
        border: 1px solid var(--hairline) !important;
        box-shadow: var(--shadow-subtle) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: flex;
        align-items: center;
        gap: 12px;
        white-space: normal;
        line-height: 1.4;
    }

    .suggestion-grid .stButton > button:hover {
        border-color: var(--ink-subtle) !important;
        box-shadow: var(--shadow-floating) !important;
        transform: translateY(-2px);
    }
    
    /* Sidebar Chat History Container */
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border: 1px solid var(--hairline) !important;
        background: var(--surface-1) !important;
        padding: 4px !important;
    }

    /* Sidebar general button styling */
    [data-testid="stSidebar"] .stButton > button {
        min-height: auto;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        font-weight: 500 !important;
        color: var(--ink-muted) !important;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13.5px !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--surface-3) !important;
        color: var(--ink) !important;
        transform: none;
    }

    /* Active Chat Bar (Primary) */
    [data-testid="stSidebar"] button[kind="primary"] {
        background: var(--ink) !important;
        color: #ffffff !important;
        border: 1px solid var(--ink) !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.15) !important;
    }
    [data-testid="stSidebar"] button[kind="primary"] [data-testid="stIconMaterial"] {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] button[kind="primary"] p {
        color: #ffffff !important;
    }

    /* Inactive Chat Bar (Secondary) */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: transparent !important;
        color: var(--ink-muted) !important;
        border: 1px solid transparent !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: var(--surface-3) !important;
        color: var(--ink) !important;
    }

    /* Prominent ➕ New Chat Button */
    [data-testid="stSidebar"] button[data-testid*="new_chat_btn"] {
        background: var(--surface-1) !important;
        border: 1px solid var(--hairline) !important;
        color: var(--ink) !important;
        box-shadow: var(--shadow-subtle) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
        margin-bottom: 8px !important;
        justify-content: center !important;
    }
    [data-testid="stSidebar"] button[data-testid*="new_chat_btn"]:hover {
        background: var(--surface-3) !important;
        border-color: var(--ink-subtle) !important;
        transform: translateY(-1px);
    }

    /* Delete Chat Button inside Sidebar */
    [data-testid="stSidebar"] div[data-testid="stColumn"]:has(button[data-testid*="chat_del_"]) {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    [data-testid="stSidebar"] button[data-testid*="chat_del_"] {
        padding: 0 !important;
        width: 32px !important;
        height: 32px !important;
        min-width: 32px !important;
        min-height: 32px !important;
        border-radius: 8px !important;
        border: none !important;
        background: transparent !important;
        color: var(--ink-subtle) !important;
        justify-content: center !important;
    }
    [data-testid="stSidebar"] button[data-testid*="chat_del_"]:hover {
        background: #fee2e2 !important;
        color: #ef4444 !important;
    }

    .mem-toast {
        font-size: 12px;
        color: var(--ink-muted);
        background: var(--surface-2);
        padding: 8px 12px;
        border-radius: var(--radius);
        border: 1px solid var(--hairline);
        margin-top: 12px;
        display: inline-block;
        font-weight: 500;
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
            
            // Animate Chat Input Bar
            gsap.from(parent.querySelectorAll('.stChatInput'), {
                y: 20,
                opacity: 0,
                duration: 1,
                ease: "power3.out",
                delay: 0.5
            });
            
        }, 500); 

        // 3. WhatsApp/ChatGPT Style Voice Recorder & Dock Transformation
        (function() {
            const parentDoc = window.parent.document;
            const parentWin = window.parent;

            function mountDockElements() {
                const chatInput = parentDoc.querySelector('.stChatInput');
                if (!chatInput) return;

                let wrapper = parentDoc.getElementById('wa-dock-wrapper');
                if (!wrapper) {
                    wrapper = parentDoc.createElement('div');
                    wrapper.id = 'wa-dock-wrapper';
                    chatInput.parentNode.insertBefore(wrapper, chatInput);
                }

                // 1. Minimized Chat Icon Button (left side when recording)
                let chatBtn = parentDoc.getElementById('wa-chat-min-btn');
                if (!chatBtn) {
                    chatBtn = parentDoc.createElement('button');
                    chatBtn.id = 'wa-chat-min-btn';
                    chatBtn.className = 'wa-dock-circle-btn';
                    chatBtn.title = 'Switch back to keyboard typing';
                    chatBtn.style.display = 'none';
                    chatBtn.innerHTML = `
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                    `;
                }

                // 2. Expandable Voice Recording Bar
                let bar = parentDoc.getElementById('wa-record-bar');
                if (!bar) {
                    bar = parentDoc.createElement('div');
                    bar.id = 'wa-record-bar';
                    bar.style.display = 'none';
                    bar.innerHTML = `
                        <button id="wa-btn-trash" class="wa-action-btn wa-trash-btn" title="Cancel recording">
                            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                            </svg>
                        </button>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div class="wa-rec-dot" id="wa-rec-dot"></div>
                            <div class="wa-timer" id="wa-timer">00:00</div>
                        </div>
                        <div class="wa-waveform" id="wa-waveform">
                            ${Array(18).fill(0).map(() => '<div class="wa-wave-bar"></div>').join('')}
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <button id="wa-btn-pause" class="wa-action-btn wa-pause-btn" title="Pause / Continue">
                                <svg id="wa-icon-pause" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
                                    <rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>
                                </svg>
                                <svg id="wa-icon-play" style="display: none; margin-left: 2px;" width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                                    <polygon points="6,4 20,12 6,20"/>
                                </svg>
                            </button>
                            <button id="wa-btn-send" class="wa-action-btn wa-send-btn" title="Send voice message">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                                </svg>
                            </button>
                        </div>
                    `;
                }

                // 3. Circular Mic Button (idle state, right side)
                let micBtn = parentDoc.getElementById('wa-mic-btn');
                if (!micBtn) {
                    micBtn = parentDoc.createElement('button');
                    micBtn.id = 'wa-mic-btn';
                    micBtn.className = 'wa-dock-circle-btn';
                    micBtn.title = 'Click to speak';
                    micBtn.innerHTML = `
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                            <line x1="12" x2="12" y1="19" y2="22"/>
                        </svg>
                    `;
                }

                // Append in exact horizontal order: [chatBtn, chatInput, bar, micBtn]
                if (chatBtn.parentNode !== wrapper) wrapper.appendChild(chatBtn);
                if (chatInput.parentNode !== wrapper) wrapper.appendChild(chatInput);
                if (bar.parentNode !== wrapper) wrapper.appendChild(bar);
                if (micBtn.parentNode !== wrapper) wrapper.appendChild(micBtn);

                // Direct binding on the buttons to ensure reliable clicks regardless of iframe lifecycle
                micBtn.onclick = (e) => {
                    if (e) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                    startRecording();
                };

                chatBtn.onclick = (e) => {
                    if (e) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                    revertDockToIdle();
                };

                const trashBtn = bar.querySelector('#wa-btn-trash');
                if (trashBtn) {
                    trashBtn.onclick = (e) => {
                        if (e) {
                            e.preventDefault();
                            e.stopPropagation();
                        }
                        currentTranscript = '';
                        revertDockToIdle();
                    };
                }

                const pauseBtn = bar.querySelector('#wa-btn-pause');
                if (pauseBtn) {
                    pauseBtn.onclick = (e) => {
                        if (e) {
                            e.preventDefault();
                            e.stopPropagation();
                        }
                        togglePause();
                    };
                }

                const sendBtn = bar.querySelector('#wa-btn-send');
                if (sendBtn) {
                    sendBtn.onclick = (e) => {
                        if (e) {
                            e.preventDefault();
                            e.stopPropagation();
                        }
                        sendRecording();
                    };
                }
            }

            // Voice Recording State
            let isRecording = false;
            let isPaused = false;
            let timerInterval = null;
            let secondsElapsed = 0;
            let animFrame = null;
            let recognition = null;
            let audioStream = null;
            let audioCtx = null;
            let analyser = null;
            let currentTranscript = '';

            function formatTime(s) {
                const m = Math.floor(s / 60).toString().padStart(2, '0');
                const sec = (s % 60).toString().padStart(2, '0');
                return `${m}:${sec}`;
            }

            function revertDockToIdle() {
                isRecording = false;
                isPaused = false;
                clearInterval(timerInterval);
                cancelAnimationFrame(animFrame);
                currentTranscript = '';

                if (recognition) {
                    try { recognition.stop(); } catch(e) {}
                    recognition = null;
                }
                if (audioStream) {
                    try {
                        audioStream.getTracks().forEach(t => t.stop());
                    } catch(e) {}
                    audioStream = null;
                }
                if (audioCtx && audioCtx.state !== 'closed') {
                    try { audioCtx.close(); } catch(e) {}
                    audioCtx = null;
                }
                analyser = null;

                const wrapper = parentDoc.getElementById('wa-dock-wrapper');
                if (wrapper) wrapper.classList.remove('recording');
            }

            function runWaveform() {
                const waveBars = parentDoc.querySelectorAll('.wa-wave-bar');
                function step() {
                    if (!isRecording) return;
                    if (!isPaused) {
                        if (analyser) {
                            const dataArray = new Uint8Array(analyser.frequencyBinCount);
                            analyser.getByteFrequencyData(dataArray);
                            waveBars.forEach((bar, idx) => {
                                const val = dataArray[idx * 2] || 0;
                                const h = Math.max(4, Math.min(24, (val / 255) * 24 + 4));
                                bar.style.height = `${h}px`;
                            });
                        } else {
                            waveBars.forEach(bar => {
                                const h = Math.floor(Math.random() * 14) + 4;
                                bar.style.height = `${h}px`;
                            });
                        }
                    }
                    animFrame = requestAnimationFrame(step);
                }
                cancelAnimationFrame(animFrame);
                animFrame = requestAnimationFrame(step);
            }

            function startRecording() {
                const wrapper = parentDoc.getElementById('wa-dock-wrapper');
                if (wrapper) wrapper.classList.add('recording');

                const timerEl = parentDoc.getElementById('wa-timer');
                const iconPause = parentDoc.getElementById('wa-icon-pause');
                const iconPlay = parentDoc.getElementById('wa-icon-play');
                const recDot = parentDoc.getElementById('wa-rec-dot');

                isRecording = true;
                isPaused = false;
                secondsElapsed = 0;
                currentTranscript = '';

                if (timerEl) timerEl.innerText = '00:00';
                if (iconPause) iconPause.style.display = 'block';
                if (iconPlay) iconPlay.style.display = 'none';
                if (recDot) recDot.style.animationPlayState = 'running';

                // 2. Start timer immediately
                clearInterval(timerInterval);
                timerInterval = setInterval(() => {
                    if (!isPaused) {
                        secondsElapsed++;
                        if (timerEl) timerEl.innerText = formatTime(secondsElapsed);
                    }
                }, 1000);

                // 3. Start live waveform
                runWaveform();

                // 4. Initialize Web Speech Recognition
                const SpeechRec = parentWin.SpeechRecognition || parentWin.webkitSpeechRecognition || window.SpeechRecognition || window.webkitSpeechRecognition;
                if (SpeechRec) {
                    try {
                        recognition = new SpeechRec();
                        recognition.continuous = true;
                        recognition.interimResults = true;
                        recognition.lang = parentWin.navigator.language || 'en-US';
                        recognition.onresult = (evt) => {
                            let text = '';
                            for (let i = 0; i < evt.results.length; i++) {
                                text += evt.results[i][0].transcript + ' ';
                            }
                            currentTranscript = text.trim();
                        };
                        recognition.onerror = (evt) => {
                            if (evt.error === 'no-speech') return;
                            console.warn("Speech recognition warning:", evt.error);
                        };
                        recognition.onend = () => {
                            if (isRecording && !isPaused) {
                                setTimeout(() => {
                                    if (isRecording && !isPaused && recognition) {
                                        try { recognition.start(); } catch(e) {}
                                    }
                                }, 250);
                            }
                        };
                        recognition.start();
                    } catch(err) {
                        console.warn("SpeechRec start failed:", err);
                    }
                }

                // 5. Connect media stream for hardware audio analyzer
                const nav = parentWin.navigator.mediaDevices ? parentWin.navigator : window.navigator;
                if (nav.mediaDevices && nav.mediaDevices.getUserMedia) {
                    nav.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
                        audioStream = stream;
                        try {
                            const AudioCtx = parentWin.AudioContext || parentWin.webkitAudioContext || window.AudioContext || window.webkitAudioContext;
                            audioCtx = new AudioCtx();
                            const source = audioCtx.createMediaStreamSource(stream);
                            analyser = audioCtx.createAnalyser();
                            analyser.fftSize = 64;
                            source.connect(analyser);
                        } catch(e) {
                            console.warn("AudioContext setup:", e);
                        }
                    }).catch((err) => {
                        console.warn("getUserMedia access:", err);
                    });
                }
            }

            function togglePause() {
                if (!isRecording) return;
                const iconPause = parentDoc.getElementById('wa-icon-pause');
                const iconPlay = parentDoc.getElementById('wa-icon-play');
                const recDot = parentDoc.getElementById('wa-rec-dot');
                const waveBars = parentDoc.querySelectorAll('.wa-wave-bar');

                if (!isPaused) {
                    isPaused = true;
                    if (iconPause) iconPause.style.display = 'none';
                    if (iconPlay) iconPlay.style.display = 'block';
                    if (recDot) recDot.style.animationPlayState = 'paused';
                    waveBars.forEach(b => b.style.height = '6px');
                    if (recognition) {
                        try { recognition.stop(); } catch(e) {}
                    }
                } else {
                    isPaused = false;
                    if (iconPause) iconPause.style.display = 'block';
                    if (iconPlay) iconPlay.style.display = 'none';
                    if (recDot) recDot.style.animationPlayState = 'running';
                    if (recognition) {
                        try { recognition.start(); } catch(e) {}
                    }
                    runWaveform();
                }
            }

            function sendRecording() {
                const text = currentTranscript.trim();
                revertDockToIdle();

                if (text) {
                    const textarea = parentDoc.querySelector('.stChatInput textarea');
                    const submitBtn = parentDoc.querySelector('[data-testid="stChatInputSubmitButton"]');
                    if (textarea && submitBtn) {
                        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                        nativeSetter.call(textarea, text);
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        setTimeout(() => {
                            submitBtn.click();
                        }, 80);
                    }
                }
            }

            // Mount immediately and monitor DOM changes
            mountDockElements();
            setInterval(mountDockElements, 300);

            // Expose active controller to parent window
            parentWin.__waDockController = {
                startRecording,
                togglePause,
                sendRecording,
                revertDockToIdle
            };
            parentWin.__startVoiceRec = startRecording;

            // Manage parent document delegated click handler cleanly
            if (parentDoc.__waVoiceClickHandler) {
                try {
                    parentDoc.removeEventListener('click', parentDoc.__waVoiceClickHandler, true);
                } catch(e) {}
            }
            parentDoc.__waVoiceClickHandler = (e) => {
                const ctrl = parentWin.__waDockController;
                if (!ctrl) return;

                const micTarget = e.target.closest('#wa-mic-btn');
                if (micTarget) {
                    e.preventDefault();
                    e.stopPropagation();
                    ctrl.startRecording();
                    return;
                }

                const chatMinTarget = e.target.closest('#wa-chat-min-btn');
                if (chatMinTarget) {
                    e.preventDefault();
                    e.stopPropagation();
                    ctrl.revertDockToIdle();
                    return;
                }

                const trashTarget = e.target.closest('#wa-btn-trash');
                if (trashTarget) {
                    e.preventDefault();
                    e.stopPropagation();
                    ctrl.revertDockToIdle();
                    return;
                }

                const pauseTarget = e.target.closest('#wa-btn-pause');
                if (pauseTarget) {
                    e.preventDefault();
                    e.stopPropagation();
                    ctrl.togglePause();
                    return;
                }

                const sendTarget = e.target.closest('#wa-btn-send');
                if (sendTarget) {
                    e.preventDefault();
                    e.stopPropagation();
                    ctrl.sendRecording();
                    return;
                }
            };
            parentDoc.addEventListener('click', parentDoc.__waVoiceClickHandler, true);
        })(); 
    </script>
    """,
    height=0,
    width=0,
)


# ── Initialize Multi-Session Chat State ──
if "chats" not in st.session_state:
    init_id = f"chat_{int(time.time() * 1000)}"
    existing_messages = st.session_state.get("messages", [])
    init_title = "New Chat"
    if existing_messages:
        for m in existing_messages:
            if m.type == "human":
                words = m.content.strip().split()
                init_title = " ".join(words[:5])
                if len(words) > 5 or len(m.content.strip()) > 28:
                    init_title = init_title[:26].rstrip() + "..."
                break
    st.session_state.chats = {
        init_id: {
            "id": init_id,
            "title": init_title,
            "messages": existing_messages,
            "created_at": time.time(),
        }
    }
    st.session_state.active_chat_id = init_id

if "active_chat_id" not in st.session_state or st.session_state.active_chat_id not in st.session_state.chats:
    if st.session_state.chats:
        st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
    else:
        new_id = f"chat_{int(time.time() * 1000)}"
        st.session_state.chats[new_id] = {
            "id": new_id,
            "title": "New Chat",
            "messages": [],
            "created_at": time.time(),
        }
        st.session_state.active_chat_id = new_id

# Synchronize st.session_state.messages with active chat session
active_chat = st.session_state.chats[st.session_state.active_chat_id]
st.session_state.messages = active_chat["messages"]

if "memory_store" not in st.session_state or not hasattr(st.session_state.memory_store, "get_all_memories"):
    st.session_state.memory_store = MemoryStore()
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ── Sidebar (Branding, Chat Bars & Memory Vault) ──
with st.sidebar:
    # 1. Brand Identity (Clean, professional, without flashy AI badges)
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding: 4px 0;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #334155 100%); border-radius: 12px; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.12); flex-shrink: 0;">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12 2.1 7.1"/><path d="M12 12l9.9 4.9"/></svg>
        </div>
        <div>
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 16px; color: var(--ink); line-height: 1.2;">Custom AI Agent</div>
            <div style="font-size: 11.5px; color: var(--ink-muted); font-weight: 500;">Personal Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Primary Action: New Chat (ChatGPT-style draft creation)
    if st.button("New Chat", icon=":material/add:", use_container_width=True, key="new_chat_btn", help="Start a new conversation"):
        curr_active = st.session_state.chats.get(st.session_state.active_chat_id, {})
        if not curr_active.get("messages"):
            # Already in an empty new chat
            st.rerun()
        
        # Check if an existing empty chat is available to reuse
        empty_id = next((c_id for c_id, c_data in st.session_state.chats.items() if not c_data.get("messages")), None)
        if empty_id:
            st.session_state.active_chat_id = empty_id
        else:
            new_id = f"chat_{int(time.time() * 1000)}"
            st.session_state.chats[new_id] = {
                "id": new_id,
                "title": "New Chat",
                "messages": [],
                "created_at": time.time(),
            }
            st.session_state.active_chat_id = new_id
        st.rerun()

    # 3. Chat Bars (Only display non-empty, saved conversations like ChatGPT)
    sorted_all_chats = sorted(st.session_state.chats.items(), key=lambda x: x[1].get("created_at", 0), reverse=True)
    saved_chats = [
        (c_id, c_data) for c_id, c_data in sorted_all_chats 
        if len(c_data.get("messages", [])) > 0
    ]
    total_chats = len(saved_chats)

    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin: 12px 0 6px 0;">
        <span style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--ink-muted);">Conversations</span>
        <span style="background: var(--surface-3); font-size: 11px; font-weight: 600; color: var(--ink); padding: 2px 8px; border-radius: 9999px;">{total_chats}</span>
    </div>
    """, unsafe_allow_html=True)

    if saved_chats:
        with st.container(height=190):
            for c_id, c_data in saved_chats:
                is_active = (c_id == st.session_state.active_chat_id)
                title_text = c_data.get("title", "Conversation")
                display_label = title_text[:18] + "..." if len(title_text) > 20 else title_text
                icon = ":material/chat_bubble:" if is_active else ":material/chat_bubble_outline:"
                btn_type = "primary" if is_active else "secondary"
                c_col1, c_col2 = st.columns([5, 1])
                with c_col1:
                    if st.button(display_label, key=f"chat_nav_{c_id}", icon=icon, use_container_width=True, type=btn_type, help=title_text):
                        st.session_state.active_chat_id = c_id
                        st.rerun()
                with c_col2:
                    if st.button(" ", key=f"chat_del_{c_id}", icon=":material/delete_outline:", help="Delete conversation"):
                        del st.session_state.chats[c_id]
                        if st.session_state.active_chat_id == c_id:
                            remaining = [k for k, v in st.session_state.chats.items() if len(v.get("messages", [])) > 0]
                            if remaining:
                                st.session_state.active_chat_id = remaining[0]
                            else:
                                new_id = f"chat_{int(time.time() * 1000)}"
                                st.session_state.chats[new_id] = {
                                    "id": new_id,
                                    "title": "New Chat",
                                    "messages": [],
                                    "created_at": time.time(),
                                }
                                st.session_state.active_chat_id = new_id
                        st.rerun()
    else:
        st.markdown("<div style='font-size: 11.5px; color: var(--ink-subtle); padding: 10px 4px;'>No saved conversations yet. Start typing or speaking to begin!</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border: none; border-top: 1px solid var(--hairline); margin: 16px 0;'>", unsafe_allow_html=True)

    # 4. Core Specialty: Semantic Memory Vault
    memories = st.session_state.memory_store.get_all_memories()
    mem_count = len(memories)

    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
        <span style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--ink-muted);">Memory Vault</span>
        <span style="background: var(--surface-3); font-size: 11px; font-weight: 600; color: var(--ink); padding: 2px 8px; border-radius: 9999px;">{mem_count} facts</span>
    </div>
    """, unsafe_allow_html=True)

    # A. Add Custom Memory Fact
    with st.expander("Add Custom Fact", expanded=False):
        with st.form(key="add_fact_form", clear_on_submit=True, border=False):
            new_fact_val = st.text_input("Fact to remember", placeholder="e.g. Loves building AI agents", label_visibility="collapsed")
            if st.form_submit_button("Save to Vault", use_container_width=True):
                if new_fact_val and new_fact_val.strip():
                    st.session_state.memory_store.save_memory(new_fact_val.strip())
                    st.toast("Fact saved to vector memory!")
                    st.rerun()

    # B. View and Delete Individual Memories
    if mem_count > 0:
        with st.expander(f"View & Manage Facts ({mem_count})", expanded=False):
            for i, m in enumerate(memories, 1):
                f_col1, f_col2 = st.columns([5, 1])
                with f_col1:
                    st.markdown(f"<div style='font-size: 12px; line-height: 1.4; padding: 6px 8px; background: var(--surface-1); border: 1px solid var(--hairline); border-radius: 8px; color: var(--ink); word-break: break-word;'><strong>{i}.</strong> {m}</div>", unsafe_allow_html=True)
                with f_col2:
                    if st.button(" ", key=f"del_mem_{i}", icon=":material/delete_outline:", help=f"Delete fact {i}"):
                        st.session_state.memory_store.delete_memory(m)
                        st.toast("Fact removed from memory!")
                        st.rerun()
    else:
        st.markdown("<div style='font-size: 11.5px; line-height: 1.4; color: var(--ink-subtle); padding: 10px; background: var(--surface-1); border: 1px dashed var(--hairline); border-radius: 8px; margin-bottom: 10px;'>No memories stored yet. Converse with the agent or add one above!</div>", unsafe_allow_html=True)

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if st.button("Recall All", use_container_width=True, help="Ask agent to recite what it remembers about you"):
            st.session_state.quick_query = "What memories do you have stored about me? Summarize everything you know."
    with col_m2:
        if st.button("Reset All", use_container_width=True, help="Clear all stored facts in FAISS"):
            st.session_state.memory_store.clear_memory()
            st.toast("Vector memory reset!")
            st.rerun()

    st.markdown("<hr style='border: none; border-top: 1px solid var(--hairline); margin: 16px 0;'>", unsafe_allow_html=True)

    # 5. Conversation Tools
    st.markdown("""<div style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--ink-muted); margin-bottom: 8px;">ACTIONS</div>""", unsafe_allow_html=True)
    
    chat_export = f"=== Conversation: {active_chat['title']} ===\n\n"
    for m in active_chat["messages"]:
        role = "User" if m.type == "human" else "AI Agent"
        clean = re.sub(r'[*_#`]', '', m.content)
        chat_export += f"{role}: {clean}\n\n"
    
    st.download_button(
        label="Export Conversation",
        data=chat_export if active_chat["messages"] else "No messages in conversation.",
        file_name=f"{re.sub(r'[^a-zA-Z0-9_-]', '_', active_chat['title'])}.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.markdown("<hr style='border: none; border-top: 1px solid var(--hairline); margin: 16px 0;'>", unsafe_allow_html=True)

    # 5. Technical Specs & Architecture Card
    with st.expander("Architecture Specs", expanded=False):
        st.markdown("""
        <div style="font-size: 11.5px; line-height: 1.7; color: var(--ink-muted);">
            <div><strong>LLM:</strong> Gemini 3.6 Flash</div>
            <div><strong>Vector DB:</strong> FAISS Semantic Index</div>
            <div><strong>Embeddings:</strong> gemini-embedding-2</div>
            <div><strong>Audio:</strong> Google SpeechRecognition</div>
            <div><strong>Orchestration:</strong> LangChain Core</div>
        </div>
        """, unsafe_allow_html=True)

    # 6. Rishikesan Creator Branding
    st.markdown("""
    <div style="margin-top: 24px; padding: 14px; background: var(--surface-1); border: 1px solid var(--hairline); border-radius: 14px; text-align: center; box-shadow: var(--shadow-subtle);">
        <div style="font-size: 11px; color: var(--ink-subtle); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.4px;">Developed by</div>
        <div style="font-weight: 700; font-size: 15px; color: var(--ink); margin-bottom: 10px;">
            <a href="https://rishiware.com" target="_blank" style="color: var(--ink); text-decoration: none;">Rishikesan</a>
        </div>
        <div style="display: flex; justify-content: center; gap: 14px;">
            <a href="https://rishiware.com" target="_blank" title="Portfolio Website" style="color: var(--ink-muted); text-decoration: none; display: flex; align-items: center;">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            </a>
            <a href="https://linkedin.com/in/rishikesan05" target="_blank" title="LinkedIn Profile" style="color: var(--ink-muted); text-decoration: none; display: flex; align-items: center;">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>
            </a>
            <a href="https://github.com/Rishikesan05" target="_blank" title="GitHub Profile" style="color: var(--ink-muted); text-decoration: none; display: flex; align-items: center;">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
            </a>
        </div>
        <div style="font-size: 10px; color: var(--ink-subtle); margin-top: 10px;">v2.0 &bull; Production Ready</div>
    </div>
    """, unsafe_allow_html=True)



# ── Main Chat Area Header (Empty State) ──
if not st.session_state.messages:
    # Dynamic time-of-day greeting
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting_time = "Good morning"
    elif 12 <= hour < 17:
        greeting_time = "Good afternoon"
    elif 17 <= hour < 22:
        greeting_time = "Good evening"
    else:
        greeting_time = "Welcome back"

    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 4vh; text-align: center; animation: fadeIn 0.8s ease;">
        <div class="hero-aura">
            <div class="hero-logo-box">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12 2.1 7.1"/><path d="M12 12l9.9 4.9"/></svg>
            </div>
        </div>
        <h1 style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: var(--ink); font-size: 36px; letter-spacing: -0.03em; margin: 0 0 8px 0;">{greeting_time}</h1>
        <p style="color: var(--ink-muted); font-size: 16px; max-width: 540px; line-height: 1.5; margin: 0 0 32px 0;">Where should we begin? Type a message or click the mic to speak.</p>
    </div>
    <style>@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}</style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='suggestion-grid' style='max-width: 760px; margin: 0 auto 32px auto;'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Memory: What do you remember about me?", icon=":material/psychology:", key="chip_mem", use_container_width=True):
            st.session_state.quick_query = "What do you remember about me from our past conversations?"
        if st.button("Ideation: 3 unique project ideas using AI", icon=":material/lightbulb:", key="chip_idea", use_container_width=True):
            st.session_state.quick_query = "Give me 3 unique project ideas using AI."
    with col2:
        if st.button("Engineering: Python async concurrency patterns", icon=":material/code:", key="chip_code", use_container_width=True):
            st.session_state.quick_query = "Write a clean Python script demonstrating asynchronous concurrency with asyncio."
        if st.button("Coaching: Practice communication skills", icon=":material/record_voice_over:", key="chip_comm", use_container_width=True):
            st.session_state.quick_query = "I want to practice my communication skills. Act as a communication coach."
    st.markdown("</div>", unsafe_allow_html=True)

# ── Chat Display ──
for idx, msg in enumerate(st.session_state.messages):
    avatar_icon = "assets/user.svg" if msg.type == "human" else "assets/assistant.svg"
    with st.chat_message(msg.type, avatar=avatar_icon):
        if msg.type == "ai":
            is_error = getattr(msg, "additional_kwargs", {}).get("is_error", False)
            if is_error:
                st.error(clean_display_text(msg.content))
                failed_q = getattr(msg, "additional_kwargs", {}).get("failed_query", "")
                
                # Dedicated prominent Retry button
                col_btn, _ = st.columns([2, 8])
                with col_btn:
                    if st.button("Retry", icon=":material/refresh:", key=f"retry_err_{idx}", help="Click to retry generating this response"):
                        active_chat = st.session_state.chats[st.session_state.active_chat_id]
                        # Remove error AI message and preceding human message if matched
                        new_msgs = []
                        for m_idx, m in enumerate(active_chat["messages"]):
                            if m_idx == idx:
                                continue
                            if m_idx == idx - 1 and m.type == "human":
                                continue
                            new_msgs.append(m)
                        active_chat["messages"] = new_msgs
                        st.session_state.messages = active_chat["messages"]
                        if failed_q:
                            st.session_state.quick_query = failed_q
                        st.rerun()
            else:
                recalled = getattr(msg, "additional_kwargs", {}).get("recalled", "")
                if recalled:
                    items = [m.strip("- ").strip() for m in recalled.split("\n") if m.strip()]
                    count = len(items)
                    items_html = "".join(f"<li style='margin-bottom: 3px;'>{item}</li>" for item in items)
                    st.markdown(f"""
                    <details style="margin-bottom: 12px; background: var(--surface-2); border: 1px solid var(--hairline); border-radius: 10px; padding: 6px 12px; font-size: 12px; cursor: pointer;">
                        <summary style="font-weight: 600; color: var(--ink); display: flex; align-items: center; gap: 6px; user-select: none;">
                            <span style="width: 6px; height: 6px; border-radius: 50%; background: #475569; display: inline-block;"></span>
                            <span>Recalled {count} relevant facts</span>
                        </summary>
                        <ul style="margin: 6px 0 2px 0; padding-left: 18px; color: var(--ink-muted); line-height: 1.45;">
                            {items_html}
                        </ul>
                    </details>
                    """, unsafe_allow_html=True)

                st.markdown(clean_display_text(msg.content))

                latency = getattr(msg, "additional_kwargs", {}).get("latency")
                is_last_ai = (idx == len(st.session_state.messages) - 1)

                if is_last_ai:
                    col_info, col_retry = st.columns([5, 1])
                    with col_info:
                        if latency:
                            st.markdown(f"""
                            <div style="display: flex; align-items: center; margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--hairline); font-size: 11px; color: var(--ink-subtle);">
                                <span>{latency:.2f}s</span>
                            </div>
                            """, unsafe_allow_html=True)
                    with col_retry:
                        prec_q = ""
                        if idx > 0 and st.session_state.messages[idx - 1].type == "human":
                            prec_q = st.session_state.messages[idx - 1].content
                        if prec_q:
                            if st.button("Retry", icon=":material/refresh:", key="retry_last_resp", help="Regenerate this response"):
                                active_chat = st.session_state.chats[st.session_state.active_chat_id]
                                active_chat["messages"] = active_chat["messages"][:-2]
                                st.session_state.messages = active_chat["messages"]
                                st.session_state.quick_query = prec_q
                                st.rerun()
                elif latency:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; justify-content: flex-end; margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--hairline); font-size: 11px; color: var(--ink-subtle);">
                        <span>{latency:.2f}s</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown(clean_display_text(msg.content))

# Fallback for trailing unanswered human message (e.g. if previous execution was interrupted)
if st.session_state.messages and st.session_state.messages[-1].type == "human" and "quick_query" not in st.session_state:
    unanswered_q = st.session_state.messages[-1].content
    with st.chat_message("ai", avatar="assets/assistant.svg"):
        st.error("**Rate Limit Exceeded or Interrupted:** Previous response could not be generated. Please wait a moment and click **Retry** below.")
        col_r, _ = st.columns([2, 8])
        with col_r:
            if st.button("Retry", icon=":material/refresh:", key="retry_unanswered_btn", help="Retry sending this message"):
                active_chat = st.session_state.chats[st.session_state.active_chat_id]
                active_chat["messages"].pop()
                st.session_state.messages = active_chat["messages"]
                st.session_state.quick_query = unanswered_q
                st.rerun()

# ── Chat Input ──
user_query = st.chat_input("Message the agent...")

if "quick_query" in st.session_state:
    user_query = st.session_state.quick_query
    del st.session_state.quick_query

query = user_query

if query:
    active_chat = st.session_state.chats[st.session_state.active_chat_id]
    
    # Auto-generate clean conversational heading if new chat
    if active_chat.get("title") == "New Chat":
        clean_q = clean_display_text(query).strip()
        words = clean_q.split()
        short_title = " ".join(words[:4])
        if len(words) > 4 or len(clean_q) > 22:
            short_title = short_title[:20].rstrip() + "..."
        active_chat["title"] = short_title.capitalize() if short_title else "Conversation"

    active_chat["messages"].append(HumanMessage(content=query))
    st.session_state.messages = active_chat["messages"]
    
    with st.chat_message("human", avatar="assets/user.svg"):
        st.markdown(clean_display_text(query))

    with st.chat_message("ai", avatar="assets/assistant.svg"):
        start_time = time.time()

        # 1. Recall relevant memories
        with st.spinner("Thinking..."):
            past_context = st.session_state.memory_store.recall_memories(query)

        # Show citation chip if memories recalled
        if past_context:
            items = [m.strip("- ").strip() for m in past_context.split("\n") if m.strip()]
            count = len(items)
            items_html = "".join(f"<li style='margin-bottom: 3px;'>{item}</li>" for item in items)
            st.markdown(f"""
            <details style="margin-bottom: 12px; background: var(--surface-2); border: 1px solid var(--hairline); border-radius: 10px; padding: 6px 12px; font-size: 12px; cursor: pointer;">
                <summary style="font-weight: 600; color: var(--ink); display: flex; align-items: center; gap: 6px; user-select: none;">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background: #475569; display: inline-block;"></span>
                    <span>Recalled {count} relevant facts</span>
                </summary>
                <ul style="margin: 6px 0 2px 0; padding-left: 18px; color: var(--ink-muted); line-height: 1.45;">
                    {items_html}
                </ul>
            </details>
            """, unsafe_allow_html=True)

        # 2. Build system prompt with memory context
        system_prompt = "You are a helpful, intelligent AI assistant with long-term memory. Be concise, friendly, and personalized."
        if past_context:
            system_prompt += f"\n\nRelevant memories from past interactions:\n<memories>\n{past_context}\n</memories>\n\nUse these to personalize your response."

        llm = ChatGoogleGenerativeAI(model="models/gemini-3.6-flash", temperature=0.7, max_retries=2)
        messages = [SystemMessage(content=system_prompt)] + active_chat["messages"]

        # 3. Stream response
        response_placeholder = st.empty()
        full_response = ""

        try:
            for chunk in llm.stream(messages):
                piece = extract_text_content(chunk.content)
                if piece:
                    full_response += piece
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
            latency = time.time() - start_time
            active_chat["messages"].append(AIMessage(content=full_response, additional_kwargs={"recalled": past_context, "latency": latency}))
            st.session_state.messages = active_chat["messages"]

            # 4. Auto-extract and save new memory
            try:
                extract_prompt = f"Extract a concise single-sentence fact about the user to remember. If nothing specific, reply 'NONE'.\n\nUser: {query}\nAI: {full_response}\n\nFact:"
                fact_content = llm.invoke(extract_prompt).content
                fact = extract_text_content(fact_content).strip()

                if fact and "NONE" not in fact.upper():
                    st.session_state.memory_store.save_memory(fact)
                    st.markdown(f"<div class='mem-toast'>Learned: {fact}</div>", unsafe_allow_html=True)
            except Exception:
                pass

            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--hairline); font-size: 11px; color: var(--ink-subtle);">
                <span>{latency:.2f}s</span>
            </div>
            """, unsafe_allow_html=True)
            st.rerun()

        except Exception as e:
            error_msg = str(e)
            is_rate_limit = "429" in error_msg or "ResourceExhausted" in error_msg
            if is_rate_limit:
                clean_err = "**Rate Limit Exceeded:** Gemini API request limit reached. Please wait a few seconds and click **Retry** below."
            else:
                clean_err = f"**Error:** {error_msg}"

            error_ai_msg = AIMessage(
                content=clean_err,
                additional_kwargs={
                    "is_error": True,
                    "error_type": "rate_limit" if is_rate_limit else "general",
                    "failed_query": query
                }
            )
            active_chat["messages"].append(error_ai_msg)
            st.session_state.messages = active_chat["messages"]
            st.rerun()


