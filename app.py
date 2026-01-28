import streamlit as st
from PIL import Image
import os
from logic import SignetLogic

# --- PAGE CONFIG ---
# Using the uploaded icon file if available, otherwise a generic fallback
icon_path = "Signet_Icon_Color.png"
page_icon = Image.open(icon_path) if os.path.exists(icon_path) else "🛡️"

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
        border-radius: 4px !important;
        margin-bottom: 8px !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    div[role="radiogroup"] label:hover {
        background-color: rgba(171, 143, 89, 0.1) !important;
        border-left: 4px solid var(--c-gold-muted) !important;
        padding-left: 16px !important;
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: var(--c-teal-deep) !important;
        color: var(--c-cream) !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div[role="radiogroup"] label[data-checked="true"] * { color: var(--c-cream) !important; }

    /* 4. HEADERS */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800 !important;
        text-transform: uppercase;
        color: var(--c-cream) !important;
        padding-bottom: 15px;
        border-bottom: 2px solid var(--c-gold-muted);
        letter-spacing: 0.05em;
    }
    
    h2, h3 { color: var(--c-gold-muted) !important; text-transform: uppercase; font-weight: 700; }

    /* 5. INPUTS (Teal on Teal) */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: var(--c-teal-dark) !important;
        border: 1px solid var(--c-sage) !important;
        color: var(--c-cream) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--c-gold-muted) !important;
        box-shadow: 0 0 5px rgba(171, 143, 89, 0.5) !important;
    }

    /* 6. BUTTONS */
    .stButton button {
        background-color: transparent !important;
        border: 1px solid var(--c-gold-muted) !important;
        color: var(--c-gold-muted) !important;
        border-radius: 0px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: var(--c-gold-muted) !important;
        color: var(--c-teal-deep) !important;
        box-shadow: 0 0 15px rgba(171, 143, 89, 0.3);
    }
    button[kind="primary"] {
        background: var(--c-gold-muted) !important;
        color: var(--c-teal-deep) !important;
        border: none !important;
    }

    /* 7. DASHBOARD CARDS & HERO */
    .dashboard-card {
        background-color: rgba(0,0,0,0.2);
        border: 1px solid var(--c-sage);
        border-left: 4px solid var(--c-gold-muted);
        padding: 25px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .hero-card {
        background: linear-gradient(135deg, var(--c-teal-dark) 0%, #111 100%);
        border: 1px solid var(--c-gold-muted);
        padding: 30px;
        text-align: center;
        border-radius: 8px;
        margin: 10px;
        transition: transform 0.2s;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .hero-card:hover { transform: translateY(-5px); border-color: var(--c-sage); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
    .hero-icon { font-size: 3rem; margin-bottom: 10px; }
    .hero-title { font-weight: 800; color: var(--c-gold-muted); font-size: 1.2rem; text-transform: uppercase; }
    .hero-desc { color: #a0a0a0; font-size: 0.9rem; margin-bottom: 15px; }

    .status-row {
        background: rgba(0,0,0,0.3);
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid transparent;
    }
    .status-row.online { border-color: var(--c-sage); }
    .status-row.offline { border-color: #8a3a3a; }
    
    .status-label { font-weight: 700; font-size: 0.9rem; letter-spacing: 0.1em; color: var(--c-cream); }
    .status-badge { font-family: monospace; font-weight: 700; color: var(--c-gold-muted); }

    /* 8. CLEANUP */
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

# START EMPTY - No profiles by default to trigger the Onboarding View
if 'profiles' not in st.session_state:
    st.session_state['profiles'] = {}

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
        # Use Real Logo if available
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", width=300)
        elif os.path.exists("Signet_Icon_Color.png"):
            st.image("Signet_Icon_Color.png", width=150) 
        else:
            st.markdown("<div style='text-align: center; font-size: 3rem; color: #ab8f59; font-weight: 800; letter-spacing: 0.1em;'>SIGNET</div>", unsafe_allow_html=True)
        
        st.markdown("<div style='text-align: center; color: #f5f5f0; font-size: 0.8rem; letter-spacing: 0.2em; opacity: 0.7; margin-top: 10px; margin-bottom: 20px;'>INTELLIGENT BRAND GOVERNANCE</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #5c6b61;'>", unsafe_allow_html=True)
        
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
    # Sidebar uses the Icon + Text if available, or just text
    if os.path.exists("Signet_Logo_Color.png"):
        st.image("Signet_Logo_Color.png", use_container_width=True)
    else:
        st.markdown('<div style="font-size: 2rem; color: #24363b; font-weight: 900; letter-spacing: 0.1em; text-align: center;">SIGNET</div>', unsafe_allow_html=True)
    
    st.divider()

    # Profile Selector Logic
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
        st.info("No profiles loaded.")

    st.divider()
    app_mode = st.radio("MODULES", ["DASHBOARD", "VISUAL COMPLIANCE", "COPY EDITOR", "CONTENT GENERATOR", "BRAND ARCHITECT", "PROFILE MANAGER"], label_visibility="collapsed")
    
    st.divider()
    if st.button("SHUT DOWN"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- MODULES ---

# 1. DASHBOARD (The Command Center)
if app_mode == "DASHBOARD":
    
    # HERO SECTION (Empty State Handling)
    if not active_profile:
        st.title("WELCOME TO SIGNET")
        st.markdown("""<p style='font-size: 1.2rem; color: #a0a0a0; margin-bottom: 40px;'>Initialize a brand profile to begin governance operations.</p>""", unsafe_allow_html=True)
        
        # 3-Column Quick Start
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div class="hero-card">
                <div class="hero-icon">🏗️</div>
                <div class="hero-title">Create Profile</div>
                <div class="hero-desc">Build a new brand identity from scratch using the Architect Wizard.</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="hero-card">
                <div class="hero-icon">📄</div>
                <div class="hero-title">Upload Guide</div>
                <div class="hero-desc">Extract rules and assets from an existing PDF Brand Guide.</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
            <div class="hero-card">
                <div class="hero-icon">⚙️</div>
                <div class="hero-title">Load Demo</div>
                <div class="hero-desc">Load the Castellan PR sample data for demonstration.</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Hidden Button to trigger Demo Load
        if st.button("LOAD DEMO DATA"):
            st.session_state['profiles']["Castellan PR (Demo)"] = """
            1. STRATEGY: Mission: Architecting Strategic Narratives... Archetype: The Ruler.
            2. VOICE: Professional, Authoritative, Direct. Style Signature: Concise.
            3. VISUALS: Deep Teal, Muted Gold, Cream.
            4. DATA DEPTH: High.
            """
            st.rerun()

        st.info("👉 To begin, select **BRAND ARCHITECT** from the sidebar.")

    else:
        # ACTIVE STATE HUD
        st.title("SYSTEM STATUS")
        
        # HUD Card
        st.markdown(f"""
        <div class="dashboard-card">
            <div style="color: #a0a0a0; font-size: 0.8rem; letter-spacing: 0.1em; margin-bottom: 5px;">ACTIVE PROFILE</div>
            <div style="font-size: 2.5rem; color: #f5f5f0; font-weight: 800;">{active_profile}</div>
            <div style="color: #ab8f59; margin-top: 5px; font-weight: 700;">CALIBRATION SCORE: {cal_score}/100</div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("ENGINE CAPABILITIES")
            st.markdown(f"""
            <div class="status-row {'online' if cal_score > 50 else 'offline'}">
                <span class="status-label">STRATEGY ENGINE</span>
                <span class="status-badge">{'ONLINE' if cal_score > 50 else 'OFFLINE'}</span>
            </div>
            <div class="status-row {'online' if cal_score > 70 else 'offline'}">
                <span class="status-label">VOICE ENGINE</span>
                <span class="status-badge">{'ONLINE' if cal_score > 70 else 'CALIBRATING'}</span>
            </div>
            <div class="status-row {'online' if cal_score > 90 else 'offline'}">
                <span class="status-label">SOCIAL ENGINE</span>
                <span class="status-badge">{'ONLINE' if cal_score > 90 else 'NO DATA'}</span>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.subheader("REQUIRED ACTIONS")
            if missing_items:
                for item in missing_items: 
                    st.markdown(f"""
                    <div style="background: rgba(171, 143, 89, 0.1); border: 1px solid #ab8f59; color: #ab8f59; padding: 12px; border-radius: 4px; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="font-size: 1.2rem; margin-right: 10px;">⚠️</span>
                        <div>
                            <div style="font-weight: 700; font-size: 0.9rem;">MISSING: {item}</div>
                            <div style="font-size: 0.75rem; opacity: 0.8;">Go to Brand Architect to upload.</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
            else: 
                st.markdown("""<div style="background: rgba(92, 107, 97, 0.2); border: 1px solid #5c6b61; color: #f5f5f0; padding: 12px; border-radius: 4px;">✅ ALL SYSTEMS NOMINAL</div>""", unsafe_allow_html=True)

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
