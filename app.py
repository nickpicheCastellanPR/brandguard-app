import streamlit as st
from PIL import Image
import os
import re
import json
from logic import SignetLogic
import database as db

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

# Initialize Logic & Database
logic = SignetLogic()
if 'db_init' not in st.session_state:
    db.init_db()
    st.session_state['db_init'] = True

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

    /* 6. BUTTONS (GLOBAL) */
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
    
    /* Red delete button override */
    button[kind="secondary"] {
        border-color: #ff5f56 !important;
        color: #ff5f56 !important;
    }

    /* 7. DASHBOARD CARDS (Static) */
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

# --- SESSION STATE & AUTH ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'user_id' not in st.session_state: st.session_state['user_id'] = None
if 'username' not in st.session_state: st.session_state['username'] = None

# WIZARD STATE DEFAULTS
def init_wizard_state():
    if 'wiz_samples_list' not in st.session_state: st.session_state['wiz_samples_list'] = []
    if 'wiz_social_list' not in st.session_state: st.session_state['wiz_social_list'] = [] 
    if 'wiz_logo_list' not in st.session_state: st.session_state['wiz_logo_list'] = []      
    if 'dashboard_upload_open' not in st.session_state: st.session_state['dashboard_upload_open'] = False 
    if 'palette_primary' not in st.session_state: st.session_state['palette_primary'] = ["#24363b"]
    if 'palette_secondary' not in st.session_state: st.session_state['palette_secondary'] = ["#f5f5f0", "#5c6b61"]
    if 'palette_accent' not in st.session_state: st.session_state['palette_accent'] = ["#ab8f59"]
    # Dynamic Keys
    if 'file_uploader_key' not in st.session_state: st.session_state['file_uploader_key'] = 0 
    if 'social_uploader_key' not in st.session_state: st.session_state['social_uploader_key'] = 1000
    if 'logo_uploader_key' not in st.session_state: st.session_state['logo_uploader_key'] = 2000

init_wizard_state()

if 'profiles' not in st.session_state: st.session_state['profiles'] = {}
if 'nav_selection' not in st.session_state: st.session_state['nav_selection'] = "DASHBOARD"

ARCHETYPES = [
    "The Ruler", "The Creator", "The Sage", "The Innocent", 
    "The Outlaw", "The Magician", "The Hero", "The Lover", 
    "The Jester", "The Everyman", "The Caregiver", "The Explorer"
]

# --- HELPER FUNCTIONS ---
def nav_to(page_name):
    st.session_state['nav_selection'] = page_name

def calculate_calibration_score(profile_data):
    # 1. Normalize Input
    if isinstance(profile_data, dict):
        text_data = profile_data.get('final_text', '')
    else:
        text_data = str(profile_data)
    
    score = 0
    
    # 2. Foundation Check (50 pts)
    # Using specific headers your Wizard/Parser generates
    core_sections = ["STRATEGY", "VOICE", "VISUALS", "LOGO RULES", "TYPOGRAPHY"]
    foundations_found = 0
    missing_core = []
    
    for section in core_sections:
        if section in text_data:
            foundations_found += 1
        else:
            missing_core.append(section.title()) # e.g. "Logo Rules"
            
    score += (foundations_found * 10)

    # 3. Confidence Check (Word Count Volume) (50 pts)
    # Regex to grab text between headers to count words
    style_match = re.search(r'Style Signature(.*?)(SOCIAL MEDIA|$)', text_data, re.DOTALL)
    social_match = re.search(r'SOCIAL MEDIA(.*?)$', text_data, re.DOTALL)
    
    style_count = len(style_match.group(1).split()) if style_match else 0
    social_count = len(social_match.group(1).split()) if social_match else 0
    
    # Simple volume scaling
    if style_count > 150: score += 25
    elif style_count > 50: score += 10
    
    if social_count > 100: score += 25
    elif social_count > 30: score += 10

    # 4. Determine Status, Color & Specific Advice
    if score < 50:
        # TIER 1: FOUNDATION (Charcoal)
        status_label = "Foundation"
        # Use your exact charcoal hex
        color = "#3d3d3d" 
        # Advice: Tell them exactly which core section is missing
        if missing_core:
            next_step = f"Missing core data: {missing_core[0]}"
        else:
            next_step = "Add Strategy details to unlock the next tier."
        msg = f"⚠️ <b>Risk: High.</b> {next_step}"

    elif score < 80:
        # TIER 2: DEVELOPING (Gold)
        status_label = "Developing"
        # Use your exact gold hex
        color = "#ab8f59" 
        # Advice: Tell them to add volume
        if style_count < 150:
            msg = "💡 <b>Refinement:</b> Add more writing samples to capture your tone."
        elif social_count < 100:
            msg = "💡 <b>Refinement:</b> Add social media examples to improve post generation."
        else:
            msg = "💡 <b>Refinement:</b> Fill out all sections to maximize accuracy."

    else:
        # TIER 3: CALIBRATED (Sage)
        status_label = "Calibrated"
        # Use the "Vibrant Sage" we designed
        color = "#4E8065" 
        msg = "✅ <b>Ready:</b> Signet has sufficient data to generate on-brand content."

    return {
        "score": score,
        "status_label": status_label,
        "color": color,
        "message": msg
    }

def convert_to_html_brand_card(brand_name, content):
    content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'^#+\s*(.*)', r'<h3 style="color: #ab8f59; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 20px;">\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^\*\s*(.*)', r'<div style="margin-left: 20px; margin-bottom: 5px;">• \1</div>', content, flags=re.MULTILINE)
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f5f5f0; color: #24363b; padding: 40px; line-height: 1.6; }}
            .brand-card {{ max-width: 800px; margin: 0 auto; background: white; padding: 60px; border-top: 10px solid #24363b; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            h1 {{ font-size: 3em; color: #24363b; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 0.05em; }}
            .subtitle {{ font-size: 1.2em; color: #ab8f59; font-weight: bold; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 40px; }}
            strong {{ color: #1b2a2e; font-weight: 700; }}
            .footer {{ margin-top: 60px; font-size: 0.7rem; color: #aaa; text-align: center; border-top: 1px solid #eee; padding-top: 20px; letter-spacing: 0.1em; }}
            .content {{ white-space: pre-wrap; font-family: inherit; }}
        </style>
    </head>
    <body>
        <div class="brand-card">
            <h1>{brand_name}</h1>
            <div class="subtitle">Brand Governance Profile</div>
            <div class="content">{content}</div>
            <div class="footer">GENERATED BY SIGNET // INTELLIGENT BRAND GOVERNANCE</div>
        </div>
    </body>
    </html>
    """
    return html_template

# --- CALLBACKS ---
def add_voice_sample_callback():
    s_type = st.session_state.get('wiz_sample_type', 'Generic')
    s_text = st.session_state.get('wiz_temp_text', '')
    u_key = f"uploader_{st.session_state['file_uploader_key']}"
    s_file = st.session_state.get(u_key, None)
    content = ""
    source = ""
    if s_text.strip():
        content = s_text
        source = "Text Paste"
    elif s_file:
        source = f"File ({s_file.name})"
        try:
            if s_file.type == "application/pdf":
                content = logic.extract_text_from_pdf(s_file)
            elif "image" in s_file.type:
                content = f"[IMAGE CONTENT: {s_file.name}]" 
            else:
                content = s_file.getvalue().decode("utf-8", errors='ignore')
        except Exception as e:
            content = f"[Extraction Failed: {str(e)}]"
    if content:
        entry = f"TYPE: {s_type} | SOURCE: {source}\nCONTENT: {content}"
        st.session_state['wiz_samples_list'].append(entry)
        st.session_state['wiz_temp_text'] = ""
        st.session_state['file_uploader_key'] += 1

def add_social_callback():
    s_platform = st.session_state.get('wiz_social_platform', 'Other')
    u_key = f"social_up_{st.session_state['social_uploader_key']}"
    s_file = st.session_state.get(u_key, None)
    if s_file:
        st.session_state['wiz_social_list'].append({'platform': s_platform, 'file': s_file})
        st.session_state['social_uploader_key'] += 1

def add_logo_callback():
    u_key = f"logo_up_{st.session_state['logo_uploader_key']}"
    s_file = st.session_state.get(u_key, None)
    if s_file:
        st.session_state['wiz_logo_list'].append({'file': s_file})
        st.session_state['logo_uploader_key'] += 1

def add_palette_color(key):
    st.session_state[key].append("#ffffff")

def remove_palette_color(key, index):
    st.session_state[key].pop(index)

# --- LOGIN / AUTH SCREEN ---
if not st.session_state['authenticated']:
    st.markdown("""<style>.stApp { background-color: #f5f5f0 !important; background-image: linear-gradient(rgba(36, 54, 59, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(36, 54, 59, 0.05) 1px, transparent 1px), radial-gradient(circle at 0% 0%, rgba(92, 107, 97, 0.5) 0%, rgba(92, 107, 97, 0.1) 40%, transparent 70%), radial-gradient(circle at 100% 100%, rgba(36, 54, 59, 0.4) 0%, rgba(36, 54, 59, 0.1) 40%, transparent 70%); background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100%; } section[data-testid="stSidebar"] { display: none; } .stTextInput input { background-color: #ffffff !important; color: #24363b !important; border: 1px solid #c0c0c0 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05); -webkit-text-fill-color: #24363b !important; } .stTextInput input:focus { border-color: #24363b !important; }</style>""", unsafe_allow_html=True)

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", width=300)
        else:
            st.markdown("<div style='text-align: center; font-size: 3.5rem; color: #24363b; font-weight: 800; letter-spacing: 0.15em;'>SIGNET</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; color: #5c6b61; font-size: 0.8rem; letter-spacing: 0.3em; font-weight: 700; margin-top: 15px; margin-bottom: 30px;'>INTELLIGENT BRAND GOVERNANCE</div>", unsafe_allow_html=True)
        
        login_tab, reg_tab = st.tabs(["LOGIN", "REGISTER"])
        
        with login_tab:
            l_user = st.text_input("USERNAME", key="l_user")
            l_pass = st.text_input("PASSWORD", type="password", key="l_pass")
            if st.button("ENTER", type="primary"):
                uid = db.verify_user(l_user, l_pass)
                if uid:
                    st.session_state['authenticated'] = True
                    st.session_state['user_id'] = uid
                    st.session_state['username'] = l_user
                    # LOAD PROFILES FROM DB
                    st.session_state['profiles'] = db.get_profiles(uid)
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
        
        with reg_tab:
            r_user = st.text_input("CHOOSE USERNAME", key="r_user")
            r_pass = st.text_input("CHOOSE PASSWORD", type="password", key="r_pass")
            if st.button("CREATE ACCOUNT"):
                if db.create_user(r_user, r_pass):
                    st.success("Account created! Please log in.")
                else:
                    st.error("Username already taken.")

        st.markdown("<br><div style='text-align: center; color: #ab8f59; font-size: 0.7rem; letter-spacing: 0.2em;'>CASTELLAN PR INTERNAL TOOL</div>", unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("Signet_Logo_Color.png"):
        st.image("Signet_Logo_Color.png", use_container_width=True)
    else:
        st.markdown('<div style="font-size: 2rem; color: #24363b; font-weight: 900; letter-spacing: 0.1em; text-align: center; margin-bottom: 20px;">SIGNET</div>', unsafe_allow_html=True)
    
    st.caption(f"LOGGED IN AS: {st.session_state.get('username', 'User').upper()}")
    
    # Refresh Profiles from DB logic if needed, but session state usually holds it
    profile_names = list(st.session_state['profiles'].keys())
    
    if profile_names:
        active_profile = st.selectbox("ACTIVE PROFILE", profile_names)
        current_rules = st.session_state['profiles'][active_profile]
        
        # Calculate Metrics
        metrics = calculate_calibration_score(current_rules)
        
        # --- REPLACEMENT: CASTELLAN SIDEBAR METER ---
        st.markdown("<br>", unsafe_allow_html=True)
        
        # We use a slightly more compact CSS for the sidebar width
        st.markdown(f"""
            <style>
                .sb-container {{ margin-bottom: 10px; }}
                .sb-label {{ font-size: 0.7rem; font-weight: 700; color: #5c6b61; letter-spacing: 1px; margin-bottom: 4px; display: block; }}
                .sb-track {{ width: 100%; height: 6px; background: #dcdcd9; border-radius: 999px; overflow: hidden; margin-bottom: 6px; }}
                .sb-fill {{ height: 100%; width: {metrics['score']}%; background: {metrics['color']}; border-radius: 999px; transition: width 0.8s ease; }}
                .sb-status {{ font-size: 0.75rem; font-weight: 800; color: {metrics['color']}; }}
            </style>
            <div class="sb-container">
                <span class="sb-label">ENGINE CONFIDENCE</span>
                <div class="sb-track">
                    <div class="sb-fill"></div>
                </div>
                <div class="sb-status">
                     {metrics['status_label'].upper()} ({metrics['score']}%)
                </div>
            </div>
        """, unsafe_allow_html=True)
        # ---------------------------------------------
    else:
        active_profile = None
        cal_score = 0
        current_rules = ""
        st.markdown("<div style='text-align:center; color:#5c6b61; font-size:0.8rem; margin-bottom:20px; font-weight:700;'>NO PROFILE LOADED</div>", unsafe_allow_html=True)

    st.divider()
    app_mode = st.radio("MODULES", ["DASHBOARD", "VISUAL COMPLIANCE", "COPY EDITOR", "CONTENT GENERATOR", "SOCIAL MEDIA ASSISTANT", "BRAND ARCHITECT", "BRAND MANAGER"], label_visibility="collapsed", key="nav_selection")
    st.divider()
    if st.button("LOGOUT"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- MODULES ---

# 1. DASHBOARD
if app_mode == "DASHBOARD":
    if not active_profile:
        st.title("WELCOME TO SIGNET")
        st.markdown("""<p style='font-size: 1.1rem; color: #a0a0a0; margin-bottom: 40px; font-family: sans-serif;'>Initialize a brand profile to begin governance operations.</p>""", unsafe_allow_html=True)
        
        if st.session_state['dashboard_upload_open']:
            with st.container():
                st.markdown("""<div class="dashboard-card" style="border-left: 4px solid #f5f5f0;"><h3 style="color: #f5f5f0;">UPLOAD BRAND GUIDE (PDF)</h3><p style="color: #a0a0a0;">The engine will extract Strategy, Voice, and Visual rules automatically.</p></div>""", unsafe_allow_html=True)
                dash_pdf = st.file_uploader("SELECT PDF", type=["pdf"], key="dash_pdf_uploader")
                col_sub, col_can = st.columns([1, 1])
                with col_sub:
                    if dash_pdf and st.button("PROCESS & INGEST", type="primary"):
                        with st.spinner("ANALYZING PDF STRUCTURE..."):
                            try:
                                raw_text = logic.extract_text_from_pdf(dash_pdf)[:50000]
                                parsing_prompt = f"TASK: Analyze this Brand Guide PDF...\nRAW PDF CONTENT:\n{raw_text}"
                                profile_data = logic.generate_brand_rules(parsing_prompt)
                                # Save to DB immediately
                                profile_name = f"{dash_pdf.name} (PDF)"
                                db.save_profile(st.session_state['user_id'], profile_name, profile_data)
                                st.session_state['profiles'][profile_name] = profile_data
                                
                                st.success(f"SUCCESS: {dash_pdf.name} ingested.")
                                st.session_state['dashboard_upload_open'] = False
                                st.rerun()
                            except Exception as e:
                                if "ResourceExhausted" in str(e): st.error("⚠️ AI QUOTA EXCEEDED: The engine needs a break. Please wait 60 seconds.")
                                else: st.error(f"Error: {e}")
                with col_can:
                    if st.button("CANCEL"):
                        st.session_state['dashboard_upload_open'] = False
                        st.rerun()
            st.divider()

        st.markdown("""<style>
            div[data-testid*="Column"] .stButton button {
                background: linear-gradient(135deg, #1b2a2e 0%, #111 100%) !important; border: 1px solid #3a4b50 !important; height: 250px !important; width: 100% !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; color: #f5f5f0 !important; border-radius: 0px !important; box-shadow: none !important; padding-top: 50px !important; position: relative !important; white-space: pre-wrap !important;
            }
            div[data-testid*="Column"] .stButton button:hover { transform: translateY(-5px) !important; border-color: #ab8f59 !important; box-shadow: 0 10px 30px rgba(0,0,0,0.4) !important; color: #ab8f59 !important; }
            div[data-testid*="Column"] .stButton button p { font-size: 1rem !important; font-weight: 700 !important; letter-spacing: 0.1em; }
            div[data-testid*="Column"]:nth-of-type(1) .stButton button::before { content: ''; position: absolute; top: 40px; width: 40px; height: 40px; border: 2px solid #ab8f59; box-shadow: 5px 5px 0px #5c6b61; }
            div[data-testid*="Column"]:nth-of-type(2) .stButton button::before { content: ''; position: absolute; top: 40px; width: 30px; height: 40px; border: 2px solid #ab8f59; background: linear-gradient(to bottom, transparent 20%, #ab8f59 20%, #ab8f59 25%, transparent 25%, transparent 40%, #ab8f59 40%, #ab8f59 45%, transparent 45%); }
            div[data-testid*="Column"]:nth-of-type(3) .stButton button::before { content: ''; position: absolute; top: 40px; width: 40px; height: 40px; border: 2px solid #ab8f59; border-radius: 50%; background: radial-gradient(circle, #5c6b61 20%, transparent 21%); }
        </style>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.button("\nCREATE PROFILE\nArchitect a new brand identity", on_click=nav_to, args=("BRAND ARCHITECT",))
        with c2: 
            if st.button("\nUPLOAD GUIDE\nIngest existing PDF rules"):
                st.session_state['dashboard_upload_open'] = True
                st.rerun()
        with c3:
            if st.button("\nLOAD DEMO\nLoad Castellan sample data"):
                 demo_data = {
                     "final_text": "1. STRATEGY: Mission: Architecting Strategic Narratives... Archetype: The Ruler.\n2. VOICE: Professional...",
                     "inputs": {
                         "wiz_name": "Castellan PR", "wiz_archetype": "The Ruler", "wiz_tone": "Professional, Direct",
                         "wiz_mission": "Architecting narratives.", "wiz_values": "Precision, Power.",
                         "wiz_guardrails": "No fluff.", "palette_primary": ["#24363b"], "palette_secondary": ["#ab8f59"], "palette_accent": ["#f5f5f0"]
                     }
                 }
                 st.session_state['profiles']["Castellan PR (Demo)"] = demo_data
                 db.save_profile(st.session_state['user_id'], "Castellan PR (Demo)", demo_data)
                 st.rerun()
        
        # --- EXISTING BRAND SIGNALS (TIERED METER) ---
        st.divider()
        st.markdown("### EXISTING BRAND SIGNALS")
        
        profiles = db.get_profiles(st.session_state['user_id'])
        
        if not profiles:
            st.info("No active signals found. Initialize a profile above.")
        else:
            profile_names = list(profiles.keys())
            for i in range(0, len(profile_names), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(profile_names):
                        p_name = profile_names[i+j]
                        p_data = profiles[p_name]
                        
                        with cols[j]:
                            with st.container():
                                st.markdown(f"<div class='dashboard-card'>", unsafe_allow_html=True)
                                st.markdown(f"#### {p_name}")
                                
                                metrics = calculate_calibration_score(p_data)
                                
                                st.markdown(f"""
                                    <style>
                                        .metric-container {{ font-family: 'Source Sans Pro', sans-serif; margin-bottom: 15px; }}
                                        .metric-header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px; }}
                                        .metric-label {{ font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #5c6b61; }}
                                        .metric-value {{ font-size: 0.85rem; font-weight: 800; color: {metrics['color']}; }}
                                        .progress-track {{ width: 100%; height: 5px; background-color: #dcdcd9; border-radius: 999px; overflow: hidden; }}
                                        .progress-fill {{ height: 100%; width: {metrics['score']}%; background-color: {metrics['color']}; border-radius: 999px; transition: width 0.8s ease; }}
                                        .metric-hint {{ font-size: 0.75rem; color: #5c6b61; margin-top: 6px; font-style: italic; opacity: 0.9; min-height: 2.4em; }}
                                    </style>
                                    <div class="metric-container">
                                        <div class="metric-header">
                                            <span class="metric-label">{metrics['status_label']}</span>
                                            <span class="metric-value">{metrics['score']}%</span>
                                        </div>
                                        <div class="progress-track">
                                            <div class="progress-fill"></div>
                                        </div>
                                        <div class="metric-hint">{metrics['message']}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                if st.button("ACTIVATE SIGNAL", key=f"open_{p_name}", use_container_width=True):
                                    st.session_state['active_profile'] = p_name
                                    st.session_state['app_mode'] = "BRAND ARCHITECT"
                                    st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br><div style='background-color: rgba(36, 54, 59, 0.5); border-top: 1px solid #3a4b50; padding: 20px; text-align: center; border-radius: 4px;'><h3 style='color: #ab8f59; margin-bottom: 10px; font-size: 1rem; letter-spacing: 0.1em;'>INTELLIGENT BRAND GOVERNANCE</h3><p style='color: #a0a0a0; font-family: sans-serif; font-size: 0.9rem; line-height: 1.6; max-width: 800px; margin: 0 auto;'>Signet is a proprietary engine...</p></div>", unsafe_allow_html=True)
    else:
        st.title("SYSTEM STATUS")
        
        # Calculate metrics for the active profile display too
        metrics = calculate_calibration_score(current_rules)
        
        st.markdown(f"""<div class="dashboard-card"><div style="color: #a0a0a0; font-size: 0.8rem; letter-spacing: 0.1em; margin-bottom: 5px;">ACTIVE PROFILE</div><div style="font-size: 2.5rem; color: #f5f5f0; font-weight: 800;">{active_profile}</div><div style="color: {metrics['color']}; margin-top: 5px; font-weight: 700;">STATUS: {metrics['status_label'].upper()} ({metrics['score']}%)</div></div>""", unsafe_allow_html=True)

# 2. VISUAL COMPLIANCE
elif app_mode == "VISUAL COMPLIANCE":
    st.title("VISUAL COMPLIANCE AUDIT")
    if not active_profile: st.warning("NO PROFILE SELECTED.")
    else:
        uploaded_file = st.file_uploader("UPLOAD ASSET", type=["jpg", "png"])
        if uploaded_file and st.button("RUN AUDIT", type="primary"):
            with st.spinner("ANALYZING PIXELS..."):
                prof_text = current_rules['final_text'] if isinstance(current_rules, dict) else current_rules
                result = logic.run_visual_audit(Image.open(uploaded_file), prof_text)
                st.markdown(result)

# 3. COPY EDITOR
elif app_mode == "COPY EDITOR":
    st.title("COPY EDITOR")
    if not active_profile: st.warning("NO PROFILE SELECTED.")
    else:
        c1, c2 = st.columns([2, 1])
        with c1: 
            text_input = st.text_area("DRAFT TEXT", height=300, placeholder="PASTE DRAFT COPY HERE...")
            cc1, cc2, cc3 = st.columns(3)
            with cc1: content_type = st.selectbox("CONTENT TYPE", ["Internal Email", "Press Release", "Blog Post", "Executive Memo", "Website Copy"])
            with cc2: sender = st.text_input("SENDER / VOICE", placeholder="e.g. CEO, Support Team")
            with cc3: audience = st.text_input("TARGET AUDIENCE", placeholder="e.g. Investors, Employees")
        with c2: st.markdown(f"""<div class="dashboard-card"><h4>TARGET VOICE</h4><h3>{active_profile}</h3></div>""", unsafe_allow_html=True)
        
        if text_input and st.button("ANALYZE & REWRITE", type="primary"):
            with st.spinner("REWRITING..."):
                prof_text = current_rules['final_text'] if isinstance(current_rules, dict) else current_rules
                context_wrapper = f"CONTEXT: Type: {content_type}, Sender: {sender}, Audience: {audience}\nDRAFT CONTENT: {text_input}"
                result = logic.run_copy_editor(context_wrapper, prof_text)
                st.markdown(result)

# 4. CONTENT GENERATOR
elif app_mode == "CONTENT GENERATOR":
    st.title("CONTENT GENERATOR")
    c1, c2 = st.columns(2)
    with c1: format_type = st.selectbox("TYPE", ["Press Release", "Email", "LinkedIn Post", "Article"])
    with c2: topic = st.text_input("TOPIC")
    audience = st.text_input("TARGET AUDIENCE", placeholder="e.g. Investors, Gen Z, Current Customers")
    key_points = st.text_area("KEY POINTS", height=150, placeholder="- Key point 1\n- Key point 2")
    if st.button("GENERATE DRAFT", type="primary"):
        with st.spinner("DRAFTING..."):
            prof_text = current_rules['final_text'] if isinstance(current_rules, dict) else current_rules
            full_prompt_topic = f"{topic} (Audience: {audience})"
            result = logic.run_content_generator(full_prompt_topic, format_type, key_points, prof_text)
            st.markdown(result)

# 5. SOCIAL MEDIA ASSISTANT
elif app_mode == "SOCIAL MEDIA ASSISTANT":
    st.title("SOCIAL MEDIA ASSISTANT")
    if not active_profile: st.warning("NO PROFILE SELECTED.")
    else:
        c1, c2 = st.columns([1, 1])
        with c1:
            platform = st.selectbox("PLATFORM", ["LinkedIn", "Instagram", "X (Twitter)", "TikTok", "Facebook"])
            topic_social = st.text_area("TOPIC / CAPTION INTENT", height=100, placeholder="What is this post about?")
        with c2:
            social_img = st.file_uploader("UPLOAD VISUAL (Optional)", type=["jpg", "png"])
            
        if st.button("GENERATE POST", type="primary"):
            with st.spinner("ANALYZING & DRAFTING..."):
                prof_text = current_rules['final_text'] if isinstance(current_rules, dict) else current_rules
                img_context = ""
                if social_img:
                    desc = logic.analyze_social_post(Image.open(social_img))
                    img_context = f"IMAGE CONTEXT: The post includes an image described as: {desc}"
                
                social_prompt = f"""
                TASK: Write a social media post for {platform}.
                TOPIC: {topic_social}
                {img_context}
                INSTRUCTIONS:
                1. Apply the 'Social Media' rules from the Brand Profile.
                2. Use the 'High Performing Posts' in the profile as a benchmark for tone/length.
                3. Adhere to platform best practices for {platform} (hashtags, emoji usage, length).
                4. Provide a 'Rationale' section explaining why you chose this angle.
                """
                result = logic.run_content_generator(social_prompt, f"{platform} Post", "See prompt", prof_text)
                st.markdown(result)

# 6. BRAND ARCHITECT
elif app_mode == "BRAND ARCHITECT":
    st.title("BRAND ARCHITECT")
    
    # PERSISTENCE HANDLED AUTOMATICALLY UPON GENERATION NOW
    st.info("Profiles are automatically saved to your account upon generation.")
    
    tab1, tab2 = st.tabs(["WIZARD", "PDF EXTRACT"])
    with tab1:
        with st.expander("1. STRATEGY (CORE)", expanded=True):
            st.text_input("BRAND NAME", key="wiz_name")
            c1, c2 = st.columns(2)
            with c1: st.selectbox("ARCHETYPE *", ARCHETYPES, index=None, placeholder="SELECT...", key="wiz_archetype")
            with c2: st.text_input("TONE KEYWORDS", placeholder="e.g. Witty, Professional, Bold", key="wiz_tone")
            st.text_area("MISSION STATEMENT", key="wiz_mission")
            st.text_area("CORE VALUES", placeholder="e.g. Transparency, Innovation, Community", key="wiz_values")
            st.text_area("BRAND GUARDRAILS (DO'S & DON'TS)", placeholder="e.g. Don't use emojis.", key="wiz_guardrails")
            
        with st.expander("2. VOICE & CALIBRATION"):
            st.caption("Upload existing content to train the engine on your voice.")
            st.selectbox("CONTENT TYPE", ["Internal Email", "Executive Memo", "Press Release", "Article/Blog", "Social Post", "Website Copy", "Other"], key="wiz_sample_type")
            v_tab1, v_tab2 = st.tabs(["PASTE TEXT", "UPLOAD FILE"])
            with v_tab1: st.text_area("PASTE TEXT HERE", key="wiz_temp_text", height=150)
            with v_tab2:
                u_key = f"uploader_{st.session_state['file_uploader_key']}"
                st.file_uploader("UPLOAD (PDF, DOCX, TXT, IMG)", type=["pdf", "docx", "txt", "png", "jpg"], key=u_key)
            st.button("ADD SAMPLE", on_click=add_voice_sample_callback)
            if st.session_state['wiz_samples_list']: 
                st.divider()
                st.markdown(f"**VOICE BUFFER: {len(st.session_state['wiz_samples_list'])} SAMPLES**")
                for i, sample in enumerate(st.session_state['wiz_samples_list']):
                    col_text, col_del = st.columns([4, 1])
                    with col_text: st.caption(f"> {sample.splitlines()[0]}")
                    with col_del:
                        if st.button("REMOVE", key=f"del_sample_{i}", type="secondary"):
                            st.session_state['wiz_samples_list'].pop(i)
                            st.rerun()

        with st.expander("3. SOCIAL MEDIA"):
            st.caption("Upload screenshots of high-performing posts.")
            st.selectbox("PLATFORM", ["LinkedIn", "Instagram", "X (Twitter)", "Facebook", "Other"], key="wiz_social_platform")
            s_key = f"social_up_{st.session_state['social_uploader_key']}"
            st.file_uploader("UPLOAD SCREENSHOT", type=["png", "jpg"], key=s_key)
            st.button("ADD SOCIAL SAMPLE", on_click=add_social_callback)
            if st.session_state['wiz_social_list']:
                st.divider()
                st.markdown(f"**SOCIAL BUFFER: {len(st.session_state['wiz_social_list'])} IMAGES**")
                for i, item in enumerate(st.session_state['wiz_social_list']):
                    c1, c2 = st.columns([4,1])
                    with c1: st.caption(f"> {item['platform']} - {item['file'].name}")
                    with c2: 
                        if st.button("REMOVE", key=f"del_social_{i}", type="secondary"):
                            st.session_state['wiz_social_list'].pop(i)
                            st.rerun()
            
        with st.expander("4. VISUALS (DYNAMIC PALETTE)"):
            st.markdown("##### LOGO")
            l_key = f"logo_up_{st.session_state['logo_uploader_key']}"
            st.file_uploader("UPLOAD LOGO", type=["png", "jpg", "svg"], key=l_key)
            st.button("ADD LOGO", on_click=add_logo_callback)
            if st.session_state['wiz_logo_list']:
                st.divider()
                st.markdown(f"**LOGO BUFFER: {len(st.session_state['wiz_logo_list'])} FILES**")
                for i, item in enumerate(st.session_state['wiz_logo_list']):
                    c1, c2 = st.columns([4,1])
                    with c1: st.caption(f"> {item['file'].name}")
                    with c2: 
                        if st.button("REMOVE", key=f"del_logo_{i}", type="secondary"):
                            st.session_state['wiz_logo_list'].pop(i)
                            st.rerun()
            st.divider()
            
            st.markdown("##### COLOR PALETTE")
            st.caption("Press 'Enter' after pasting a hex code for it to register.")
            
            st.markdown("**PRIMARY COLORS**")
            for i, color in enumerate(st.session_state['palette_primary']):
                c1, c2 = st.columns([4,1])
                with c1: st.session_state['palette_primary'][i] = st.color_picker(f"Primary {i+1}", color, key=f"p_{i}")
                with c2:
                    if st.button("REMOVE", key=f"del_p_{i}", type="secondary"):
                        remove_palette_color('palette_primary', i)
                        st.rerun()
            st.button("ADD PRIMARY COLOR", on_click=add_palette_color, args=('palette_primary',))
            
            st.markdown("---")
            st.markdown("**SECONDARY COLORS**")
            for i, color in enumerate(st.session_state['palette_secondary']):
                c1, c2 = st.columns([4,1])
                with c1: st.session_state['palette_secondary'][i] = st.color_picker(f"Secondary {i+1}", color, key=f"s_{i}")
                with c2:
                    if st.button("REMOVE", key=f"del_s_{i}", type="secondary"):
                        remove_palette_color('palette_secondary', i)
                        st.rerun()
            st.button("ADD SECONDARY COLOR", on_click=add_palette_color, args=('palette_secondary',))
            
            st.markdown("---")
            st.markdown("**ACCENT COLORS**")
            for i, color in enumerate(st.session_state['palette_accent']):
                c1, c2 = st.columns([4,1])
                with c1: st.session_state['palette_accent'][i] = st.color_picker(f"Accent {i+1}", color, key=f"a_{i}")
                with c2:
                    if st.button("REMOVE", key=f"del_a_{i}", type="secondary"):
                        remove_palette_color('palette_accent', i)
                        st.rerun()
            st.button("ADD ACCENT COLOR", on_click=add_palette_color, args=('palette_accent',))

        if st.button("GENERATE SYSTEM", type="primary"):
            if not st.session_state.get("wiz_name") or not st.session_state.get("wiz_archetype"): st.error("NAME/ARCHETYPE REQUIRED")
            else:
                with st.spinner("CALIBRATING..."):
                    try:
                        palette_str = f"Primary: {', '.join(st.session_state['palette_primary'])}. Secondary: {', '.join(st.session_state['palette_secondary'])}. Accents: {', '.join(st.session_state['palette_accent'])}."
                        logo_desc_list = [f"Logo Variant ({item['file'].name}): {logic.describe_logo(Image.open(item['file']))}" for item in st.session_state['wiz_logo_list']]
                        logo_summary = "\n".join(logo_desc_list) if logo_desc_list else "None provided."
                        social_desc_list = [f"Platform: {item['platform']}. Analysis: {logic.analyze_social_post(Image.open(item['file']))}" for item in st.session_state['wiz_social_list']]
                        social_summary = "\n".join(social_desc_list) if social_desc_list else "None provided."
                        all_samples = "\n---\n".join(st.session_state['wiz_samples_list'])
                        
                        prompt = f"""
                        SYSTEM INSTRUCTION: Generate a comprehensive brand profile strictly following the numbered format below.
                        1. STRATEGY: Brand: {st.session_state.wiz_name}. Archetype: {st.session_state.wiz_archetype}. Mission: {st.session_state.wiz_mission}. Values: {st.session_state.wiz_values}
                        2. VOICE: Tone: {st.session_state.wiz_tone}. Analysis: {all_samples}
                        3. VISUALS: Palette: {palette_str}. Logo: {logo_summary}. Social: {social_summary}
                        4. GUARDRAILS: {st.session_state.wiz_guardrails}
                        """
                        
                        final_text_out = logic.generate_brand_rules(prompt)
                        profile_data = {
                            "final_text": final_text_out,
                            "inputs": {
                                "wiz_name": st.session_state.wiz_name,
                                "wiz_archetype": st.session_state.wiz_archetype,
                                "wiz_tone": st.session_state.wiz_tone,
                                "wiz_mission": st.session_state.wiz_mission,
                                "wiz_values": st.session_state.wiz_values,
                                "wiz_guardrails": st.session_state.wiz_guardrails,
                                "palette_primary": st.session_state['palette_primary'],
                                "palette_secondary": st.session_state['palette_secondary'],
                                "palette_accent": st.session_state['palette_accent']
                            }
                        }
                        
                        profile_name = f"{st.session_state.wiz_name} (Gen)"
                        st.session_state['profiles'][profile_name] = profile_data
                        
                        # SAVE TO DB
                        db.save_profile(st.session_state['user_id'], profile_name, profile_data)
                        
                        st.session_state['wiz_samples_list'] = []
                        st.session_state['wiz_social_list'] = []
                        st.session_state['wiz_logo_list'] = []
                        st.success("CALIBRATED & SAVED TO DATABASE")
                        st.rerun()
                    except Exception as e:
                        if "ResourceExhausted" in str(e): st.error("⚠️ AI QUOTA EXCEEDED: Please wait 60 seconds.")
                        else: st.error(f"Error: {e}")

    with tab2:
        pdf = st.file_uploader("UPLOAD PDF", type=["pdf"])
        if pdf and st.button("EXTRACT"):
            try:
                st.session_state['profiles'][f"{pdf.name} (PDF)"] = logic.generate_brand_rules(f"Extract: {logic.extract_text_from_pdf(pdf)[:20000]}")
                st.success("EXTRACTED")
            except Exception as e: st.error(f"Error: {e}")

# 7. BRAND MANAGER
elif app_mode == "BRAND MANAGER":
    st.title("BRAND MANAGER")
    if st.session_state['profiles']:
        target = st.selectbox("PROFILE", list(st.session_state['profiles'].keys()))
        profile_obj = st.session_state['profiles'][target]
        
        is_structured = isinstance(profile_obj, dict) and "inputs" in profile_obj
        final_text_view = profile_obj['final_text'] if is_structured else profile_obj
        
        html_data = convert_to_html_brand_card(target, final_text_view)
        st.download_button(label="📄 DOWNLOAD BRAND KIT (HTML)", data=html_data, file_name=f"{target.replace(' ', '_')}_BrandKit.html", mime="text/html", use_container_width=True)
        
        st.divider()
        
        if is_structured:
            inputs = profile_obj['inputs']
            
            with st.expander("1. STRATEGY", expanded=True):
                new_name = st.text_input("BRAND NAME", inputs['wiz_name'])
                idx = ARCHETYPES.index(inputs['wiz_archetype']) if inputs['wiz_archetype'] in ARCHETYPES else 0
                new_arch = st.selectbox("ARCHETYPE", ARCHETYPES, index=idx)
                new_mission = st.text_area("MISSION", inputs['wiz_mission'])
                new_values = st.text_area("VALUES", inputs['wiz_values'])
            
            with st.expander("2. VOICE"):
                new_tone = st.text_input("TONE KEYWORDS", inputs['wiz_tone'])
            
            with st.expander("3. GUARDRAILS"):
                new_guard = st.text_area("DO'S & DON'TS", inputs['wiz_guardrails'])
            
            if st.button("SAVE CHANGES & REGENERATE PROFILE"):
                profile_obj['inputs']['wiz_name'] = new_name
                profile_obj['inputs']['wiz_archetype'] = new_arch
                profile_obj['inputs']['wiz_mission'] = new_mission
                profile_obj['inputs']['wiz_values'] = new_values
                profile_obj['inputs']['wiz_tone'] = new_tone
                profile_obj['inputs']['wiz_guardrails'] = new_guard
                
                p_p = ", ".join(inputs['palette_primary'])
                p_s = ", ".join(inputs['palette_secondary'])
                
                new_text = f"""
                1. STRATEGY
                - Brand: {new_name}
                - Archetype: {new_arch}
                - Mission: {new_mission}
                - Values: {new_values}
                
                2. VOICE
                - Tone Keywords: {new_tone}
                
                3. VISUALS
                - Primary: {p_p}
                - Secondary: {p_s}
                
                4. GUARDRAILS
                - {new_guard}
                """
                profile_obj['final_text'] = new_text
                st.session_state['profiles'][target] = profile_obj
                
                # UPDATE DB
                db.save_profile(st.session_state['user_id'], target, profile_obj)
                
                st.success("UPDATED & REBUILT")
                st.rerun()

        else:
            st.warning("This profile was created from a PDF/Raw Text. Structured editing is unavailable.")
            new_raw = st.text_area("EDIT RAW TEXT", final_text_view, height=500)
            if st.button("SAVE RAW CHANGES"):
                st.session_state['profiles'][target] = new_raw
                db.save_profile(st.session_state['user_id'], target, new_raw)
                st.success("SAVED")

        if st.button("DELETE PROFILE"): 
            del st.session_state['profiles'][target]
            db.delete_profile(st.session_state['user_id'], target)
            st.rerun()

# --- FOOTER ---
st.markdown("""<div class="footer">POWERED BY CASTELLAN PR // INTERNAL USE ONLY</div>""", unsafe_allow_html=True)

