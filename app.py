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

# --- THE CASTELLAN DESIGN SYSTEM (Sarah's Spec) ---
st.markdown("""
<style>
    /* VARIABLES */
    :root {
        --bg-dark: #0E1117;
        --bg-panel: #161A22;
        --gold: #D4AF37;
        --cream: #F0EAD6;
        --text-main: #E0E0E0;
    }

    /* 1. GLOBAL */
    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-main);
    }
    
    h1, h2, h3, h4, .stMarkdown, p, div {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        letter-spacing: 0.02em;
    }
    
    /* Cream Headers (Sarah's contrast fix) */
    h1 { 
        font-weight: 800 !important; 
        text-transform: uppercase; 
        color: var(--cream) !important; 
        font-size: 2.5rem !important;
        text-shadow: 0px 0px 15px rgba(0,0,0,0.5);
    }
    
    h2, h3 { 
        color: var(--gold) !important; 
        text-transform: uppercase;
        font-weight: 600 !important;
    }

    /* 2. GLOW BUTTONS (Robust Selector) */
    .stButton button {
        background-color: transparent !important;
        color: var(--gold) !important;
        border: 1px solid var(--gold) !important;
        border-radius: 2px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 0 transparent; 
    }
    
    .stButton button:hover {
        background-color: rgba(212, 175, 55, 0.15) !important;
        color: var(--cream) !important;
        border-color: var(--cream) !important;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.5), inset 0 0 5px rgba(212, 175, 55, 0.2) !important;
        transform: translateY(-2px);
    }
    
    /* Primary Action Buttons */
    button[kind="primary"] {
        background-color: var(--gold) !important;
        color: #0E1117 !important;
        border: 1px solid var(--gold) !important;
    }

    /* 3. INPUTS (Contrast Fix - Targeting the Container) */
    /* This makes the input box visible against the dark background */
    div[data-baseweb="input"] {
        background-color: #1c212c !important;
        border: 1px solid #444 !important;
        border-radius: 2px !important; 
    }
    div[data-baseweb="input"] > div {
        background-color: transparent !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1c212c !important;
        border: 1px solid #444 !important;
        color: #FFFFFF !important;
    }
    
    /* 4. DASHBOARD HUD (Marcus's Requirement) */
    .metric-card {
        background: linear-gradient(180deg, #1c212c 0%, #13171f 100%);
        padding: 24px;
        border-left: 5px solid var(--gold);
        border-radius: 4px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .metric-card h4 { color: #8b949e !important; font-size: 0.85rem !important; margin: 0; letter-spacing: 0.15em; font-weight: 600;}
    .metric-card h3 { color: var(--cream) !important; font-size: 1.5rem !important; margin: 10px 0; letter-spacing: 0.05em; }

    /* Custom Status Bars (Replacing the blocky green alerts) */
    .status-bar {
        padding: 10px; border-radius: 4px; margin-bottom: 5px; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;
    }
    .status-online { background: rgba(46, 160, 67, 0.2); color: #4cd964; border: 1px solid #2ea043; }
    .status-warn { background: rgba(212, 175, 55, 0.15); color: var(--gold); border: 1px solid #D4AF37; }
    .status-offline { background: rgba(218, 54, 51, 0.2); color: #ff5f56; border: 1px solid #f85149; }
    
    /* 5. SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-panel);
        border-right: 1px solid #30363d;
    }
    
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
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", width=160) 
        else:
            st.markdown("<h1 style='text-align: center; color: #D4AF37;'>SIGNET</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888; font-size: 0.8rem; letter-spacing: 0.2em;'>RESTRICTED ACCESS // CASTELLAN PR</p>", unsafe_allow_html=True)
        st.markdown("---")
        password = st.text_input("ACCESS KEY", type="password", label_visibility="collapsed", placeholder="ENTER ACCESS KEY")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("AUTHENTICATE SYSTEM"):
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
        st.header("SIGNET")
    
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
    
    if cal_score < 60: st.markdown("<span style='color: #e3b341; font-size: 0.75rem; font-weight: 600;'>⚠️ LOW CALIBRATION</span>", unsafe_allow_html=True)
    elif cal_score < 90: st.markdown("<span style='color: #e3b341; font-size: 0.75rem; font-weight: 600;'>⚠️ PARTIAL CALIBRATION</span>", unsafe_allow_html=True)
    else: st.markdown("<span style='color: #4cd964; font-size: 0.75rem; font-weight: 600;'>✅ FULLY OPTIMIZED</span>", unsafe_allow_html=True)

    st.divider()
    app_mode = st.radio("MODULE SELECTION", ["DASHBOARD", "VISUAL COMPLIANCE", "COPY EDITOR", "CONTENT GENERATOR", "BRAND ARCHITECT", "PROFILE MANAGER"])
    st.divider()
    if st.button("LOGOUT"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- MODULES ---

if app_mode == "DASHBOARD":
    st.title("SYSTEM STATUS")
    if not active_profile:
        st.warning("NO PROFILES LOADED.")
    else:
        st.markdown(f"""<div class="metric-card"><h4>ACTIVE BRAND PROFILE</h4><h3>{active_profile}</h3></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### CAPABILITIES")
            st.markdown(f'<div class="status-bar {"status-online" if cal_score > 50 else "status-offline"}">STRATEGY ENGINE: {"ONLINE" if cal_score > 50 else "OFFLINE"}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="status-bar {"status-online" if cal_score > 70 else "status-warn"}">VOICE ENGINE: {"ONLINE" if cal_score > 70 else "CALIBRATING"}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="status-bar {"status-online" if cal_score > 90 else "status-offline"}">SOCIAL ENGINE: {"ONLINE" if cal_score > 90 else "NO DATA"}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown("### ACTIONS")
            if missing_items:
                for item in missing_items: st.info(f"UPLOAD: {item}")
            else: st.write("SYSTEM OPTIMIZED.")

elif app_mode == "VISUAL COMPLIANCE":
    st.title("VISUAL COMPLIANCE AUDIT")
    if not active_profile: st.warning("NO PROFILE SELECTED.")
    else:
        uploaded_file = st.file_uploader("UPLOAD ASSET", type=["jpg", "png"])
        if uploaded_file and st.button("RUN AUDIT", type="primary"):
            with st.spinner("ANALYZING PIXELS..."):
                result = logic.run_visual_audit(Image.open(uploaded_file), current_rules)
                st.markdown(result)

elif app_mode == "COPY EDITOR":
    st.title("COPY EDITOR")
    if not active_profile: st.warning("NO PROFILE SELECTED.")
    else:
        c1, c2 = st.columns([2, 1])
        with c1: text_input = st.text_area("DRAFT TEXT", height=300)
        with c2: st.markdown(f"""<div class="metric-card"><h4>TARGET</h4><h3>{active_profile}</h3></div>""", unsafe_allow_html=True)
        if text_input and st.button("ANALYZE & REWRITE", type="primary"):
            with st.spinner("REWRITING..."):
                result = logic.run_copy_editor(text_input, current_rules)
                st.markdown(result)

elif app_mode == "CONTENT GENERATOR":
    st.title("CONTENT GENERATOR")
    if cal_score < 60: st.warning(f"⚠️ LOW CONFIDENCE ({cal_score}%).")
    c1, c2 = st.columns(2)
    with c1: format_type = st.selectbox("TYPE", ["Press Release", "Email", "LinkedIn Post", "Article"])
    with c2: topic = st.text_input("TOPIC")
    key_points = st.text_area("KEY POINTS", height=150)
    if st.button("GENERATE DRAFT", type="primary"):
        with st.spinner("DRAFTING..."):
            result = logic.run_content_generator(topic, format_type, key_points, current_rules)
            st.markdown(result)

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

elif app_mode == "PROFILE MANAGER":
    st.title("PROFILE MANAGER")
    if st.session_state['profiles']:
        target = st.selectbox("PROFILE", list(st.session_state['profiles'].keys()))
        new_rules = st.text_area("EDIT", st.session_state['profiles'][target], height=400)
        c1, c2, c3 = st.columns(3)
        if c1.button("SAVE"): st.session_state['profiles'][target] = new_rules; st.success("SAVED")
        if c3.button("DELETE"): del st.session_state['profiles'][target]; st.rerun()
