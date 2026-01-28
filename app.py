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

# --- THE CASTELLAN DESIGN SYSTEM (CSS) ---
st.markdown("""
<style>
    /* VARIABLES */
    :root {
        --bg-dark: #0E1117;
        --bg-panel: #161A22;
        --gold: #D4AF37;
        --gold-dim: #8a7020;
        --cream: #F0EAD6;
        --text-main: #E0E0E0;
        --success-bg: rgba(46, 160, 67, 0.2);
        --success-border: #2ea043;
        --error-bg: rgba(218, 54, 51, 0.2);
        --error-border: #f85149;
    }

    /* 1. GLOBAL RESET */
    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-main);
    }
    
    h1, h2, h3, h4, .stMarkdown, p {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        letter-spacing: 0.03em;
    }
    
    h1 { 
        font-weight: 800 !important; 
        text-transform: uppercase; 
        color: var(--cream) !important; 
        font-size: 3rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2, h3 { 
        color: var(--gold) !important; 
        text-transform: uppercase;
        font-weight: 600 !important;
    }
    
    /* 2. THE 'GLOW UP' BUTTONS */
    /* Target the button element directly */
    div.stButton > button {
        background-color: transparent !important;
        color: var(--gold) !important;
        border: 1px solid var(--gold) !important;
        border-radius: 2px !important; /* Sharp but slight soften */
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        box-shadow: 0 0 0 transparent;
    }
    
    /* Hover State */
    div.stButton > button:hover {
        background-color: rgba(212, 175, 55, 0.15) !important;
        color: var(--cream) !important;
        border-color: var(--cream) !important;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.5), inset 0 0 5px rgba(212, 175, 55, 0.2) !important;
        transform: translateY(-2px);
    }
    
    div.stButton > button:active {
        transform: translateY(1px);
    }
    
    /* Primary Action Buttons (Filled Gold) */
    div.stButton > button[kind="primary"] {
        background-color: var(--gold) !important;
        color: #0E1117 !important;
        border: 1px solid var(--gold) !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: var(--cream) !important;
        border-color: var(--cream) !important;
        color: #000 !important;
        box-shadow: 0 0 20px var(--gold) !important;
    }

    /* 3. INPUT FIELD CONTRAST FIX */
    /* Forces lighter background on inputs so they don't disappear */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #1c212c !important; 
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        border-radius: 2px !important;
    }
    
    /* Focus State for Inputs */
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 8px rgba(212, 175, 55, 0.3) !important;
    }
    
    /* 4. DASHBOARD HUD ELEMENTS (Custom HTML) */
    .metric-card {
        background: linear-gradient(180deg, #1c212c 0%, #13171f 100%);
        padding: 24px;
        border: 1px solid #30363d;
        border-left: 5px solid var(--gold);
        border-radius: 4px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .metric-card h4 { color: #8b949e !important; font-size: 0.85rem !important; margin: 0; letter-spacing: 0.15em; font-weight: 600;}
    .metric-card h1 { color: var(--cream) !important; font-size: 2.8rem !important; margin: 10px 0; letter-spacing: 0.05em; }
    .metric-card p { color: #8b949e !important; font-size: 0.9rem; margin: 0; }
    
    /* Custom Status Bars */
    .status-row {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 4px;
        border: 1px solid transparent;
        font-weight: 700;
        letter-spacing: 0.05em;
        font-size: 0.85rem;
        text-transform: uppercase;
    }
    .status-online {
        background-color: var(--success-bg);
        border-color: var(--success-border);
        color: #4cd964;
    }
    .status-offline {
        background-color: var(--error-bg);
        border-color: var(--error-border);
        color: #ff5f56;
    }
    .status-warning {
        background-color: rgba(212, 175, 55, 0.15);
        border-color: var(--gold);
        color: var(--gold);
    }
    
    /* 5. SIDEBAR & LAYOUT */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-panel);
        border-right: 1px solid #30363d;
    }
    
    .stExpander {
        border: 1px solid #30363d !important;
        border-radius: 4px !important;
        background-color: #1c212c !important;
    }
    
    /* 6. CLEANUP */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'check_count' not in st.session_state:
    st.session_state['check_count'] = 0
if 'wiz_temp_sample' not in st.session_state:
    st.session_state['wiz_temp_sample'] = ""
if 'wiz_samples_list' not in st.session_state:
    st.session_state['wiz_samples_list'] = []

if 'profiles' not in st.session_state:
    st.session_state['profiles'] = {
        "Apple (Creator)": """
        1. STRATEGY: Mission: To bring the best user experience... Archetype: The Creator.
        2. VOICE: Innovative, Minimalist. Style Signature: Short sentences. High impact.
        3. VISUALS: Black, White, Grey. Sans-Serif fonts.
        4. DATA DEPTH: High (Social Samples, Press Samples included).
        """
    }

MAX_CHECKS = 50

# --- ARCHETYPES ---
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
    if "Style Signature" in profile_data: 
        score += 25
    else:
        missing.append("Voice Samples")
    if "SOCIAL MEDIA" in profile_data or "Social Style Signature" in profile_data: 
        score += 25
    else:
        missing.append("Social Screenshots")
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
        # LOGO FIX: Centered and constrained width
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", width=160) 
        else:
            st.markdown("<h1 style='text-align: center; color: #D4AF37;'>SIGNET</h1>", unsafe_allow_html=True)
            
        st.markdown("<p style='text-align: center; color: #888; font-size: 0.8rem; letter-spacing: 0.2em;'>RESTRICTED ACCESS // CASTELLAN PR</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        password = st.text_input("ACCESS KEY", type="password", label_visibility="collapsed", placeholder="ENTER ACCESS KEY")
        
        # Spacer
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
    st.markdown("<p style='color: #888; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 5px;'>ENGINE CONFIDENCE</p>", unsafe_allow_html=True)
    st.progress(cal_score / 100)
    
    if cal_score < 60:
        st.markdown("<span style='color: #e3b341; font-size: 0.75rem; font-weight: 600;'>⚠️ LOW CALIBRATION</span>", unsafe_allow_html=True)
    elif cal_score < 90:
        st.markdown("<span style='color: #e3b341; font-size: 0.75rem; font-weight: 600;'>⚠️ PARTIAL CALIBRATION</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color: #4cd964; font-size: 0.75rem; font-weight: 600;'>✅ FULLY OPTIMIZED</span>", unsafe_allow_html=True)

    st.divider()
    
    app_mode = st.radio("MODULE SELECTION", [
        "DASHBOARD", 
        "VISUAL COMPLIANCE", 
        "COPY EDITOR", 
        "CONTENT GENERATOR", 
        "BRAND ARCHITECT",
        "PROFILE MANAGER"
    ])
    
    st.divider()
    if st.button("LOGOUT"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- MODULE 1: DASHBOARD ---
if app_mode == "DASHBOARD":
    st.title("SYSTEM STATUS")
    
    if not active_profile:
        st.warning("NO PROFILES LOADED. NAVIGATE TO BRAND ARCHITECT.")
    else:
        # HUD CARD
        st.markdown(f"""
        <div class="metric-card">
            <h4>ACTIVE BRAND PROFILE</h4>
            <h1>{active_profile}</h1>
            <p>CALIBRATION SCORE: {cal_score}/100</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### CAPABILITIES")
            
            # CUSTOM STATUS BARS (Replaces standard st.success)
            if cal_score > 50: 
                st.markdown('<div class="status-row status-online">Strategy Engine: ONLINE</div>', unsafe_allow_html=True)
            else: 
                st.markdown('<div class="status-row status-offline">Strategy Engine: OFFLINE</div>', unsafe_allow_html=True)
            
            if cal_score > 70: 
                st.markdown('<div class="status-row status-online">Voice Engine: ONLINE</div>', unsafe_allow_html=True)
            else: 
                st.markdown('<div class="status-row status-warning">Voice Engine: CALIBRATING...</div>', unsafe_allow_html=True)
            
            if cal_score > 90: 
                st.markdown('<div class="status-row status-online">Social Engine: ONLINE</div>', unsafe_allow_html=True)
            else: 
                st.markdown('<div class="status-row status-offline">Social Engine: NO DATA</div>', unsafe_allow_html=True)
            
        with c2:
            st.markdown("### REQUIRED ACTIONS")
            if missing_items:
                for item in missing_items:
                    st.info(f"UPLOAD: {item}")
            else:
                st.write("SYSTEM IS FULLY CALIBRATED.")

# --- MODULE 2: VISUAL COMPLIANCE ---
elif app_mode == "VISUAL COMPLIANCE":
    st.title("VISUAL COMPLIANCE AUDIT")
    st.markdown("Upload creative assets to verify brand alignment.")
    
    uploaded_file = st.file_uploader("UPLOAD ASSET", type=["jpg", "png", "jpeg"])
    
    if uploaded_file and st.button("RUN AUDIT", type="primary"):
        image = Image.open(uploaded_file)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(image, caption="ASSET PREVIEW", use_container_width=True)
        with c2:
            with st.spinner("ANALYZING PIXELS..."):
                result = logic.run_visual_audit(image, current_rules)
                st.markdown(result)

# --- MODULE 3: COPY EDITOR ---
elif app_mode == "COPY EDITOR":
    st.title("COPY EDITOR")
    st.markdown("Analyze and rewrite drafts for voice alignment.")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        text_input = st.text_area("DRAFT TEXT", height=300, placeholder="PASTE DRAFT COPY HERE...")
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>TARGET VOICE</h4>
            <h3>{active_profile}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    if text_input and st.button("ANALYZE & REWRITE", type="primary"):
        with st.spinner("EVALUATING SYNTAX AND TONE..."):
            result = logic.run_copy_editor(text_input, current_rules)
            st.markdown(result)

# --- MODULE 4: CONTENT GENERATOR ---
elif app_mode == "CONTENT GENERATOR":
    st.title("CONTENT GENERATOR")
    
    if cal_score < 60:
        st.warning(f"⚠️ LOW CONFIDENCE ({cal_score}%). RESULTS MAY BE GENERIC. UPLOAD VOICE SAMPLES.")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        format_type = st.selectbox("ASSET TYPE", ["Press Release", "Internal Email", "LinkedIn Post", "Article", "Client Letter"])
    with c2:
        topic = st.text_input("TOPIC / HEADLINE", placeholder="E.g. Q4 Earnings Results")
        
    key_points = st.text_area("KEY POINTS / BULLETS", height=200, placeholder="- Record revenue\n- New expansion")
    
    if st.button("GENERATE DRAFT", type="primary"):
        if not key_points or not topic:
            st.error("MISSING INPUTS")
        else:
            with st.spinner(f"DRAFTING {format_type.upper()}..."):
                result = logic.run_content_generator(topic, format_type, key_points, current_rules)
                st.markdown("### GENERATED DRAFT")
                st.markdown(result)

# --- MODULE 5: BRAND ARCHITECT ---
elif app_mode == "BRAND ARCHITECT":
    st.title("BRAND ARCHITECT")
    
    tab1, tab2 = st.tabs(["WIZARD", "PDF EXTRACT"])
    
    with tab1:
        # 1. STRATEGY
        with st.expander("1. STRATEGY (CORE)", expanded=True):
            wiz_name = st.text_input("BRAND NAME")
            wiz_archetype = st.selectbox("ARCHETYPE *", ARCHETYPES, index=None, placeholder="SELECT ARCHETYPE...")
            wiz_mission = st.text_area("MISSION STATEMENT")

        # 2. VOICE
        with st.expander("2. VOICE & CALIBRATION", expanded=True):
            st.info("UPLOAD SAMPLES TO TRAIN THE ENGINE. 5+ SAMPLES RECOMMENDED.")
            
            # Resetting Widget
            st.text_area("PASTE SAMPLE TEXT (PRESS ADD TO SAVE)", key="wiz_temp_sample", height=100)
            if st.button("➕ ADD SAMPLE"):
                add_voice_sample()
                st.success(f"SAMPLE ADDED. BUFFER: {len(st.session_state['wiz_samples_list'])}")
            
            if st.session_state['wiz_samples_list']:
                st.caption(f"READY TO PROCESS {len(st.session_state['wiz_samples_list'])} SAMPLES.")

        # 3. SOCIAL
        with st.expander("3. SOCIAL MEDIA (OPTIMIZATION)", expanded=False):
            st.markdown("Upload screenshots of high-performing posts.")
            wiz_social_file = st.file_uploader("UPLOAD SCREENSHOT", type=["png", "jpg"])

        # 4. VISUALS
        with st.expander("4. VISUALS"):
            vc1, vc2 = st.columns(2)
            with vc1:
                p_col = st.color_picker("PRIMARY COLOR", "#000000")
            with vc2:
                wiz_logo_file = st.file_uploader("UPLOAD LOGO", type=["png", "jpg"])

        if st.button("GENERATE SYSTEM", type="primary"):
            if not wiz_name or not wiz_archetype:
                st.error("NAME AND ARCHETYPE REQUIRED.")
            else:
                with st.spinner("CALIBRATING ENGINE..."):
                    logo_desc = logic.describe_logo(Image.open(wiz_logo_file)) if wiz_logo_file else "None"
                    social_desc = logic.analyze_social_post(Image.open(wiz_social_file)) if wiz_social_file else "None"
                    all_samples = "\n\n".join(st.session_state['wiz_samples_list'])
                    
                    prompt = f"""
                    Create profile for "{wiz_name}".
                    Archetype: {wiz_archetype}
                    Mission: {wiz_mission}
                    Voice Samples: {all_samples}
                    Social Media Analysis: {social_desc}
                    Primary Color: {p_col}
                    Logo: {logo_desc}
                    """
                    rules = logic.generate_brand_rules(prompt)
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = rules
                    st.session_state['wiz_samples_list'] = [] # Clear buffer
                    st.success("PROFILE CREATED & CALIBRATED")
                    st.rerun()

    with tab2:
        pdf = st.file_uploader("UPLOAD PDF GUIDE", type=["pdf"])
        if pdf and st.button("EXTRACT RULES"):
            raw = logic.extract_text_from_pdf(pdf)
            rules = logic.generate_brand_rules(f"Extract rules: {raw[:20000]}")
            st.session_state['profiles'][f"{pdf.name} (PDF)"] = rules
            st.success("EXTRACTED")

# --- MODULE 6: MANAGER ---
elif app_mode == "PROFILE MANAGER":
    st.title("PROFILE MANAGER")
    
    if not active_profile:
        st.warning("NO PROFILES FOUND.")
    else:
        target = st.selectbox("SELECT PROFILE", list(st.session_state['profiles'].keys()))
        current_rules = st.session_state['profiles'][target]
        new_rules = st.text_area("EDIT RULES", current_rules, height=400)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("SAVE CHANGES"):
                st.session_state['profiles'][target] = new_rules
                st.success("SAVED")
        with c2:
            pdf_bytes = logic.create_pdf(target, new_rules)
            st.download_button("DOWNLOAD PDF", pdf_bytes, f"{target}.pdf")
        with c3:
            if st.button("DELETE PROFILE"):
                del st.session_state['profiles'][target]
                st.rerun()
