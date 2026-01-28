import streamlit as st
from PIL import Image
import os
from logic import SignetLogic

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Signet", 
    page_icon="Signet_Icon_Color.png", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Logic
logic = SignetLogic()

# --- THE DESIGN SYSTEM (Expert CSS) ---
st.markdown("""
<style>
    /* 1. COLOR PALETTE */
    :root {
        --bg-base: #0E1117;       /* Deepest Black */
        --bg-panel: #161B22;      /* Sidebar/Cards */
        --bg-input: #0d1117;      /* Input Fields */
        --gold-primary: #D4AF37;  /* Borders/Text */
        --gold-glow: rgba(212, 175, 55, 0.25);
        --text-cream: #F0EAD6;    /* Primary Headers */
        --text-grey: #8B949E;     /* Meta Text */
        --border-subtle: #30363D;
        --success: #238636;
        --error: #DA3633;
    }

    /* 2. TYPOGRAPHY & HEADERS */
    h1, h2, h3, p, div, span {
        font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif !important;
        letter-spacing: 0.02em;
    }
    
    h1 {
        font-weight: 800 !important;
        text-transform: uppercase;
        color: var(--text-cream) !important;
        font-size: 2.2rem !important;
        margin-bottom: 0px !important;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-subtle);
    }
    
    h3 {
        color: var(--gold-primary) !important;
        font-size: 1.1rem !important;
        text-transform: uppercase;
        font-weight: 700 !important;
        margin-top: 20px !important;
    }

    /* 3. INPUT FIELDS (CRITICAL FIX) */
    /* This forces inputs to be visible against the dark background */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: var(--bg-input) !important;
        border: 1px solid var(--border-subtle) !important;
        color: #E6EDF3 !important;
        border-radius: 4px !important;
    }
    
    /* Focus State: Gold Glow */
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--gold-primary) !important;
        box-shadow: 0 0 0 1px var(--gold-primary) !important;
    }

    /* 4. BUTTONS (Tactile Feel) */
    .stButton button {
        background-color: transparent !important;
        border: 1px solid var(--gold-primary) !important;
        color: var(--gold-primary) !important;
        border-radius: 0px !important; /* Sharp corners = High Tech */
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        transition: all 0.2s ease-in-out;
    }
    
    .stButton button:hover {
        background-color: var(--gold-glow) !important;
        box-shadow: 0 0 15px var(--gold-glow);
        transform: translateY(-1px);
        color: #FFF !important;
    }
    
    /* Primary Buttons */
    button[kind="primary"] {
        background: var(--gold-primary) !important;
        color: #000 !important;
        border: none !important;
    }

    /* 5. CUSTOM DASHBOARD CARDS (Replacing st.success) */
    .dashboard-card {
        background-color: var(--bg-panel);
        border: 1px solid var(--border-subtle);
        border-left: 4px solid var(--gold-primary);
        padding: 20px;
        margin-bottom: 15px;
        border-radius: 4px;
    }
    
    .status-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #0d1117;
        border: 1px solid var(--border-subtle);
        padding: 12px 16px;
        margin-bottom: 8px;
        border-radius: 4px;
        font-family: 'Courier New', monospace; /* Tech feel */
    }
    
    .status-label { font-weight: 700; color: #E6EDF3; font-size: 0.9rem; }
    .status-indicator { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }
    
    .online { color: #3FB950; text-shadow: 0 0 10px rgba(63, 185, 80, 0.4); }
    .offline { color: #F85149; }
    .calibrating { color: #D29922; }

    /* 6. SIDEBAR CLEANUP */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-panel);
        border-right: 1px solid var(--border-subtle);
    }
    .sidebar-logo-text {
        font-size: 2rem;
        font-weight: 900;
        color: var(--gold-primary);
        text-align: center;
        letter-spacing: 0.2em;
        margin-bottom: 20px;
    }

    /* 7. REMOVE BLOAT */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'check_count' not in st.session_state: st.session_state['check_count'] = 0
if 'wiz_temp_sample' not in st.session_state: st.session_state['wiz_temp_sample'] = ""
if 'wiz_samples_list' not in st.session_state: st.session_state['wiz_samples_list'] = []

if 'profiles' not in st.session_state:
    st.session_state['profiles'] = {
        "Apple (Creator)": """
        1. STRATEGY: Mission: Best user experience... Archetype: The Creator.
        2. VOICE: Innovative, Minimalist. Style Signature: Short sentences. High impact.
        3. VISUALS: Black, White, Grey. Sans-Serif fonts.
        4. DATA DEPTH: High (Social Samples, Press Samples included).
        """
    }

MAX_CHECKS = 50

ARCHETYPES = [
    "The Ruler: Control, leadership, responsibility",
    "The Creator: Innovation, imagination, expression",
    "The Sage: Wisdom, truth, expertise",
    "The Innocent: Optimism, safety, simplicity",
    "The Outlaw: Disruption, liberation, rebellion",
    "The Magician: Transformation, vision, wonder",
    "The Hero: Mastery, action, courage",
    "The Lover: Intimacy, connection, indulgence",
    "The Jester: Humor, play, enjoyment",
    "The Everyman: Belonging, connection, down-to-earth",
    "The Caregiver: Service, nurturing, protection",
    "The Explorer: Freedom, discovery, authenticity"
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

def add_voice_sample():
    if st.session_state.wiz_temp_sample:
        st.session_state['wiz_samples_list'].append(st.session_state.wiz_temp_sample)
        st.session_state.wiz_temp_sample = ""

# --- LOGIN SCREEN ---
if not st.session_state['authenticated']:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        # Replaced image with High-Contrast Text for reliability if image missing
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", width=160) 
        else:
            st.markdown("<div style='text-align: center; font-size: 3rem; color: #D4AF37; font-weight: 800; letter-spacing: 0.1em;'>SIGNET</div>", unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; color: #8B949E; font-size: 0.8rem; letter-spacing: 0.2em; margin-top: -10px;'>INTELLIGENT BRAND GOVERNANCE</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #30363D;'>", unsafe_allow_html=True)
        
        password = st.text_input("ACCESS KEY", type="password", label_visibility="collapsed", placeholder="ENTER ACCESS KEY")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INITIALIZE SYSTEM", type="primary"):
            if logic.check_password(password):
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("⛔ ACCESS DENIED")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("Signet_Logo_Color.png"):
        st.image("Signet_Logo_Color.png", use_container_width=True)
    else:
        st.markdown('<div class="sidebar-logo-text">SIGNET</div>', unsafe_allow_html=True)
    
    if st.session_state['profiles']:
        active_profile = st.selectbox("ACTIVE PROFILE", list(st.session_state['profiles'].keys()))
        current_rules = st.session_state['profiles'][active_profile]
        cal_score, missing_items = calculate_calibration_score(current_rules)
    else:
        active_profile = None
        cal_score = 0
        current_rules = ""
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("ENGINE CONFIDENCE")
    st.progress(cal_score / 100)
    
    # Custom Sidebar Status text
    if cal_score < 60: 
        st.markdown("<span style='color: #D29922; font-weight: 700;'>⚠️ LOW CALIBRATION</span>", unsafe_allow_html=True)
    elif cal_score < 90: 
        st.markdown("<span style='color: #D29922; font-weight: 700;'>⚠️ PARTIAL CALIBRATION</span>", unsafe_allow_html=True)
    else: 
        st.markdown("<span style='color: #3FB950; font-weight: 700;'>✅ OPTIMIZED</span>", unsafe_allow_html=True)

    st.divider()
    app_mode = st.radio("MODULES", ["DASHBOARD", "VISUAL COMPLIANCE", "COPY EDITOR", "CONTENT GENERATOR", "BRAND ARCHITECT", "PROFILE MANAGER"])
    st.divider()
    if st.button("SHUT DOWN"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- MODULES ---

# 1. DASHBOARD (The HUD Redesign)
if app_mode == "DASHBOARD":
    st.title("SYSTEM STATUS")
    
    if not active_profile:
        st.warning("NO PROFILES LOADED.")
    else:
        # The Hero Card
        st.markdown(f"""
        <div class="dashboard-card">
            <div style="color: #8B949E; font-size: 0.8rem; letter-spacing: 0.1em; margin-bottom: 5px;">ACTIVE PROFILE</div>
            <div style="font-size: 2.5rem; color: #F0EAD6; font-weight: 800;">{active_profile}</div>
            <div style="color: #D4AF37; margin-top: 5px;">CALIBRATION SCORE: {cal_score}/100</div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("ENGINE CAPABILITIES")
            # Custom HTML Rows (No st.success)
            st.markdown(f"""
            <div class="status-row">
                <span class="status-label">STRATEGY ENGINE</span>
                <span class="status-indicator {'online' if cal_score > 50 else 'offline'}">{'ONLINE' if cal_score > 50 else 'OFFLINE'}</span>
            </div>
            <div class="status-row">
                <span class="status-label">VOICE ENGINE</span>
                <span class="status-indicator {'online' if cal_score > 70 else 'calibrating'}">{'ONLINE' if cal_score > 70 else 'CALIBRATING'}</span>
            </div>
            <div class="status-row">
                <span class="status-label">SOCIAL ENGINE</span>
                <span class="status-indicator {'online' if cal_score > 90 else 'offline'}">{'ONLINE' if cal_score > 90 else 'NO DATA'}</span>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.subheader("REQUIRED ACTIONS")
            if missing_items:
                for item in missing_items: 
                    st.info(f"MISSING DATA: {item}")
            else: 
                st.success("ALL SYSTEMS NOMINAL.")

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
        with st.expander("1. STRATEGY (CORE)", expanded=True):
            wiz_name = st.text_input("BRAND NAME")
            wiz_archetype = st.selectbox("ARCHETYPE *", ARCHETYPES, index=None, placeholder="SELECT...")
            wiz_mission = st.text_area("MISSION")
        with st.expander("2. VOICE & CALIBRATION"):
            st.text_area("PASTE SAMPLE (PRESS ADD)", key="wiz_temp_sample", height=100)
            if st.button("➕ ADD SAMPLE"): add_voice_sample(); st.success("ADDED")
            if st.session_state['wiz_samples_list']: st.caption(f"BUFFER: {len(st.session_state['wiz_samples_list'])}")
        with st.expander("3. SOCIAL MEDIA"):
            wiz_social_file = st.file_uploader("UPLOAD SCREENSHOT", type=["png", "jpg"])
        with st.expander("4. VISUALS"):
            vc1, vc2 = st.columns(2)
            with vc1: p_col = st.color_picker("PRIMARY COLOR")
            with vc2: wiz_logo_file = st.file_uploader("UPLOAD LOGO")
        if st.button("GENERATE SYSTEM", type="primary"):
            if not wiz_name or not wiz_archetype: st.error("NAME/ARCHETYPE REQUIRED")
            else:
                with st.spinner("CALIBRATING..."):
                    logo_desc = logic.describe_logo(Image.open(wiz_logo_file)) if wiz_logo_file else "None"
                    social_desc = logic.analyze_social_post(Image.open(wiz_social_file)) if wiz_social_file else "None"
                    all_samples = "\n".join(st.session_state['wiz_samples_list'])
                    prompt = f"Profile for {wiz_name}. Archetype: {wiz_archetype}. Mission: {wiz_mission}. Samples: {all_samples}. Social: {social_desc}. Logo: {logo_desc}"
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = logic.generate_brand_rules(prompt)
                    st.session_state['wiz_samples_list'] = []
                    st.success("CALIBRATED")
                    st.rerun()
    with tab2:
        pdf = st.file_uploader("UPLOAD PDF", type=["pdf"])
        if pdf and st.button("EXTRACT"):
            st.session_state['profiles'][f"{pdf.name} (PDF)"] = logic.generate_brand_rules(f"Extract: {logic.extract_text_from_pdf(pdf)[:20000]}")
            st.success("EXTRACTED")

# 6. PROFILE MANAGER
elif app_mode == "PROFILE MANAGER":
    st.title("PROFILE MANAGER")
    if st.session_state['profiles']:
        target = st.selectbox("PROFILE", list(st.session_state['profiles'].keys()))
        new_rules = st.text_area("EDIT", st.session_state['profiles'][target], height=400)
        c1, c2, c3 = st.columns(3)
        if c1.button("SAVE"): st.session_state['profiles'][target] = new_rules; st.success("SAVED")
        if c3.button("DELETE"): del st.session_state['profiles'][target]; st.rerun()
