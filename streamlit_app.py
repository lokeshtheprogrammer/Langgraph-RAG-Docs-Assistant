"""
RAG Technical Documentation Assistant — Streamlit UI
A premium, human-centric interface for the self-corrective RAG pipeline.
"""

import streamlit as st
import requests
import uuid
import json
import time

# ─── Configuration ───────────────────────────────────────────────────────────
API_BASE = "http://127.0.0.1:8000"

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Documentation Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Premium CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Design Tokens — Deep Ocean Palette ── */
    :root {
        /* Backgrounds — layered deep navy */
        --bg-base:        #060b18;
        --bg-raised:      #0d1628;
        --bg-overlay:     #111f3a;
        --bg-glass:       rgba(14,165,233,0.03);
        /* Borders */
        --border-subtle:  rgba(255,255,255,0.07);
        --border-glow:    rgba(14,165,233,0.4);
        /* Accents — electric sky & cyan */
        --accent-1:       #0ea5e9;   /* sky-500 */
        --accent-2:       #38bdf8;   /* sky-400 */
        --accent-indigo:  #818cf8;   /* indigo-400 */
        --accent-warm:    #f59e0b;
        --accent-green:   #10b981;
        --accent-red:     #ef4444;
        --accent-cyan:    #22d3ee;   /* cyan-400 */
        /* Text */
        --text-primary:   #e2eaf4;
        --text-secondary: #8fa8c8;
        --text-muted:     #3d5470;
        /* Shape */
        --radius-sm:      8px;
        --radius-md:      14px;
        --radius-lg:      22px;
        /* Shadows */
        --shadow-ambient: 0 0 80px rgba(14,165,233,0.07);
        --shadow-card:    0 4px 28px rgba(0,0,0,0.5);
        /* Fonts */
        --font-sans:      'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono:      'JetBrains Mono', 'Courier New', monospace;
    }

    /* ── Global Reset ── */
    *, *::before, *::after { box-sizing: border-box; }

    html, body, .stApp {
        background: var(--bg-base) !important;
        font-family: var(--font-sans) !important;
        color: var(--text-primary) !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Deep ocean ambient glow */
    .stApp::before {
        content: '';
        position: fixed;
        top: -25vh;
        left: 50%;
        transform: translateX(-50%);
        width: 90vw;
        height: 65vh;
        background:
            radial-gradient(ellipse 60% 50% at 30% 0%, rgba(14,165,233,0.08) 0%, transparent 60%),
            radial-gradient(ellipse 50% 40% at 70% 0%, rgba(34,211,238,0.05) 0%, transparent 60%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Force text contrast everywhere ── */
    .stApp p, .stApp li, .stApp label, .stApp span:not(.badge),
    .stApp div:not(.metric-value), .stApp h1, .stApp h2,
    .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: var(--text-primary) !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: var(--bg-raised) !important;
        border-right: 1px solid var(--border-subtle) !important;
        box-shadow: 4px 0 40px rgba(0,0,0,0.4) !important;
    }
    section[data-testid="stSidebar"] > div { padding-top: 0 !important; }
    
    /* Stronger contrast overrides inside sidebar */
    section[data-testid="stSidebar"] *,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] .stMarkdown {
        color: var(--text-secondary) !important;
    }
    section[data-testid="stSidebar"] strong {
        color: var(--text-primary) !important;
    }

    /* ── Sidebar Brand Header ── */
    .brand-header {
        padding: 24px 20px 16px;
        border-bottom: 1px solid var(--border-subtle);
        margin-bottom: 4px;
    }
    .brand-logo {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #e0f2fe 0%, #38bdf8 45%, #0ea5e9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        display: block;
        line-height: 1.2;
    }
    .brand-tag {
        font-size: 0.68rem;
        color: var(--text-muted) !important;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 3px;
    }

    /* ── API Status Pill ── */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        margin: 8px 20px 0;
    }
    .status-online {
        background: rgba(14,165,233,0.10);
        color: #38bdf8 !important;
        border: 1px solid rgba(14,165,233,0.25);
    }
    .status-offline {
        background: rgba(239,68,68,0.10);
        color: #f87171 !important;
        border: 1px solid rgba(239,68,68,0.25);
    }
    .status-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-online .status-dot { background: #0ea5e9; animation: pulse-sky 2s infinite; }
    .status-offline .status-dot { background: #ef4444; }

    @keyframes pulse-sky {
        0%, 100% { box-shadow: 0 0 0 0 rgba(14,165,233,0.5); }
        50%       { box-shadow: 0 0 0 6px rgba(14,165,233,0); }
    }

    /* ── Expanders in sidebar ── */
    section[data-testid="stSidebar"] [data-testid="stExpander"] {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        border-bottom: 1px solid var(--border-subtle) !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary {
        padding: 12px 20px !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.4px !important;
        color: var(--text-secondary) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        color: var(--text-primary) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] > div > div {
        padding: 0 20px 16px !important;
    }

    /* ── Sidebar Stats Cards ── */
    .sidebar-stat-card {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        padding: 10px 6px !important;
        text-align: center;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
    }
    .sidebar-stat-label {
        font-size: 0.62rem !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--text-secondary) !important;
        opacity: 0.75;
        margin-bottom: 4px;
    }
    .sidebar-stat-num {
        font-size: 1.15rem !important;
        font-weight: 700;
        color: var(--text-primary) !important;
        font-family: var(--font-mono), monospace;
    }

    /* ── Sidebar custom buttons ── */
    section[data-testid="stSidebar"] button {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background-color: rgba(14, 165, 233, 0.08) !important;
        border-color: rgba(14, 165, 233, 0.3) !important;
        color: var(--accent-2) !important;
        box-shadow: 0 2px 10px rgba(14, 165, 233, 0.1) !important;
    }

    /* ── Main Layout ── */
    .block-container {
        max-width: 900px !important;
        padding: 40px 32px 120px !important;
        margin: 0 auto !important;
        position: relative;
        z-index: 1;
    }

    /* ── Page Header ── */
    .page-header {
        text-align: center;
        margin-bottom: 40px;
        padding-top: 8px;
    }
    .page-title {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.8px;
        background: linear-gradient(135deg, #e0f2fe 0%, #38bdf8 40%, #0ea5e9 70%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.2;
    }
    .page-subtitle {
        font-size: 0.88rem;
        color: var(--text-muted) !important;
        margin-top: 8px;
        font-weight: 400;
        letter-spacing: 0.2px;
    }

    /* ── Chat Container ── */
    .chat-wrap { display: flex; flex-direction: column; gap: 20px; }

    /* ── User Message ── */
    .msg-row-user {
        display: flex;
        justify-content: flex-end;
        align-items: flex-end;
        gap: 10px;
        animation: slideInRight 0.35s cubic-bezier(0.34,1.56,0.64,1);
    }
    @keyframes slideInRight {
        from { opacity:0; transform:translateX(20px) scale(0.96); }
        to   { opacity:1; transform:translateX(0)    scale(1); }
    }
    .user-bubble {
        background: linear-gradient(135deg, #0369a1 0%, #0ea5e9 60%, #38bdf8 100%);
        color: #fff !important;
        padding: 13px 18px;
        border-radius: 20px 20px 5px 20px;
        max-width: 72%;
        font-size: 0.93rem;
        line-height: 1.6;
        box-shadow: 0 6px 22px rgba(14,165,233,0.35), 0 1px 4px rgba(0,0,0,0.25);
        word-break: break-word;
    }
    .user-avatar {
        width: 32px; height: 32px;
        background: linear-gradient(135deg, #0369a1, #0ea5e9);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem;
        flex-shrink: 0;
        box-shadow: 0 3px 12px rgba(14,165,233,0.4);
    }

    /* ── Assistant Message ── */
    .msg-row-bot {
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 10px;
        animation: slideInLeft 0.35s cubic-bezier(0.34,1.56,0.64,1);
    }
    @keyframes slideInLeft {
        from { opacity:0; transform:translateX(-20px) scale(0.96); }
        to   { opacity:1; transform:translateX(0)     scale(1); }
    }
    .bot-avatar {
        width: 32px; height: 32px;
        background: linear-gradient(135deg, #082f49, #0c4a6e);
        border: 1px solid rgba(14,165,233,0.3);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem;
        flex-shrink: 0;
        box-shadow: 0 3px 10px rgba(0,0,0,0.35);
    }
    .bot-bubble {
        background: var(--bg-raised);
        border: 1px solid var(--border-subtle);
        color: var(--text-primary) !important;
        padding: 14px 18px;
        border-radius: 5px 20px 20px 20px;
        max-width: 82%;
        font-size: 0.93rem;
        line-height: 1.7;
        box-shadow: var(--shadow-card);
        word-break: break-word;
        position: relative;
    }
    .bot-bubble::before {
        content: '';
        position: absolute;
        top: -1px; left: -1px; right: -1px; bottom: -1px;
        border-radius: inherit;
        background: linear-gradient(135deg, rgba(14,165,233,0.09) 0%, rgba(34,211,238,0.04) 40%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }
    .bot-bubble > * { position: relative; z-index: 1; }

    /* ── Source Chips ── */
    .source-row {
        display: flex; flex-wrap: wrap; gap: 6px;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid var(--border-subtle);
    }
    .source-chip {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(14,165,233,0.08);
        border: 1px solid rgba(14,165,233,0.22);
        color: #7dd3fc !important;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-family: var(--font-mono);
        font-weight: 500;
        transition: background 0.2s, border-color 0.2s;
        cursor: default;
    }
    .source-chip:hover { background: rgba(14,165,233,0.15); border-color: rgba(14,165,233,0.4); }

    /* ── Feedback Row ── */
    .feedback-row {
        display: flex; align-items: center; gap: 8px;
        margin-top: 8px;
        padding-left: 42px;
    }
    .feedback-label {
        font-size: 0.72rem;
        color: var(--text-muted) !important;
        letter-spacing: 0.3px;
    }

    /* ── Debug Panel ── */
    .debug-panel {
        background: var(--bg-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        margin-top: 8px;
        margin-left: 42px;
        overflow: hidden;
        box-shadow: var(--shadow-card);
    }
    .debug-header-bar {
        padding: 10px 16px;
        background: rgba(14,165,233,0.06);
        border-bottom: 1px solid var(--border-subtle);
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #38bdf8 !important;
        display: flex; align-items: center; gap: 8px;
    }
    .debug-body { padding: 14px 16px; }

    /* ── Stat Chips row ── */
    .stat-row {
        display: flex; flex-wrap: wrap; gap: 8px;
        margin-bottom: 14px;
    }
    .stat-chip {
        background: var(--bg-overlay);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        padding: 6px 12px;
        font-size: 0.75rem;
        display: flex; flex-direction: column; gap: 2px;
        min-width: 90px;
    }
    .stat-chip-label {
        color: var(--text-muted) !important;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .stat-chip-value {
        color: var(--text-primary) !important;
        font-family: var(--font-mono);
        font-size: 0.82rem;
        font-weight: 500;
    }

    /* ── Chunk Cards ── */
    .chunk-card {
        background: var(--bg-overlay);
        border-left: 3px solid var(--accent-1);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 0.82rem;
        transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    }
    .chunk-card:hover { transform: translateX(4px); background: rgba(14,165,233,0.04); }
    .chunk-card.relevant { border-left-color: var(--accent-green); }
    .chunk-card.relevant:hover { background: rgba(16,185,129,0.05); }
    .chunk-card.irrelevant { border-left-color: var(--accent-red); }
    .chunk-card.irrelevant:hover { background: rgba(239,68,68,0.04); }

    .chunk-meta {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--text-muted) !important;
        margin-bottom: 5px;
    }
    .chunk-text { color: var(--text-secondary) !important; line-height: 1.5; }

    /* ── Grounding bar ── */
    .ground-bar-wrap {
        background: var(--bg-overlay);
        border-radius: var(--radius-sm);
        overflow: hidden;
        height: 6px;
        margin: 8px 0 4px;
    }
    .ground-bar-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.6s cubic-bezier(0.16,1,0.3,1);
    }
    .ground-bar-good  { background: linear-gradient(90deg, #10b981, #34d399); }
    .ground-bar-mid   { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
    .ground-bar-low   { background: linear-gradient(90deg, #ef4444, #f87171); }

    /* ── Empty State ── */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80px 20px;
        text-align: center;
    }
    .empty-icon {
        width: 72px; height: 72px;
        background: linear-gradient(135deg, rgba(14,165,233,0.12), rgba(34,211,238,0.05));
        border: 1px solid rgba(14,165,233,0.22);
        border-radius: 24px;
        display: flex; align-items: center; justify-content: center;
        font-size: 2rem;
        margin-bottom: 24px;
        box-shadow: 0 0 50px rgba(14,165,233,0.12);
    }
    .empty-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-primary) !important;
        margin-bottom: 8px;
        letter-spacing: -0.3px;
    }
    .empty-sub { font-size: 0.85rem; color: var(--text-muted) !important; max-width: 440px; line-height: 1.6; }
    .empty-suggestions {
        display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;
        margin-top: 24px;
    }
    .suggestion-pill {
        background: var(--bg-raised);
        border: 1px solid var(--border-subtle);
        border-radius: 999px;
        padding: 7px 16px;
        font-size: 0.80rem;
        color: var(--text-secondary) !important;
        cursor: pointer;
        transition: border-color 0.2s, background 0.2s, color 0.2s;
    }
    .suggestion-pill:hover {
        border-color: rgba(14,165,233,0.4);
        background: rgba(14,165,233,0.07);
        color: #7dd3fc !important;
    }

    /* ── Buttons (Streamlit) ── */
    .stButton > button {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-sm) !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        padding: 6px 14px !important;
        transition: all 0.2s ease !important;
        font-family: var(--font-sans) !important;
    }
    .stButton > button:hover {
        border-color: rgba(14,165,233,0.45) !important;
        color: #7dd3fc !important;
        background: rgba(14,165,233,0.07) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    /* Primary action button */
    .stButton.primary-btn > button {
        background: linear-gradient(135deg, #0369a1, #0ea5e9) !important;
        color: #fff !important;
        border-color: transparent !important;
        box-shadow: 0 4px 14px rgba(14,165,233,0.3) !important;
    }
    .stButton.primary-btn > button:hover {
        box-shadow: 0 6px 22px rgba(14,165,233,0.45) !important;
        color: #fff !important;
    }

    /* ── Chat input ── */
    [data-testid="stChatInput"] {
        background: var(--bg-raised) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: 0 0 0 0 transparent;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(14,165,233,0.5) !important;
        box-shadow: 0 0 0 3px rgba(14,165,233,0.08) !important;
    }
    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: var(--text-primary) !important;
        font-family: var(--font-sans) !important;
        font-size: 0.93rem !important;
    }
    [data-testid="stChatInput"] textarea::placeholder { color: var(--text-muted) !important; }

    /* ── Metrics widget ── */
    [data-testid="metric-container"] {
        background: var(--bg-overlay) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-sm) !important;
        padding: 10px !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] { color: var(--text-muted) !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { color: var(--text-primary) !important; }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: var(--bg-overlay) !important;
        border: 1px dashed rgba(139,92,246,0.25) !important;
        border-radius: var(--radius-md) !important;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover { border-color: rgba(139,92,246,0.5) !important; }

    /* ── Slider ── */
    [data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stTickBar"] span { color: var(--text-muted) !important; }
    [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
        background: var(--accent-1) !important;
        border-color: var(--accent-1) !important;
    }

    /* ── Toggle ── */
    [data-testid="stToggle"] { accent-color: var(--accent-1) !important; }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: var(--accent-1) !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-subtle); border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(139,92,246,0.3); }

    /* ── Divider ── */
    hr { border-color: var(--border-subtle) !important; margin: 20px 0 !important; }

    /* ── Caption ── */
    [data-testid="stCaptionContainer"] { color: var(--text-muted) !important; }

    /* ── Progress bar ── */
    [data-testid="stProgressBar"] > div {
        background: linear-gradient(90deg, #0369a1, #0ea5e9, #22d3ee) !important;
        border-radius: 999px !important;
    }
    [data-testid="stProgressBar"] { background: var(--bg-overlay) !important; border-radius: 999px !important; }

    /* ── Toast ── */
    [data-testid="toastContainer"] [data-testid="toast"] {
        background: var(--bg-raised) !important;
        border: 1px solid rgba(14,165,233,0.3) !important;
        color: var(--text-primary) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
    }

    /* ── Quick Stats Row ── */
    .quick-stats-row {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 14px;
        justify-content: flex-start;
    }
    .quick-stat-pill {
        background: rgba(14,165,233,0.06);
        border: 1px solid rgba(14,165,233,0.15);
        border-radius: 999px;
        padding: 5px 14px;
        font-size: 0.76rem;
        color: var(--text-secondary) !important;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .quick-stat-pill strong {
        color: var(--accent-2) !important;
    }

    /* ── Central Workspace Landing Page ── */
    div[data-testid="stVerticalBlock"]:has(.central-card-marker) {
        max-width: 860px;
        margin: 40px auto;
        background: var(--bg-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 40px 48px;
        box-shadow: var(--shadow-card), var(--shadow-ambient);
    }
    .central-column-title {
        margin-bottom: 12px;
    }
    /* Style columns to have a subtle border separation */
    div[data-testid="stVerticalBlock"]:has(.central-card-marker) [data-testid="column"]:first-child {
        border-right: 1px solid var(--border-subtle);
        padding-right: 40px !important;
    }
    div[data-testid="stVerticalBlock"]:has(.central-card-marker) [data-testid="column"]:last-child {
        padding-left: 40px !important;
    }
</style>
""", unsafe_allow_html=True)
# ─── Chat Input Mascot Image ──────────────────────────────────────────────────
import base64
import os

img_base64 = ""
try:
    img_path = os.path.join(os.path.dirname(__file__), ".streamlit", "image.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
except Exception:
    pass

if img_base64:
    st.markdown(f"""
    <style>
        [data-testid="stChatInput"] {{
            margin-left: 52px !important;
            overflow: visible !important;
        }}
        [data-testid="stChatInput"]::before {{
            content: "";
            display: block;
            width: 38px;
            height: 38px;
            background-image: url("data:image/png;base64,{img_base64}");
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            position: absolute;
            left: -48px;
            top: 50%;
            transform: translateY(-50%);
            z-index: 10;
            pointer-events: none;
        }}
    </style>
    """, unsafe_allow_html=True)


# ─── Session State Init ──────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debug_traces" not in st.session_state:
    st.session_state.debug_traces = []


# ─── Helper Functions ────────────────────────────────────────────────────────
def check_api_health() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def query_rag(question: str, top_k: int = 5, max_retries: int = 2) -> dict:
    payload = {
        "question": question,
        "session_id": st.session_state.session_id,
        "top_k": top_k,
        "max_retries": max_retries,
    }
    try:
        r = requests.post(f"{API_BASE}/query", json=payload, timeout=120)
        return r.json() if r.status_code == 200 else {"error": f"API {r.status_code}: {r.text}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to FastAPI backend. Is the server running on port 8000?"}
    except Exception as e:
        return {"error": str(e)}

def upload_document(file) -> dict:
    try:
        files = {"file": (file.name, file.getvalue(), file.type or "application/octet-stream")}
        r = requests.post(f"{API_BASE}/ingest", files=files, timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_documents() -> dict:
    try:
        r = requests.get(f"{API_BASE}/documents", timeout=10)
        return r.json() if r.status_code == 200 else {"documents": []}
    except Exception:
        return {"documents": []}

def get_metrics() -> dict:
    try:
        r = requests.get(f"{API_BASE}/metrics", timeout=10)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

def submit_feedback(query_text: str, answer_text: str, rating: str):
    payload = {
        "query": query_text,
        "answer": answer_text,
        "rating": rating,
        "session_id": st.session_state.session_id,
    }
    try:
        requests.post(f"{API_BASE}/feedback", json=payload, timeout=10)
    except Exception:
        pass

def render_grounding_bar(score: float):
    pct = int(score * 100)
    cls = "good" if score >= 0.75 else ("mid" if score >= 0.5 else "low")
    label = "Fully Grounded ✓" if score >= 0.75 else ("Partially Grounded ◈" if score >= 0.5 else "Low Grounding ⚠")
    return f"""
    <div style="font-size:0.72rem;color:var(--text-muted);font-weight:600;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">
        Grounding — {pct}% &nbsp;·&nbsp; {label}
    </div>
    <div class="ground-bar-wrap">
        <div class="ground-bar-fill ground-bar-{cls}" style="width:{pct}%"></div>
    </div>
    """


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    api_up = check_api_health()
    st.markdown(f"""
    <div class="brand-header">
        <span class="brand-logo">📄 RAG Assistant</span>
        <div class="brand-tag">Documentation Intelligence</div>
    </div>
    <div class="{'status-pill status-online' if api_up else 'status-pill status-offline'}">
        <span class="status-dot"></span>
        {'API Connected' if api_up else 'API Offline'}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Document Center ──────────────────────────────────────────────────────
    with st.expander("⊞  Documents", expanded=False):
        docs_data = get_documents()
        docs_list = docs_data.get("documents", [])
        if docs_list:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            docs_html = ""
            for doc in docs_list:
                fname = doc.get("filename", "unknown")
                chunks = doc.get("chunk_count", 0)
                docs_html += (
                    f"<div style='font-size:0.78rem;padding:6px 0;border-bottom:1px solid var(--border-subtle);color:var(--text-secondary);display:flex;justify-content:space-between;align-items:center'>"
                    f"<span style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:145px;' title='{fname}'>📄 {fname}</span>"
                    f"<span style='color:var(--text-muted);font-family:var(--font-mono);font-size:0.72rem;background:rgba(255,255,255,0.03);padding:2px 6px;border-radius:4px;'>{chunks}ch</span>"
                    f"</div>"
                )
            st.markdown(
                f"<div style='max-height: 180px; overflow-y: auto; padding-right: 4px; scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.1) transparent;'>"
                f"{docs_html}"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.caption("No documents indexed yet.")

    # ── Metrics ─────────────────────────────────────────────────────────────
    with st.expander("◈  Metrics", expanded=False):
        metrics = get_metrics()
        if metrics:
            st.markdown(
                f"<div style='display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; margin-bottom: 8px;'>"
                f"<div class='sidebar-stat-card'>"
                f"<div class='sidebar-stat-label'>Documents</div>"
                f"<div class='sidebar-stat-num'>{metrics.get('total_documents', 0)}</div>"
                f"</div>"
                f"<div class='sidebar-stat-card'>"
                f"<div class='sidebar-stat-label'>Chunks</div>"
                f"<div class='sidebar-stat-num'>{metrics.get('total_chunks', 0)}</div>"
                f"</div>"
                f"<div class='sidebar-stat-card'>"
                f"<div class='sidebar-stat-label'>Likes</div>"
                f"<div class='sidebar-stat-num' style='color:var(--accent-green) !important;'>👍 {metrics.get('feedback_positive', 0)}</div>"
                f"</div>"
                f"<div class='sidebar-stat-card'>"
                f"<div class='sidebar-stat-label'>Dislikes</div>"
                f"<div class='sidebar-stat-num' style='color:var(--accent-red) !important;'>👎 {metrics.get('feedback_negative', 0)}</div>"
                f"</div>"
                f"</div>"
                f"<div style='font-size:0.7rem; color:var(--text-muted); text-align:center; padding-top:4px;'>"
                f"Latency Avg: <strong style='color:var(--text-secondary);'>{metrics.get('average_response_time_ms', 0)}ms</strong>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.caption("Metrics unavailable.")

    # ── Controls ─────────────────────────────────────────────────────────────
    with st.expander("◎  Controls", expanded=False):
        top_k = st.slider("Top-K Chunks", 1, 20, 5, key="top_k_slider")
        max_retries = st.slider("Max Retries", 0, 5, 2, key="retry_slider")
        show_debug = st.toggle("Show Debug Trace", value=True, key="debug_toggle")

    # ── Action Buttons ───────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Conversation", use_container_width=True, key="clear_btn"):
        st.session_state.messages = []
        st.session_state.debug_traces = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    # Footer
    st.markdown(
        "<div style='padding:16px 20px;font-size:0.65rem;color:var(--text-muted);border-top:1px solid var(--border-subtle);margin-top:auto;letter-spacing:0.5px'>"
        "Self-Corrective RAG · LangGraph</div>",
        unsafe_allow_html=True,
    )


# ─── Main Area ───────────────────────────────────────────────────────────────
# Retrieve metrics for quick stats
metrics = get_metrics()
total_docs = metrics.get("total_documents", 0)
total_chunks = metrics.get("total_chunks", 0)

# Page header
st.markdown(f"""
<div class="page-header">
    <div class="page-title">RAG Documentation Assistant</div>
    <div class="page-subtitle">Ask questions about your indexed technical docs — retrieval-graded, citation-grounded answers.</div>
    <div class="quick-stats-row">
        <span class="quick-stat-pill">📄 Indexed Documents: <strong>{total_docs}</strong></span>
        <span class="quick-stat-pill">🧩 Chunks: <strong>{total_chunks}</strong></span>
        <span class="quick-stat-pill">⚙️ LLM: <strong>Gemini → Groq Failover</strong></span>
        <span class="quick-stat-pill">🌐 Web Search: <strong>Enabled</strong></span>
    </div>
</div>
""", unsafe_allow_html=True)

# Read controls from session (set in sidebar)
top_k = st.session_state.get("top_k_slider", 5)
max_retries = st.session_state.get("retry_slider", 2)
show_debug = st.session_state.get("debug_toggle", True)

# ─── Avatar SVGs ──────────────────────────────────────────────────────────────
USER_AVATAR_SVG = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:14px; height:14px; color:#fff;">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
</svg>"""

BOT_AVATAR_SVG = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:15px; height:15px; color:#38bdf8;">
    <path d="M6 20h12" />
    <path d="M12 20v-3" />
    <path d="M19 13.5C19 10 16 9 12 9s-7 1-7 4.5c0 1.5 1.5 2.5 3.5 3h7c2-.5 3.5-1.5 3.5-3z" />
    <path d="M5 11c-2 0-3-1-3-2.5S3.5 6 5 6c1 0 2 .5 2.5 1.5" />
    <path d="M19 13.5c1.5-1 2.5-3 2-4.5" />
    <path d="M19 4.5l1.5 1.5-1.5 1.5-1.5-1.5z" />
    <path d="M14 2l1 1-1 1-1-1z" />
</svg>"""

# ─── Render Chat History ─────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="msg-row-user">
            <div class="user-bubble">{msg["content"]}</div>
            <div class="user-avatar">
                {USER_AVATAR_SVG}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        content = msg["content"]
        # Build sources HTML
        trace = st.session_state.debug_traces[i] if i < len(st.session_state.debug_traces) else None
        sources_html = ""
        if trace and trace.get("sources"):
            chips = "".join(
                f'<span class="source-chip">📄 {s["source_file"]} #{s["chunk_index"]}</span>'
                for s in trace["sources"]
            )
            sources_html = f'<div class="source-row">{chips}</div>'

        st.markdown(f"""
        <div class="msg-row-bot">
            <div class="bot-avatar">
                {BOT_AVATAR_SVG}
            </div>
            <div class="bot-bubble">
                {content}
                {sources_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Feedback row
        if trace:
            fb_col1, fb_col2, fb_col3 = st.columns([0.5, 0.5, 10])
            with fb_col1:
                if st.button("👍", key=f"hist_pos_{i}", help="Helpful"):
                    submit_feedback(
                        st.session_state.messages[i - 1]["content"] if i > 0 else "",
                        content, "positive"
                    )
                    st.toast("Thanks for the feedback!", icon="✅")
            with fb_col2:
                if st.button("👎", key=f"hist_neg_{i}", help="Not helpful"):
                    submit_feedback(
                        st.session_state.messages[i - 1]["content"] if i > 0 else "",
                        content, "negative"
                    )
                    st.toast("Feedback noted.", icon="📝")

        # Debug trace (history)
        if show_debug and trace and i > 0:
            with st.expander("◈ Retrieval trace", expanded=False):
                _q = st.session_state.messages[i - 1]["content"] if i > 0 else "—"
                _rw = trace.get("rewritten_query", _q)
                _qt = trace.get("query_type", "—")
                _rt = trace.get("response_time_ms", "—")
                _rc = trace.get("retry_count", 0)
                _fb = trace.get("is_fallback", False)
                _hs = trace.get("hallucination_score")
                st.markdown(f"""
                <div class="stat-row">
                    <div class="stat-chip"><span class="stat-chip-label">Query Type</span><span class="stat-chip-value">{_qt}</span></div>
                    <div class="stat-chip"><span class="stat-chip-label">Latency</span><span class="stat-chip-value">{_rt} ms</span></div>
                    <div class="stat-chip"><span class="stat-chip-label">Retries</span><span class="stat-chip-value">{_rc}</span></div>
                    <div class="stat-chip"><span class="stat-chip-label">Fallback</span><span class="stat-chip-value">{'Yes' if _fb else 'No'}</span></div>
                </div>
                """, unsafe_allow_html=True)
                if _hs is not None:
                    st.markdown(render_grounding_bar(_hs), unsafe_allow_html=True)


# ─── Chat Input ──────────────────────────────────────────────────────────────
question = st.chat_input("🧞 Ask the RAG Genie anything…", disabled=not api_up)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.debug_traces.append(None)

    # Show user bubble immediately
    st.markdown(f"""
    <div class="msg-row-user">
        <div class="user-bubble">{question}</div>
        <div class="user-avatar">
            {USER_AVATAR_SVG}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Query backend
    with st.spinner(""):
        result = query_rag(question, top_k=top_k, max_retries=max_retries)

    if "error" in result:
        answer = f"⚠ {result['error']}"
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.debug_traces.append(None)
        st.markdown(f"""
        <div class="msg-row-bot">
            <div class="bot-avatar">
                {BOT_AVATAR_SVG}
            </div>
            <div class="bot-bubble" style="border-color:rgba(239,68,68,0.25)">{answer}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        answer = result.get("answer", "No response generated.")
        sources = result.get("sources", [])

        sources_html = ""
        if sources:
            chips = "".join(
                f'<span class="source-chip">📄 {s["source_file"]} #{s["chunk_index"]}</span>'
                for s in sources
            )
            sources_html = f'<div class="source-row">{chips}</div>'

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.debug_traces.append(result)

        st.markdown(f"""
        <div class="msg-row-bot">
            <div class="bot-avatar">
                {BOT_AVATAR_SVG}
            </div>
            <div class="bot-bubble">
                {answer}
                {sources_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Feedback
        fb1, fb2, fb3 = st.columns([0.5, 0.5, 10])
        with fb1:
            if st.button("👍", key=f"pos_{len(st.session_state.messages)}", help="Helpful"):
                submit_feedback(question, answer, "positive")
                st.toast("Thanks!", icon="✅")
        with fb2:
            if st.button("👎", key=f"neg_{len(st.session_state.messages)}", help="Not helpful"):
                submit_feedback(question, answer, "negative")
                st.toast("Noted.", icon="📝")

        # Debug trace for new message
        if show_debug:
            is_fallback = result.get("is_fallback", False)
            retry_count = result.get("retry_count", 0)
            response_time = result.get("response_time_ms", 0)
            halluc_score = result.get("hallucination_score")
            query_type = result.get("query_type", "unknown")
            rewritten = result.get("rewritten_query", question)

            with st.expander("◈ Retrieval trace", expanded=False):
                st.markdown(f"""
                <div class="stat-row">
                    <div class="stat-chip"><span class="stat-chip-label">Query Type</span><span class="stat-chip-value">{query_type}</span></div>
                    <div class="stat-chip"><span class="stat-chip-label">Latency</span><span class="stat-chip-value">{response_time} ms</span></div>
                    <div class="stat-chip"><span class="stat-chip-label">Retries</span><span class="stat-chip-value">{retry_count}</span></div>
                    <div class="stat-chip"><span class="stat-chip-label">Fallback</span><span class="stat-chip-value">{'Yes' if is_fallback else 'No'}</span></div>
                </div>
                """, unsafe_allow_html=True)

                if halluc_score is not None:
                    st.markdown(render_grounding_bar(halluc_score), unsafe_allow_html=True)

                if rewritten != question:
                    st.markdown(
                        f"<div style='font-size:0.78rem;margin-top:10px;color:var(--text-muted)'>"
                        f"<strong style='color:var(--text-secondary)'>Rewritten:</strong> {rewritten}</div>",
                        unsafe_allow_html=True,
                    )

                retrieved = result.get("retrieved_chunks", [])
                graded = result.get("graded_chunks", [])

                if retrieved:
                    st.markdown(
                        f"<div style='font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text-muted);margin:12px 0 6px'>Retrieved — {len(retrieved)} chunks</div>",
                        unsafe_allow_html=True,
                    )
                    for idx, chunk in enumerate(retrieved):
                        dist = chunk.get('distance')
                        dist_str = f" · distance: {dist:.3f}" if dist is not None else ""
                        st.markdown(f"""
                        <div class="chunk-card">
                            <div class="chunk-meta">{chunk.get('source_file','?')} · chunk #{chunk.get('chunk_index', idx)}{dist_str}</div>
                            <div class="chunk-text">{chunk.get('content','')[:200]}…</div>
                        </div>
                        """, unsafe_allow_html=True)

                if graded:
                    rel = sum(1 for c in graded if c.get("grade") == "relevant")
                    st.markdown(
                        f"<div style='font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text-muted);margin:12px 0 6px'>Graded — {rel}/{len(graded)} relevant</div>",
                        unsafe_allow_html=True,
                    )
                    for chunk in graded:
                        grade = chunk.get("grade", "unknown")
                        icon = "✓" if grade == "relevant" else "✗"
                        css_extra = "relevant" if grade == "relevant" else "irrelevant"
                        dist = chunk.get('distance')
                        dist_str = f" · distance: {dist:.3f}" if dist is not None else ""
                        st.markdown(f"""
                        <div class="chunk-card {css_extra}">
                            <div class="chunk-meta">{icon} {grade.upper()} · {chunk.get('source_file','?')} · chunk #{chunk.get('chunk_index','?')}{dist_str}</div>
                            <div class="chunk-text">{chunk.get('content','')[:150]}…</div>
                        </div>
                        """, unsafe_allow_html=True)

    st.rerun()


if not st.session_state.messages:
    with st.container():
        st.markdown('<div class="central-card-marker"></div>', unsafe_allow_html=True)

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <div style="width: 38px; height: 38px; background: linear-gradient(135deg, #0f172a, #1e293b); border: 1.5px solid rgba(148,163,184,0.3); border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(0,0,0,0.2); flex-shrink: 0;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="width:15px; height:15px; color:#94a3b8;">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="12" y1="18" x2="12" y2="12" />
                        <polyline points="9 15 12 12 15 15" />
                    </svg>
                </div>
                <div>
                    <span style="font-size: 1.3rem; font-weight: 700; color: var(--text-primary) !important; display: block; line-height: 1.2;">Add a Document</span>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 20px; line-height: 1.5;">
                Drag and drop your PDF, Markdown, HTML, or text files here to add them to your assistant's library.
            </div>
            """, unsafe_allow_html=True)
            
            # Central file uploader
            central_uploaded = st.file_uploader(
                "Upload a document",
                type=["md", "txt", "pdf", "html"],
                help="Supported formats: PDF · Markdown · Text · HTML",
                label_visibility="collapsed",
                key="central_uploader"
            )
            
            if central_uploaded:
                if st.button("Add to Assistant's Knowledge", use_container_width=True, key="central_ingest_btn", type="primary"):
                    with st.spinner("Processing document..."):
                        result = upload_document(central_uploaded)
                    if "error" in result:
                        st.error("Something went wrong: " + result["error"])
                    elif result.get("duplicate"):
                        st.warning("This document is already in your library!")
                    else:
                        st.success(f"Successfully added! Indexed {result.get('chunk_count', 0)} parts.")
                        time.sleep(1)
                        st.rerun()

        with col_right:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <div style="width: 38px; height: 38px; background: linear-gradient(135deg, #082f49, #0c4a6e); border: 1.5px solid rgba(14,165,233,0.45); border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(14,165,233,0.3); flex-shrink: 0;">
                    {BOT_AVATAR_SVG}
                </div>
                <div>
                    <span style="font-size: 1.3rem; font-weight: 700; color: var(--text-primary) !important; display: block; line-height: 1.2;">Ask the RAG Genie</span>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 20px; line-height: 1.5;">
                Have a question? Type it in the bar at the bottom of the page, or try one of these popular questions:
            </div>
            """, unsafe_allow_html=True)

            if st.button("💡 What is FastAPI?", use_container_width=True, key="sugg_fastapi"):
                st.session_state.messages.append({"role": "user", "content": "What is FastAPI?"})
                st.session_state.debug_traces.append(None)
                st.rerun()
                
            if st.button("💡 Summarize this resume", use_container_width=True, key="sugg_resume"):
                st.session_state.messages.append({"role": "user", "content": "Summarize this resume"})
                st.session_state.debug_traces.append(None)
                st.rerun()
                
            if st.button("💡 Compare Pydantic and Dataclasses", use_container_width=True, key="sugg_compare"):
                st.session_state.messages.append({"role": "user", "content": "Compare Pydantic and Dataclasses"})
                st.session_state.debug_traces.append(None)
                st.rerun()

            st.markdown("""
            <div style="margin-top: 24px; padding: 12px 16px; background: rgba(100,200,255,0.06); border-radius: 10px; border: 1px solid rgba(100,200,255,0.12);">
                <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.6;">
                    🧞 <strong style="color: var(--text-primary);">Ask the Genie:</strong> Type your question in the input bar at the bottom of the screen to start chatting!
                </div>
            </div>
            """, unsafe_allow_html=True)
