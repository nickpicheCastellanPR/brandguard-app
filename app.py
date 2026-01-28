import streamlit as st
from PIL import Image
import os
from logic import SignetLogic

# --- PAGE CONFIG ---
icon_path = "Signet_Icon_Color.png"
if os.path.exists(icon_path):
    page_icon = Image.open(icon_path)
else:
    page_icon = None 

st.set_page_config(
    page_title="Signet", 
    page_icon=page_icon, 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Logic
logic = SignetLogic()

# --- THE CASTELLAN IDENTITY SYSTEM (CSS) ---
st.markdown("""
<style>
    /* 1. PALETTE DEFINITION */
    :root {
        --c-teal-deep: #24363b;   /* Main Background */
        --c-teal-dark: #1b2a2e;   /* Input Backgrounds */
        --c-gold-muted: #ab8f59;  /* Accents & Borders */
        --c-cream: #f5f5f0;       /* Sidebar & Text */
        --c-sage: #5c6b61;        /* Success/Secondary */
        --c-charcoal: #3d3d3d;    /* Sidebar Text */
    }

    /* 2. LAYOUT & BACKGROUNDS */
    .stApp {
        background-color: var(--c-teal-deep);
        color: var(--c-cream);
    }
    
    /* THE SIDEBAR - CREAM */
    section[data-testid="stSidebar"] {
        background-color: var(--c-cream) !important;
        border-right: 1px solid var(--c-gold-muted);
    }
    
    /* Sidebar Text Overrides (Dark on Cream) */
    section[data-testid="stSidebar"] * {
        color: var(--c-teal-deep) !important;
    }
    
    /* 3. NAVIGATION MENU (Clean List) */
    div[role="radiogroup"] label > div:first-child { display: none !important; }
    div[role="radiogroup"] label {
        padding: 12px 20px !important;
        border-radius: 0px !important;
        border-left: 3px solid transparent !important;
        margin-bottom: 4px !important;
        transition: all 0.2s ease;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-family: 'Helvetica Neue', sans-serif !important;
    }
    div[role="radiogroup"] label:hover {
        background-color: rgba(36, 54, 59, 0.05) !important;
        border-left: 3px solid var(--c-gold-muted) !important;
        padding-left: 25px !important;
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: var(--c-teal-deep) !important;
        color: var(--c-cream) !important;
        border-left: 3px solid var(--c-gold-muted) !important;
    }
    div[role="radiogroup"] label[data-checked="true"] * { color: var(--c-cream) !important; }

    /* 4. HEADERS */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800 !important;
        text-transform: uppercase;
        color: var(--c-cream) !important;
        padding-bottom: 15px;
        border-bottom: 1px solid var(--c-gold-muted);
        letter-spacing: 0.05em;
    }
    
    h2, h3 { color: var(--c-gold-muted) !important; text-transform: uppercase; font-weight: 700; }

    /* 5. INPUTS (FIXED VISIBILITY) */
    .stTextInput input, 
    .stTextArea textarea, 
    .stSelectbox div[data-baseweb="select"] > div,
    .stSelectbox div[data-baseweb="select"] span {
        background-color: var(--c-teal-dark) !important;
        border: 1px solid var(--c-sage) !important;
        color: #FFFFFF !important;       /* FORCE WHITE TEXT */
        caret-color: #FFFFFF !important; /* FORCE WHITE CURSOR */
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 0px !important;
    }
    
    /* Placeholder Text Color */
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #A0A0A0 !important;
        -webkit-text-fill-color: #A0A0A0 !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--c-gold-muted) !important;
        box-shadow: 0 0 8px rgba(171, 143, 89, 0.2) !important;
    }
    
    /* Fix Dropdown Menu Items */
    ul[data-baseweb="menu"] li {
        color: #FFFFFF !important;
        background-color: var(--c-teal-dark) !important;
    }

    /* 6. BUTTONS */
    .stButton button {
        background-color: transparent !important;
        border: 1px solid var(--c-gold-muted) !important;
        color: var(--c-gold-muted) !important;
        border-radius: 0px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        transition: all 0.2s;
        padding: 0.6rem 1.2rem;
    }
    .stButton button:hover {
        background-color: var(--c-gold-muted) !important;
        color: var(--c-teal-deep) !important;
        box-shadow: 0 0 15px rgba(171, 143, 89, 0.4);
        transform: translateY(-1px);
    }
    button[kind="primary"] {
        background: var(--c-gold-muted) !important;
        color: var(--c-teal-deep) !important;
        border: none !important;
    }

    /* 7. DASHBOARD CARDS */
    .dashboard-card {
        background-color: rgba(27, 42, 46, 0.6);
        border: 1px solid var(--c-sage);
        border-left: 4px solid var(--c-gold-muted);
        padding: 25px;
        margin-bottom: 20px;
    }
    
    /* 8. OVERRIDE ALERTS */
    div.stAlert {
        background-color: rgba(171, 143, 89, 0.1);
        border: 1px solid var(--c-gold-muted);
        color: var(--c-gold-muted);
        border-radius: 0px;
    }
    div.stAlert > div { color: var(--c-cream) !important; }
    
    /* 9. HERO CARDS (Icons via CSS) */
    .hero-card {
        background: linear-gradient(135deg, var(--c-teal-dark) 0%, #111 100%);
        border: 1px solid #3a4b50;
        padding: 30px;
        text-align: center;
        margin: 10px;
        transition: transform 0.2s;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
    }
    .hero-card:hover { 
        transform: translateY(-5px); 
        border-color: var(--c-gold-muted); 
        box-shadow: 0 10px 30px rgba(0,0,0,0.4); 
    }
    
    /* CSS Icons */
    .icon-build { width: 40px; height: 40px; border: 2px solid var(--c-gold-muted); position: relative; margin-bottom: 20px; }
    .icon-build::after { content: ''; position: absolute; top: -10px; left: 10px; width: 100%; height: 100%; border: 2px solid var(--c-sage); }
    
    .icon-doc { width: 30px; height: 40px; border: 2px solid var(--c-gold-muted); margin-bottom: 20px; position: relative; }
    .icon-doc::before { content: ''; position: absolute; top: 5px; left: 5px; width: 15px; height: 2px; background: var(--c-sage); box-shadow: 0 5px 0 var(--c-sage), 0 10px 0 var(--c-sage); }

    .icon-gear { width: 40px; height: 40px; border: 2px solid var(--c-gold-muted); border-radius: 50%; margin-bottom: 20px; display: flex; justify-content: center; align-items: center; }
    .icon-gear::after { content: ''; width: 10px; height: 10px; background: var(--c-sage); }

    .hero-title { font-weight: 800; color: var(--c-cream); font-size: 1rem; text-transform: uppercase; letter-spacing: 0.1em;}
    .hero-desc { color: #a0a0a0; font-size: 0.8rem; margin-top: 10px; font-family: monospace; }

    /* 10. STATUS INDICATORS */
    .status-dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .dot-green { background-color: #4cd964; box-shadow: 0 0 10px #4cd964; }
    .dot-red { background-color: #ff5f56; opacity: 0.5; }
    .dot-yellow { background-color: var(--c-gold-muted); box-shadow: 0 0 5px var(--c-gold-muted); }

    .status-row {
        background: rgba(255,255,255,0.03);
        padding: 15px;
        margin-bottom: 10px;
        border-left: 2px solid transparent;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* 11. FOOTER */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: var(--c-teal-deep);
        color: var(--c-sage);
        text-align: center;
        padding: 10px;
        font-size: 0.7rem;
        letter-spacing: 0.2em;
        border-top: 1px solid #30363d;
        z-index: 100;
    }
    
    /* CLEANUP */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'authenticated' not in st.session_
