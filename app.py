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
        background: radial-gradient(circle, rgba(99, 102, 241, 0.35) 0%, rgba(168, 85, 247, 0.2) 45%, transparent 70%);
        filter: blur(24px);
        z-index: 0;
        animation: auraFloat 5s ease-in-out infinite alternate;
    }
    @keyframes auraFloat {
        0% { transform: scale(0.9); opacity: 0.65; }
        100% { transform: scale(1.22); opacity: 1; }
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
        padding: 0 !important;
        pointer-events: none !important;
    }
    [data-testid="stBottomBlockContainer"] {
        padding: 0 !important;
    }

    /* Container for the two side buttons and audio */
    [data-testid="stHorizontalBlock"]:has(.action-btn-left),
    [data-testid="stLayoutWrapper"]:has(.action-btn-left),
    [data-testid="stElementContainer"]:has([data-testid="stAudioInput"]) {
        position: static !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* ── UNIFIED 3-PART LUXURY BOTTOM DOCK (Desktop) ── */
    /* Dock width: 46px [+] + 10px + 490px [input] + 10px + 200px [voice] = 756px */

    /* 1. Left '+' Button (New Chat & Conversations Menu) */
    [data-testid="stColumn"]:has(.action-btn-left) {
        position: fixed !important;
        bottom: 22px !important;
        left: calc(50% - 378px) !important;
        z-index: 1001 !important;
        width: 46px !important;
        min-width: 46px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 2. Center Chat Input */
    .stChatInput {
        padding-bottom: 0 !important;
        margin-bottom: 0 !important;
    }
    .stChatInput > div {
        position: fixed !important;
        bottom: 22px !important;
        left: calc(50% - 262px) !important;
        width: 524px !important;
        max-width: 524px !important;
        height: 46px !important;
        min-height: 46px !important;
        margin: 0 !important;
        border-radius: var(--radius-pill) !important;
        border: 1px solid var(--hairline) !important;
        background: var(--surface-1) !important;
        box-shadow: var(--shadow-floating) !important;
        padding: 4px 10px 4px 18px !important;
        transition: all 0.25s ease !important;
        pointer-events: auto !important;
        display: flex !important;
        align-items: center !important;
        z-index: 1000 !important;
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
        margin: 0 !important;
    }

    /* Responsive Mobile Layout for Bottom Dock */
    @media (max-width: 820px) {
        [data-testid="stColumn"]:has(.action-btn-left) {
            left: 12px !important;
            bottom: 16px !important;
            width: 40px !important;
            min-width: 40px !important;
        }
        [data-testid="stColumn"]:has(.action-btn-left) [data-testid="stPopover"] button {
            width: 40px !important;
            height: 40px !important;
            min-width: 40px !important;
            min-height: 40px !important;
        }
        .stChatInput > div {
            left: 58px !important;
            width: calc(100% - 114px) !important;
            max-width: calc(100% - 114px) !important;
            bottom: 16px !important;
            height: 40px !important;
            min-height: 40px !important;
        }
    }

    /* Base styling for circular floating '+' action button */
    [data-testid="stColumn"]:has(.action-btn-left) {
        position: fixed !important;
        bottom: 22px !important;
        left: calc(50% - 320px) !important;
        width: 46px !important;
        min-width: 46px !important;
        max-width: 46px !important;
        height: 46px !important;
        min-height: 46px !important;
        z-index: 1000 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    @media (min-width: 821px) {
        [data-testid="stSidebar"][aria-expanded="true"] ~ * [data-testid="stColumn"]:has(.action-btn-left) {
            left: calc(50% + 150px - 320px) !important;
        }
        [data-testid="stSidebar"][aria-expanded="true"] ~ * .stChatInput > div {
            left: calc(50% + 150px - 262px) !important;
        }
    }
    [data-testid="stColumn"]:has(.action-btn-left) {
        position: fixed !important;
        bottom: 22px !important;
        left: calc(50% - 320px) !important;
        width: 46px !important;
        min-width: 46px !important;
        max-width: 46px !important;
        height: 46px !important;
        min-height: 46px !important;
        z-index: 1000 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    [data-testid="stColumn"]:has(.action-btn-left) [data-testid="stPopover"] button {
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

        // 3. WhatsApp-Style Voice Recorder Component
        (function() {
            const parentDoc = window.parent.document;
            if (parentDoc.getElementById('wa-voice-container')) return;

            const styleEl = parentDoc.createElement('style');
            styleEl.innerHTML = `
                #wa-voice-container {
                    position: fixed;
                    bottom: 22px;
                    left: calc(50% + 150px + 274px);
                    z-index: 10001;
                    font-family: 'Plus Jakarta Sans', sans-serif;
                }
                @media (max-width: 820px) {
                    #wa-voice-container {
                        left: auto !important;
                        right: 12px !important;
                        bottom: 16px !important;
                    }
                }
                #wa-mic-btn {
                    width: 46px;
                    height: 46px;
                    border-radius: 50%;
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                    color: #0f172a;
                }
                #wa-mic-btn:hover {
                    transform: scale(1.06);
                    border-color: #94a3b8;
                    box-shadow: 0 12px 28px rgba(0,0,0,0.12);
                }
                #wa-record-bar {
                    display: none;
                    position: fixed;
                    bottom: 22px;
                    left: calc(50% + 150px - 262px);
                    width: 582px;
                    height: 46px;
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 9999px;
                    box-shadow: 0 14px 35px -5px rgba(0, 0, 0, 0.12);
                    z-index: 10002;
                    align-items: center;
                    justify-content: space-between;
                    padding: 0 12px;
                    box-sizing: border-box;
                    animation: waSlideUp 0.22s cubic-bezier(0.16, 1, 0.3, 1);
                }
                @media (max-width: 820px) {
                    #wa-record-bar {
                        left: 12px !important;
                        right: 12px !important;
                        width: calc(100% - 24px) !important;
                        bottom: 16px !important;
                    }
                }
                @keyframes waSlideUp {
                    from { opacity: 0; transform: translateY(8px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .wa-rec-dot {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: #ef4444;
                    animation: waPulse 1.2s infinite;
                }
                @keyframes waPulse {
                    0% { transform: scale(0.85); opacity: 0.6; }
                    50% { transform: scale(1.25); opacity: 1; box-shadow: 0 0 10px rgba(239, 68, 68, 0.6); }
                    100% { transform: scale(0.85); opacity: 0.6; }
                }
                .wa-action-btn {
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    border: none;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.15s ease;
                }
                .wa-trash-btn {
                    background: #fee2e2;
                    color: #ef4444;
                }
                .wa-trash-btn:hover {
                    background: #fecaca;
                    transform: scale(1.08);
                }
                .wa-pause-btn {
                    background: #f1f5f9;
                    color: #0f172a;
                }
                .wa-pause-btn:hover {
                    background: #e2e8f0;
                    transform: scale(1.08);
                }
                .wa-send-btn {
                    background: #10b981;
                    color: #ffffff;
                    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
                }
                .wa-send-btn:hover {
                    background: #059669;
                    transform: scale(1.08);
                }
                .wa-timer {
                    font-size: 14px;
                    font-weight: 600;
                    color: #ef4444;
                    font-variant-numeric: tabular-nums;
                    min-width: 44px;
                }
                .wa-waveform {
                    display: flex;
                    align-items: center;
                    gap: 3px;
                    height: 24px;
                    flex: 1;
                    max-width: 220px;
                    justify-content: center;
                }
                .wa-wave-bar {
                    width: 3px;
                    height: 6px;
                    border-radius: 3px;
                    background: #6366f1;
                    transition: height 0.08s ease;
                }
            `;
            parentDoc.head.appendChild(styleEl);

            const container = parentDoc.createElement('div');
            container.id = 'wa-voice-container';
            container.innerHTML = `
                <div id="wa-mic-btn" title="Voice record like WhatsApp">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                        <line x1="12" x2="12" y1="19" y2="22"/>
                    </svg>
                </div>
                <div id="wa-record-bar">
                    <button id="wa-btn-trash" class="wa-action-btn wa-trash-btn" title="Delete recording">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                        </svg>
                    </button>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div class="wa-rec-dot" id="wa-rec-dot"></div>
                        <div class="wa-timer" id="wa-timer">00:00</div>
                    </div>
                    <div class="wa-waveform" id="wa-waveform">
                        ${Array(16).fill(0).map(() => '<div class="wa-wave-bar"></div>').join('')}
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button id="wa-btn-pause" class="wa-action-btn wa-pause-btn" title="Pause / Continue">
                            <svg id="wa-icon-pause" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
                                <rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>
                            </svg>
                            <svg id="wa-icon-play" style="display: none; margin-left: 2px;" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <polygon points="6,4 20,12 6,20"/>
                            </svg>
                        </button>
                        <button id="wa-btn-send" class="wa-action-btn wa-send-btn" title="Send voice message">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
            parentDoc.body.appendChild(container);

            let isRecording = false;
            let isPaused = false;
            let mediaRecorder = null;
            let audioStream = null;
            let audioContext = null;
            let analyser = null;
            let animFrame = null;
            let timerInterval = null;
            let secondsElapsed = 0;
            let recognition = null;
            let finalTranscript = '';

            const micBtn = parentDoc.getElementById('wa-mic-btn');
            const recordBar = parentDoc.getElementById('wa-record-bar');
            const trashBtn = parentDoc.getElementById('wa-btn-trash');
            const pauseBtn = parentDoc.getElementById('wa-btn-pause');
            const sendBtn = parentDoc.getElementById('wa-btn-send');
            const timerEl = parentDoc.getElementById('wa-timer');
            const iconPause = parentDoc.getElementById('wa-icon-pause');
            const iconPlay = parentDoc.getElementById('wa-icon-play');
            const waveBars = parentDoc.querySelectorAll('.wa-wave-bar');
            const recDot = parentDoc.getElementById('wa-rec-dot');

            function formatTime(secs) {
                const m = Math.floor(secs / 60).toString().padStart(2, '0');
                const s = (secs % 60).toString().padStart(2, '0');
                return `${m}:${s}`;
            }

            function updateWaveform() {
                if (!isRecording || isPaused) return;
                if (analyser) {
                    const dataArray = new Uint8Array(analyser.frequencyBinCount);
                    analyser.getByteFrequencyData(dataArray);
                    waveBars.forEach((bar, idx) => {
                        const val = dataArray[idx * 2] || 0;
                        const h = Math.max(4, Math.min(22, (val / 255) * 22 + 4));
                        bar.style.height = `${h}px`;
                    });
                } else {
                    waveBars.forEach((bar) => {
                        const h = Math.floor(Math.random() * 16) + 4;
                        bar.style.height = `${h}px`;
                    });
                }
                animFrame = requestAnimationFrame(updateWaveform);
            }

            async function startRecording() {
                try {
                    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const source = audioContext.createMediaStreamSource(audioStream);
                    analyser = audioContext.createAnalyser();
                    analyser.fftSize = 64;
                    source.connect(analyser);

                    mediaRecorder = new MediaRecorder(audioStream);
                    mediaRecorder.start();

                    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
                    if (SpeechRec) {
                        recognition = new SpeechRec();
                        recognition.continuous = true;
                        recognition.interimResults = true;
                        recognition.lang = 'en-US';
                        finalTranscript = '';
                        recognition.onresult = (event) => {
                            let text = '';
                            for (let i = 0; i < event.results.length; i++) {
                                text += event.results[i][0].transcript + ' ';
                            }
                            finalTranscript = text.trim();
                        };
                        recognition.start();
                    }

                    isRecording = true;
                    isPaused = false;
                    secondsElapsed = 0;
                    timerEl.innerText = "00:00";
                    iconPause.style.display = "block";
                    iconPlay.style.display = "none";
                    recDot.style.animationPlayState = "running";

                    recordBar.style.display = "flex";
                    micBtn.style.display = "none";

                    timerInterval = setInterval(() => {
                        if (!isPaused) {
                            secondsElapsed++;
                            timerEl.innerText = formatTime(secondsElapsed);
                        }
                    }, 1000);

                    updateWaveform();
                } catch (err) {
                    console.error("Mic access denied or error:", err);
                    alert("Microphone access denied. Please allow microphone permissions in your browser.");
                }
            }

            function stopAndCleanup() {
                isRecording = false;
                isPaused = false;
                if (timerInterval) clearInterval(timerInterval);
                if (animFrame) cancelAnimationFrame(animFrame);
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                    try { mediaRecorder.stop(); } catch(e) {}
                }
                if (audioStream) {
                    audioStream.getTracks().forEach(track => track.stop());
                }
                if (audioContext && audioContext.state !== 'closed') {
                    try { audioContext.close(); } catch(e) {}
                }
                if (recognition) {
                    try { recognition.stop(); } catch(e) {}
                }
                recordBar.style.display = "none";
                micBtn.style.display = "flex";
            }

            trashBtn.onclick = () => {
                finalTranscript = '';
                stopAndCleanup();
            };

            pauseBtn.onclick = () => {
                if (!isRecording) return;
                if (!isPaused) {
                    isPaused = true;
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        mediaRecorder.pause();
                    }
                    if (recognition) {
                        try { recognition.stop(); } catch(e) {}
                    }
                    iconPause.style.display = "none";
                    iconPlay.style.display = "block";
                    recDot.style.animationPlayState = "paused";
                    waveBars.forEach(bar => bar.style.height = '6px');
                } else {
                    isPaused = false;
                    if (mediaRecorder && mediaRecorder.state === 'paused') {
                        mediaRecorder.resume();
                    }
                    if (recognition) {
                        try { recognition.start(); } catch(e) {}
                    }
                    iconPause.style.display = "block";
                    iconPlay.style.display = "none";
                    recDot.style.animationPlayState = "running";
                    updateWaveform();
                }
            };

            sendBtn.onclick = () => {
                const textToSend = finalTranscript.trim();
                stopAndCleanup();

                if (textToSend) {
                    const textarea = parentDoc.querySelector('.stChatInput textarea');
                    const submitBtn = parentDoc.querySelector('[data-testid="stChatInputSubmitButton"]');
                    if (textarea && submitBtn) {
                        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                        nativeSetter.call(textarea, textToSend);
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        setTimeout(() => {
                            submitBtn.click();
                        }, 80);
                    }
                }
            };

            micBtn.onclick = startRecording;
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
    # 1. Brand Identity
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding: 4px 0;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #334155 100%); border-radius: 12px; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.12); flex-shrink: 0;">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12 2.1 7.1"/><path d="M12 12l9.9 4.9"/></svg>
        </div>
        <div>
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 16.5px; color: var(--ink); line-height: 1.2;">Custom AI Agent</div>
            <div style="font-size: 11.5px; color: var(--ink-muted); font-weight: 500;">Persistent Vector Memory</div>
        </div>
    </div>
    <div style="display: inline-flex; align-items: center; gap: 6px; background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 9999px; margin-bottom: 16px;">
        <span style="width: 6px; height: 6px; border-radius: 50%; background: #10b981; display: inline-block;"></span>
        FAISS Vector Store Active
    </div>
    """, unsafe_allow_html=True)

    # 2. Primary Action: New Chat
    if st.button("New Chat", icon=":material/add:", use_container_width=True, key="new_chat_btn", help="Start a new conversation"):
        new_id = f"chat_{int(time.time() * 1000)}"
        st.session_state.chats[new_id] = {
            "id": new_id,
            "title": "New Chat",
            "messages": [],
            "created_at": time.time(),
        }
        st.session_state.active_chat_id = new_id
        st.rerun()

    # 3. Chat Bars (Recent Conversations)
    total_chats = len(st.session_state.chats)
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin: 12px 0 6px 0;">
        <span style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--ink-muted);">Conversations</span>
        <span style="background: var(--surface-3); font-size: 11px; font-weight: 600; color: var(--ink); padding: 2px 8px; border-radius: 9999px;">{total_chats}</span>
    </div>
    """, unsafe_allow_html=True)

    with st.container(height=190):
        sorted_chats = sorted(st.session_state.chats.items(), key=lambda x: x[1].get("created_at", 0), reverse=True)
        for c_id, c_data in sorted_chats:
            is_active = (c_id == st.session_state.active_chat_id)
            
            # Automatically resolve real conversation title from first human message
            title_text = c_data.get("title", "New Chat")
            if (title_text == "New Chat" or not title_text) and c_data.get("messages"):
                for m in c_data["messages"]:
                    if m.type == "human" and m.content:
                        clean_t = clean_display_text(m.content).strip()
                        words = clean_t.split()
                        short_t = " ".join(words[:4])
                        if len(words) > 4 or len(clean_t) > 22:
                            short_t = short_t[:20].rstrip() + "..."
                        if short_t:
                            title_text = short_t
                            c_data["title"] = short_t
                        break

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
                    if len(st.session_state.chats) > 1:
                        del st.session_state.chats[c_id]
                        if st.session_state.active_chat_id == c_id:
                            st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
                    else:
                        st.session_state.chats[c_id]["messages"] = []
                        st.session_state.chats[c_id]["title"] = "New Chat"
                    st.rerun()

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
        new_fact_val = st.text_input("Fact to remember", placeholder="e.g. Loves building AI agents", label_visibility="collapsed", key="input_custom_fact")
        if st.button("Save to Vault", use_container_width=True, key="btn_save_custom_fact"):
            if new_fact_val.strip():
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
            <div><strong>LLM:</strong> Gemini 3.5 Flash</div>
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
    mem_count = len(st.session_state.memory_store.get_all_memories())
    
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
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 2vh; text-align: center; animation: fadeIn 0.8s ease;">
        <div style="display: inline-flex; align-items: center; gap: 6px; background: var(--surface-2); border: 1px solid var(--hairline); color: var(--ink-muted); font-size: 11.5px; font-weight: 600; padding: 4px 14px; border-radius: 9999px; margin-bottom: 20px; box-shadow: var(--shadow-subtle);">
            <span style="width: 7px; height: 7px; border-radius: 50%; background: #10b981; display: inline-block;"></span>
            FAISS VECTOR MEMORY ACTIVE &bull; {mem_count} FACTS STORED
        </div>
        <div class="hero-aura">
            <div class="hero-logo-box">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12 2.1 7.1"/><path d="M12 12l9.9 4.9"/></svg>
            </div>
        </div>
        <h1 style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: var(--ink); font-size: 36px; letter-spacing: -0.03em; margin: 0 0 8px 0;">{greeting_time}</h1>
        <p style="color: var(--ink-muted); font-size: 16px; max-width: 540px; line-height: 1.5; margin: 0 0 32px 0;">Your autonomous AI assistant powered by Gemini 3.5 Flash with persistent long-term semantic memory across conversations.</p>
    </div>
    <style>@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}</style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='suggestion-grid' style='max-width: 760px; margin: 0 auto 32px auto;'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Memory Vault: What do you remember about me?", icon=":material/psychology:", key="chip_mem", use_container_width=True):
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
for msg in st.session_state.messages:
    avatar_icon = "assets/user.svg" if msg.type == "human" else "assets/assistant.svg"
    with st.chat_message(msg.type, avatar=avatar_icon):
        if msg.type == "ai":
            recalled = getattr(msg, "additional_kwargs", {}).get("recalled", "")
            if recalled:
                items = [m.strip("- ").strip() for m in recalled.split("\n") if m.strip()]
                count = len(items)
                items_html = "".join(f"<li style='margin-bottom: 3px;'>{item}</li>" for item in items)
                st.markdown(f"""
                <details style="margin-bottom: 12px; background: var(--surface-2); border: 1px solid var(--hairline); border-radius: 10px; padding: 6px 12px; font-size: 12px; cursor: pointer;">
                    <summary style="font-weight: 600; color: var(--ink); display: flex; align-items: center; gap: 6px; user-select: none;">
                        <span style="width: 6px; height: 6px; border-radius: 50%; background: #10b981; display: inline-block;"></span>
                        <span>Recalled {count} facts from your Memory Vault</span>
                    </summary>
                    <ul style="margin: 6px 0 2px 0; padding-left: 18px; color: var(--ink-muted); line-height: 1.45;">
                        {items_html}
                    </ul>
                </details>
                """, unsafe_allow_html=True)

        st.markdown(clean_display_text(msg.content))

        if msg.type == "ai":
            latency = getattr(msg, "additional_kwargs", {}).get("latency")
            if latency:
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--hairline); font-size: 11px; color: var(--ink-muted);">
                    <span>Responded in {latency:.2f}s &bull; Gemini 3.5 Flash</span>
                    <span style="color: var(--ink-subtle);">Long-Term Vector Context Active</span>
                </div>
                """, unsafe_allow_html=True)

# ── Fixed Bottom Elements (+ button) ──
dock_col, _ = st.columns([1, 99])
with dock_col:
    st.markdown("<div class='action-btn-left' style='display: none;'></div>", unsafe_allow_html=True)
    with st.popover(" ", icon=":material/add:", help="New Chat or Switch Conversations"):
        st.markdown("<div style='font-weight: 700; font-size: 14px; margin-bottom: 8px; color: var(--ink);'>Conversations</div>", unsafe_allow_html=True)
        if st.button("Start New Chat", icon=":material/add_comment:", use_container_width=True, key="pop_new_chat"):
            new_id = f"chat_{int(time.time() * 1000)}"
            st.session_state.chats[new_id] = {
                "id": new_id,
                "title": "New Chat",
                "messages": [],
                "created_at": time.time(),
            }
            st.session_state.active_chat_id = new_id
            st.rerun()
        
        st.markdown("<div style='font-size: 11px; font-weight: 700; color: var(--ink-muted); margin: 12px 0 6px 0; text-transform: uppercase; letter-spacing: 0.5px;'>Recent Chats</div>", unsafe_allow_html=True)
        pop_sorted_chats = sorted(st.session_state.chats.items(), key=lambda x: x[1].get("created_at", 0), reverse=True)
        for c_id, c_data in pop_sorted_chats[:6]:
            is_active = (c_id == st.session_state.active_chat_id)
            title = c_data.get("title", "New Chat")
            display_title = title[:24] + "..." if len(title) > 26 else title
            icon_name = ":material/check_circle:" if is_active else ":material/chat_bubble_outline:"
            btn_type = "primary" if is_active else "secondary"
            if st.button(display_title, key=f"pop_chat_{c_id}", icon=icon_name, use_container_width=True, type=btn_type):
                st.session_state.active_chat_id = c_id
                st.rerun()

        st.markdown("<hr style='border: none; border-top: 1px solid var(--hairline); margin: 12px 0 8px 0;'>", unsafe_allow_html=True)
        if st.button("Reset Long-Term Memory", icon=":material/delete_outline:", use_container_width=True, help="Clear FAISS vector store"):
            st.session_state.memory_store.clear_memory()
            st.toast("Long-term memory cleared!")
            st.rerun()

# ── Chat Input ──
user_query = st.chat_input("Message the agent...")

if "quick_query" in st.session_state:
    user_query = st.session_state.quick_query
    del st.session_state.quick_query

query = user_query

if query:
    active_chat = st.session_state.chats[st.session_state.active_chat_id]
    
    # Auto-generate conversational title if still default
    if active_chat["title"] == "New Chat":
        words = query.strip().split()
        short_title = " ".join(words[:5])
        if len(words) > 5 or len(query.strip()) > 26:
            short_title = short_title[:24].rstrip() + "..."
        active_chat["title"] = short_title if short_title else "Chat"

    active_chat["messages"].append(HumanMessage(content=query))
    st.session_state.messages = active_chat["messages"]
    
    with st.chat_message("human", avatar="assets/user.svg"):
        st.markdown(clean_display_text(query))

    with st.chat_message("ai", avatar="assets/assistant.svg"):
        start_time = time.time()

        # 1. Recall relevant memories
        with st.spinner("Recalling memory..."):
            past_context = st.session_state.memory_store.recall_memories(query)

        # Show citation chip if memories recalled
        if past_context:
            items = [m.strip("- ").strip() for m in past_context.split("\n") if m.strip()]
            count = len(items)
            items_html = "".join(f"<li style='margin-bottom: 3px;'>{item}</li>" for item in items)
            st.markdown(f"""
            <details style="margin-bottom: 12px; background: var(--surface-2); border: 1px solid var(--hairline); border-radius: 10px; padding: 6px 12px; font-size: 12px; cursor: pointer;">
                <summary style="font-weight: 600; color: var(--ink); display: flex; align-items: center; gap: 6px; user-select: none;">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background: #10b981; display: inline-block;"></span>
                    <span>Recalled {count} facts from your Memory Vault</span>
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

        llm = ChatGoogleGenerativeAI(model="models/gemini-3.5-flash", temperature=0.7)
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
            extract_prompt = f"Extract a concise single-sentence fact about the user to remember. If nothing specific, reply 'NONE'.\n\nUser: {query}\nAI: {full_response}\n\nFact:"
            fact_content = llm.invoke(extract_prompt).content
            fact = extract_text_content(fact_content).strip()

            if fact and "NONE" not in fact.upper():
                st.session_state.memory_store.save_memory(fact)
                st.markdown(f"<div class='mem-toast'>Learned: {fact}</div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--hairline); font-size: 11px; color: var(--ink-muted);">
                <span>Responded in {latency:.2f}s &bull; Gemini 3.5 Flash</span>
                <span style="color: var(--ink-subtle);">Long-Term Vector Context Active</span>
            </div>
            """, unsafe_allow_html=True)
            st.rerun()

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "ResourceExhausted" in error_msg:
                st.error("**Rate Limit Exceeded:** Please wait 30 seconds and try again.")
            else:
                st.error(f"**Error:** {error_msg}")

