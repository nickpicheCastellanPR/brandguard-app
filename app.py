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
    
    /* Red delete button override */
    button[kind="secondary"] {
        border-color: #ff5f56 !important;
        color: #ff5f56 !important;
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
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'check_count' not in st.session_state: st.session_state['check_count'] = 0

# WIZARD STATE LISTS
if 'wiz_samples_list' not in st.session_state: st.session_state['wiz_samples_list'] = []
if 'wiz_social_list' not in st.session_state: st.session_state['wiz_social_list'] = [] # Stores: {'platform': str, 'file': UploadedFile}
if 'wiz_logo_list' not in st.session_state: st.session_state['wiz_logo_list'] = []     # Stores: {'file': UploadedFile}

# DYNAMIC KEYS FOR UPLOADERS
if 'file_uploader_key' not in st.session_state: st.session_state['file_uploader_key'] = 0 
if 'social_uploader_key' not in st.session_state: st.session_state['social_uploader_key'] = 1000
if 'logo_uploader_key' not in st.session_state: st.session_state['logo_uploader_key'] = 2000

if 'profiles' not in st.session_state:
    st.session_state['profiles'] = {}

MAX_CHECKS = 50

ARCHETYPES = [
    "The Ruler", "The Creator", "The Sage", "The Innocent", 
    "The Outlaw", "The Magician", "The Hero", "The Lover", 
    "The Jester", "The Everyman", "The Caregiver", "The Explorer"
]

# --- HELPER FUNCTIONS ---
def calculate_calibration_score(profile_data):
    score = 0
    missing = []
    if "STRATEGY" in profile_data: score += 10
    if "VOICE" in profile_data: score += 10
    if "VISUALS" in profile_data: score += 10
    if "LOGO RULES" in profile_data: score += 10
    if "TYPOGRAPHY" in profile_data: score += 10
    if "Style Signature" in profile_data: score += 25
    else: missing.append("Voice Samples")
    if "SOCIAL MEDIA" in profile_data: score += 25
    else: missing.append("Social Screenshots")
    return score, missing

def add_voice_sample_callback():
    """Safely adds text/file sample from state variables and resets inputs."""
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
    """Adds a social media image to the buffer."""
    s_platform = st.session_state.get('wiz_social_platform', 'Other')
    u_key = f"social_up_{st.session_state['social_uploader_key']}"
    s_file = st.session_state.get(u_key, None)
    
    if s_file:
        st.session_state['wiz_social_list'].append({
            'platform': s_platform,
            'file': s_file
        })
        # Reset uploader
        st.session_state['social_uploader_key'] += 1

def add_logo_callback():
    """Adds a logo file to the buffer."""
    u_key = f"logo_up_{st.session_state['logo_uploader_key']}"
    s_file = st.session_state.get(u_key, None)
    
    if s_file:
        st.session_state['wiz_logo_list'].append({
            'file': s_file
        })
        # Reset uploader
        st.session_state['logo_uploader_key'] += 1

# --- LOGIN SCREEN (ARCHITECTURAL VIGNETTE + GRADIENT CORNERS) ---
if not st.session_state['authenticated']:
    st.markdown("""
    <style>
        .stApp {
            background-color: #f5f5f0 !important;
            /* Layer 1: The Blueprint Grid (Top) 
               Layer 2: Top-Left Sage Corner (Radial)
               Layer 3: Bottom-Right Teal Corner (Radial)
            */
            background-image: 
                linear-gradient(rgba(36, 54, 59, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(36, 54, 59, 0.05) 1px, transparent 1px),
                
                radial-gradient(circle at 0% 0%, rgba(92, 107, 97, 0.5) 0%, rgba(92, 107, 97, 0.1) 40%, transparent 70%),
                radial-gradient(circle at 100% 100%, rgba(36, 54, 59, 0.4) 0%, rgba(36, 54, 59, 0.1) 40%, transparent 70%);
                
            background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100%;
        }
        section[data-testid="stSidebar"] { display: none; }
        
        .stTextInput input {
            background-color: #ffffff !important;
            color: #24363b !important;
            border: 1px solid #c0c0c0 !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            /* Reset dark mode override for login screen specifically */
            -webkit-text-fill-color: #24363b !important;
        }
        .stTextInput input:focus { border-color: #24363b !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", width=300)
        else:
            st.markdown("<div style='text-align: center; font-size: 3.5rem; color: #24363b; font-weight: 800; letter-spacing: 0.15em;'>SIGNET</div>", unsafe_allow_html=True)
        
        st.markdown("<div style='text-align: center; color: #5c6b61; font-size: 0.8rem; letter-spacing: 0.3em; font-weight: 700; margin-top: 15px; margin-bottom: 30px;'>INTELLIGENT BRAND GOVERNANCE</div>", unsafe_allow_html=True)
        
        password = st.text_input("ACCESS KEY", type="password", label_visibility="collapsed", placeholder="ENTER ACCESS KEY")
        
        if st.button("INITIALIZE SYSTEM", type="primary"):
            if logic.check_password(password):
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("⛔ ACCESS DENIED")
                
        st.markdown("<br><div style='text-align: center; color: #ab8f59; font-size: 0.7rem; letter-spacing: 0.2em;'>CASTELLAN PR INTERNAL TOOL</div>", unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR (AUTHENTICATED) ---
with st.sidebar:
    if os.path.exists("Signet_Logo_Color.png"):
        st.image("Signet_Logo_Color.png", use_container_width=True)
    else:
        st.markdown('<div style="font-size: 2rem; color: #24363b; font-weight: 900; letter-spacing: 0.1em; text-align: center; margin-bottom: 20px;">SIGNET</div>', unsafe_allow_html=True)
    
    profile_names = list(st.session_state['profiles'].keys())
    
    if profile_names:
        active_profile = st.selectbox("ACTIVE PROFILE", profile_names)
        current_rules = st.session_state['profiles'][active_profile]
        cal_score, missing_items = calculate_calibration_score(current_rules)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("ENGINE CONFIDENCE")
        st.progress(cal_score / 100)
        
        if cal_score < 60: 
            st.markdown("<span style='color: #ab8f59; font-weight: 700;'>⚠️ LOW CALIBRATION</span>", unsafe_allow_html=True)
        elif cal_score < 90: 
            st.markdown("<span style='color: #ab8f59; font-weight: 700;'>⚠️ PARTIAL CALIBRATION</span>", unsafe_allow_html=True)
        else: 
            st.markdown("<span style='color: #5c6b61; font-weight: 700;'>✅ OPTIMIZED</span>", unsafe_allow_html=True)
    else:
        active_profile = None
        cal_score = 0
        current_rules = ""
        missing_items = []
        st.markdown("<div style='text-align:center; color:#5c6b61; font-size:0.8rem; margin-bottom:20px; font-weight:700;'>NO PROFILE LOADED</div>", unsafe_allow_html=True)

    st.divider()
    app_mode = st.radio("MODULES", ["DASHBOARD", "VISUAL COMPLIANCE", "COPY EDITOR", "CONTENT GENERATOR", "BRAND ARCHITECT", "BRAND MANAGER"], label_visibility="collapsed")
    
    st.divider()
    st.markdown("<div style='text-align: center; color: #24363b; font-size: 0.6rem; letter-spacing: 0.1em; margin-bottom: 10px;'>POWERED BY CASTELLAN PR</div>", unsafe_allow_html=True)
    if st.button("SHUT DOWN"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- MODULES ---

# 1. DASHBOARD
if app_mode == "DASHBOARD":
    
    if not active_profile:
        st.title("WELCOME TO SIGNET")
        st.markdown("""<p style='font-size: 1.1rem; color: #a0a0a0; margin-bottom: 40px; font-family: sans-serif;'>Initialize a brand profile to begin governance operations.</p>""", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class="hero-card"><div class="icon-build"></div><div class="hero-title">Create Profile</div><div class="hero-desc">Architect a new brand identity.</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div class="hero-card"><div class="icon-doc"></div><div class="hero-title">Upload Guide</div><div class="hero-desc">Ingest existing PDF rules.</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div class="hero-card"><div class="icon-gear"></div><div class="hero-title">Load Demo</div><div class="hero-desc">Load Castellan sample data.</div></div>""", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("LOAD DEMO DATA", type="primary"):
            st.session_state['profiles']["Castellan PR (Demo)"] = """
            1. STRATEGY: Mission: Architecting Strategic Narratives... Archetype: The Ruler.
            2. VOICE: Professional, Authoritative, Direct. Style Signature: Concise.
            3. VISUALS: Deep Teal, Muted Gold, Cream.
            4. DATA DEPTH: High.
            """
            st.rerun()

        st.markdown("""<div style="margin-top: 20px; padding: 15px; border: 1px solid #ab8f59; border-left: 4px solid #ab8f59; background: rgba(171, 143, 89, 0.1); color: #f5f5f0;">👉 To start fresh, select <strong>BRAND ARCHITECT</strong> from the sidebar.</div>""", unsafe_allow_html=True)

    else:
        st.title("SYSTEM STATUS")
        st.markdown(f"""<div class="dashboard-card"><div style="color: #a0a0a0; font-size: 0.8rem; letter-spacing: 0.1em; margin-bottom: 5px;">ACTIVE PROFILE</div><div style="font-size: 2.5rem; color: #f5f5f0; font-weight: 800;">{active_profile}</div><div style="color: #ab8f59; margin-top: 5px; font-weight: 700;">CALIBRATION SCORE: {cal_score}/100</div></div>""", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("ENGINE CAPABILITIES")
            st.markdown(f"""
            <div class="status-row">
                <span class="status-label">STRATEGY ENGINE</span>
                <span><span class="status-dot {'dot-green' if cal_score > 50 else 'dot-red'}"></span><span style="color: #f5f5f0; font-weight:700; font-size:0.8rem;">{'ONLINE' if cal_score > 50 else 'OFFLINE'}</span></span>
            </div>
            <div class="status-row">
                <span class="status-label">VOICE ENGINE</span>
                <span><span class="status-dot {'dot-green' if cal_score > 70 else 'dot-yellow'}"></span><span style="color: #f5f5f0; font-weight:700; font-size:0.8rem;">{'ONLINE' if cal_score > 70 else 'CALIBRATING'}</span></span>
            </div>
            <div class="status-row">
                <span class="status-label">SOCIAL ENGINE</span>
                <span><span class="status-dot {'dot-green' if cal_score > 90 else 'dot-red'}"></span><span style="color: #f5f5f0; font-weight:700; font-size:0.8rem;">{'ONLINE' if cal_score > 90 else 'NO DATA'}</span></span>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.subheader("REQUIRED ACTIONS")
            if missing_items:
                for item in missing_items: 
                    st.markdown(f"""<div style="background: rgba(171, 143, 89, 0.1); border-left: 3px solid #ab8f59; color: #ab8f59; padding: 12px; margin-bottom: 8px;"><div style="font-weight: 700; font-size: 0.9rem;">MISSING DATA: {item}</div><div style="font-size: 0.75rem; opacity: 0.8; color: #f5f5f0;">Navigate to Brand Architect to upload.</div></div>""", unsafe_allow_html=True)
            else: 
                st.markdown("""<div style="background: rgba(92, 107, 97, 0.2); border-left: 3px solid #5c6b61; color: #f5f5f0; padding: 12px;">✅ ALL SYSTEMS NOMINAL</div>""", unsafe_allow_html=True)

# 2. VISUAL COMPLIANCE
elif app_mode == "VISUAL COMPLIANCE":
    st.title("VISUAL COMPLIANCE AUDIT")
    if not active_profile: st.warning("NO PROFILE SELECTED.")
    else:
        uploaded_file = st.file_uploader("UPLOAD ASSET", type=["jpg", "png"])
        if uploaded_file and st.button("RUN AUDIT", type="primary"):
            with st.spinner("ANALYZING PIXELS..."):
                result = logic.run_visual_audit(Image.open(uploaded_file), current_rules)
                st.markdown(result)

# 3. COPY EDITOR
elif app_mode == "COPY EDITOR":
    st.title("COPY EDITOR")
    if not active_profile: st.warning("NO PROFILE SELECTED.")
    else:
        c1, c2 = st.columns([2, 1])
        with c1: text_input = st.text_area("DRAFT TEXT", height=300, placeholder="PASTE DRAFT COPY HERE...")
        with c2: st.markdown(f"""<div class="dashboard-card"><h4>TARGET VOICE</h4><h3>{active_profile}</h3></div>""", unsafe_allow_html=True)
        if text_input and st.button("ANALYZE & REWRITE", type="primary"):
            with st.spinner("REWRITING..."):
                result = logic.run_copy_editor(text_input, current_rules)
                st.markdown(result)

# 4. CONTENT GENERATOR
elif app_mode == "CONTENT GENERATOR":
    st.title("CONTENT GENERATOR")
    if cal_score < 60: st.warning(f"⚠️ LOW CONFIDENCE ({cal_score}%).")
    c1, c2 = st.columns(2)
    with c1: format_type = st.selectbox("TYPE", ["Press Release", "Email", "LinkedIn Post", "Article"])
    with c2: topic = st.text_input("TOPIC")
    key_points = st.text_area("KEY POINTS", height=150, placeholder="- Key point 1\n- Key point 2")
    if st.button("GENERATE DRAFT", type="primary"):
        with st.spinner("DRAFTING..."):
            result = logic.run_content_generator(topic, format_type, key_points, current_rules)
            st.markdown(result)

# 5. BRAND ARCHITECT
elif app_mode == "BRAND ARCHITECT":
    st.title("BRAND ARCHITECT")
    tab1, tab2 = st.tabs(["WIZARD", "PDF EXTRACT"])
    with tab1:
        # --- SECTION 1: STRATEGY ---
        with st.expander("1. STRATEGY (CORE)", expanded=True):
            wiz_name = st.text_input("BRAND NAME")
            c1, c2 = st.columns(2)
            with c1: wiz_archetype = st.selectbox("ARCHETYPE *", ARCHETYPES, index=None, placeholder="SELECT...")
            with c2: wiz_tone = st.text_input("TONE KEYWORDS", placeholder="e.g. Witty, Professional, Bold")
            wiz_mission = st.text_area("MISSION STATEMENT")
            wiz_values = st.text_area("CORE VALUES", placeholder="e.g. Transparency, Innovation, Community")
            
        # --- SECTION 2: VOICE & CALIBRATION (UPGRADED) ---
        with st.expander("2. VOICE & CALIBRATION"):
            st.caption("Upload existing content to train the engine on your voice.")
            
            # Type Selector
            st.selectbox("CONTENT TYPE", ["Internal Email", "Executive Memo", "Press Release", "Article/Blog", "Social Post", "Website Copy", "Other"], key="wiz_sample_type")
            
            # Input Methods
            v_tab1, v_tab2 = st.tabs(["PASTE TEXT", "UPLOAD FILE"])
            with v_tab1:
                st.text_area("PASTE TEXT HERE", key="wiz_temp_text", height=150)
            with v_tab2:
                # Dynamic key ensures the uploader clears after 'Add' is clicked
                u_key = f"uploader_{st.session_state['file_uploader_key']}"
                st.file_uploader("UPLOAD (PDF, DOCX, TXT, IMG)", type=["pdf", "docx", "txt", "png", "jpg"], key=u_key)
            
            # Add Button with Callback (Fixes the Error)
            st.button("➕ ADD SAMPLE", on_click=add_voice_sample_callback)
            
            # Display Buffer
            if st.session_state['wiz_samples_list']: 
                st.divider()
                st.markdown(f"**VOICE BUFFER: {len(st.session_state['wiz_samples_list'])} SAMPLES**")
                
                # Iterate safely with index to allow deletion
                for i, sample in enumerate(st.session_state['wiz_samples_list']):
                    col_text, col_del = st.columns([5, 1])
                    header = sample.split('\n')[0]
                    with col_text:
                        st.caption(f"✅ {header}")
                    with col_del:
                        if st.button("🗑️", key=f"del_sample_{i}", type="secondary"):
                            st.session_state['wiz_samples_list'].pop(i)
                            st.rerun()

        # --- SECTION 3: SOCIAL ---
        with st.expander("3. SOCIAL MEDIA"):
            st.caption("Upload screenshots of high-performing posts.")
            
            st.selectbox("PLATFORM", ["LinkedIn", "Instagram", "X (Twitter)", "Facebook", "Other"], key="wiz_social_platform")
            
            # Dynamic Key for Uploader
            s_key = f"social_up_{st.session_state['social_uploader_key']}"
            st.file_uploader("UPLOAD SCREENSHOT", type=["png", "jpg"], key=s_key)
            
            st.button("➕ ADD SOCIAL SAMPLE", on_click=add_social_callback)
            
            if st.session_state['wiz_social_list']:
                st.divider()
                st.markdown(f"**SOCIAL BUFFER: {len(st.session_state['wiz_social_list'])} IMAGES**")
                for i, item in enumerate(st.session_state['wiz_social_list']):
                    c1, c2 = st.columns([5,1])
                    with c1: st.caption(f"✅ {item['platform']} - {item['file'].name}")
                    with c2: 
                        if st.button("🗑️", key=f"del_social_{i}", type="secondary"):
                            st.session_state['wiz_social_list'].pop(i)
                            st.rerun()
            
        # --- SECTION 4: VISUALS ---
        with st.expander("4. VISUALS"):
            # Logo
            st.markdown("##### LOGO")
            l_key = f"logo_up_{st.session_state['logo_uploader_key']}"
            st.file_uploader("UPLOAD LOGO", type=["png", "jpg", "svg"], key=l_key)
            st.button("➕ ADD LOGO", on_click=add_logo_callback)
            
            if st.session_state['wiz_logo_list']:
                st.divider()
                st.markdown(f"**LOGO BUFFER: {len(st.session_state['wiz_logo_list'])} FILES**")
                for i, item in enumerate(st.session_state['wiz_logo_list']):
                    c1, c2 = st.columns([5,1])
                    with c1: st.caption(f"✅ {item['file'].name}")
                    with c2: 
                        if st.button("🗑️", key=f"del_logo_{i}", type="secondary"):
                            st.session_state['wiz_logo_list'].pop(i)
                            st.rerun()
            
            st.divider()
            
            # Color Palette Builder
            st.markdown("##### COLOR PALETTE")
            
            st.markdown("**PRIMARY (2)**")
            pc1, pc2 = st.columns(2)
            with pc1: p1 = st.color_picker("Primary 1", "#24363b")
            with pc2: p2 = st.color_picker("Primary 2", "#ab8f59")
            
            st.markdown("**SECONDARY (4)**")
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1: s1 = st.color_picker("Sec 1", "#f5f5f0")
            with sc2: s2 = st.color_picker("Sec 2", "#5c6b61")
            with sc3: s3 = st.color_picker("Sec 3", "#3d3d3d")
            with sc4: s4 = st.color_picker("Sec 4", "#1b2a2e")
            
            st.markdown("**ACCENT (2)**")
            ac1, ac2 = st.columns(2)
            with ac1: a1 = st.color_picker("Accent 1", "#ffffff")
            with ac2: a2 = st.color_picker("Accent 2", "#000000")
            
        # GENERATE BUTTON
        if st.button("GENERATE SYSTEM", type="primary"):
            if not wiz_name or not wiz_archetype: st.error("NAME/ARCHETYPE REQUIRED")
            else:
                with st.spinner("CALIBRATING..."):
                    
                    # 1. PROCESS LOGOS
                    logo_desc_list = []
                    for item in st.session_state['wiz_logo_list']:
                        # Logic class handles the analysis
                        desc = logic.describe_logo(Image.open(item['file']))
                        logo_desc_list.append(f"Logo Variant ({item['file'].name}): {desc}")
                    logo_summary = "\n".join(logo_desc_list) if logo_desc_list else "None provided."
                    
                    # 2. PROCESS SOCIAL
                    social_desc_list = []
                    for item in st.session_state['wiz_social_list']:
                        # Logic class handles analysis
                        raw_analysis = logic.analyze_social_post(Image.open(item['file']))
                        social_desc_list.append(f"Platform: {item['platform']}. Analysis: {raw_analysis}. (INSTRUCTION: Ignore comments/UI. Focus on image style, caption voice, and hashtags).")
                    social_summary = "\n".join(social_desc_list) if social_desc_list else "None provided."
                    
                    # 3. COMBINE SAMPLES
                    all_samples = "\n---\n".join(st.session_state['wiz_samples_list'])
                    
                    # 4. PALETTE
                    palette_str = f"Primary: {p1}, {p2}. Secondary: {s1}, {s2}, {s3}, {s4}. Accents: {a1}, {a2}."
                    
                    # 5. FINAL PROMPT
                    prompt = f"""
                    Profile for {wiz_name}. 
                    Archetype: {wiz_archetype}. 
                    Mission: {wiz_mission}. 
                    Values: {wiz_values}.
                    Tone Keywords: {wiz_tone}.
                    
                    TRAINING SAMPLES:
                    {all_samples}
                    
                    Social Analysis: {social_summary}. 
                    Logo Analysis: {logo_summary}.
                    Defined Palette: {palette_str}
                    """
                    
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = logic.generate_brand_rules(prompt)
                    
                    # CLEAR BUFFERS
                    st.session_state['wiz_samples_list'] = []
                    st.session_state['wiz_social_list'] = []
                    st.session_state['wiz_logo_list'] = []
                    
                    st.success("CALIBRATED")
                    st.rerun()
    with tab2:
        pdf = st.file_uploader("UPLOAD PDF", type=["pdf"])
        if pdf and st.button("EXTRACT"):
            st.session_state['profiles'][f"{pdf.name} (PDF)"] = logic.generate_brand_rules(f"Extract: {logic.extract_text_from_pdf(pdf)[:20000]}")
            st.success("EXTRACTED")

# 6. BRAND MANAGER
elif app_mode == "BRAND MANAGER":
    st.title("BRAND MANAGER")
    if st.session_state['profiles']:
        target = st.selectbox("PROFILE", list(st.session_state['profiles'].keys()))
        new_rules = st.text_area("EDIT", st.session_state['profiles'][target], height=400)
        c1, c2, c3 = st.columns(3)
        if c1.button("SAVE"): st.session_state['profiles'][target] = new_rules; st.success("SAVED")
        if c3.button("DELETE"): del st.session_state['profiles'][target]; st.rerun()

# --- FOOTER ---
st.markdown("""<div class="footer">POWERED BY CASTELLAN PR // INTERNAL USE ONLY</div>""", unsafe_allow_html=True)
