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
    }

    /* 1. GLOBAL RESET & FONTS */
    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-main);
    }
    
    h1, h2, h3, h4, .stMarkdown, p, div {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        letter-spacing: 0.02em;
    }
    
    h1 { 
        font-weight: 800 !important; 
        text-transform: uppercase; 
        color: var(--cream) !important; 
        font-size: 2.2rem !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 0px 0px 15px rgba(0,0,0,0.5);
    }
    
    h2, h3 { 
        color: var(--gold) !important; 
        text-transform: uppercase;
        font-weight: 600 !important;
    }

    /* 2. THE 'GLOW' BUTTONS (High Specificity) */
    div.stButton > button {
        background-color: transparent !important;
        color: var(--gold) !important;
        border: 1px solid var(--gold) !important;
        border-radius: 2px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        box-shadow: 0 0 0 transparent; 
    }
    
    /* HOVER STATE: The Glow Effect */
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
    
    /* PRIMARY ACTION BUTTONS (Filled Gold) */
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
    /* Forces lighter background on inputs so they don't disappear into the dark mode */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #1c212c !important; 
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        border-radius: 2px !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 8px rgba(212, 175, 55, 0.3) !important;
    }
    
    /* 4. METRIC CARDS (HUD STYLE) */
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
    .metric-card h3 { color: var(--cream) !important; font-size: 1.5rem !important; margin: 10px 0; letter-spacing: 0.05em; }
    
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

# --- LOGIN SCREEN ---
if not st.session_state['authenticated']:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        # LOGO CENTERING
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
    
    st.caption("SYSTEM STATUS: ONLINE")
    st.divider()
    
    app_mode = st.radio("MODULE SELECTION", [
        "VISUAL COMPLIANCE", 
        "COPY EDITOR", 
        "BRAND ARCHITECT",
        "PROFILE MANAGER"
    ])
    
    st.divider()
    if st.button("LOGOUT"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- MODULE 1: VISUAL COMPLIANCE ---
if app_mode == "VISUAL COMPLIANCE":
    st.title("VISUAL COMPLIANCE AUDIT")
    st.markdown("Upload creative assets to verify brand alignment.")
    
    if not st.session_state['profiles']:
        st.warning("NO PROFILES FOUND. PLEASE CREATE ONE.")
    else:
        profile = st.selectbox("ACTIVE PROFILE", list(st.session_state['profiles'].keys()))
        rules = st.session_state['profiles'][profile]
        
        uploaded_file = st.file_uploader("UPLOAD ASSET", type=["jpg", "png", "jpeg"])
        
        if uploaded_file and st.button("RUN AUDIT", type="primary"):
            image = Image.open(uploaded_file)
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(image, caption="ASSET PREVIEW", use_container_width=True)
            with c2:
                with st.spinner("ANALYZING PIXELS..."):
                    result = logic.run_visual_audit(image, rules)
                    st.markdown(result)

# --- MODULE 2: COPY EDITOR ---
elif app_mode == "COPY EDITOR":
    st.title("COPY EDITOR")
    st.markdown("Analyze and rewrite drafts for voice alignment.")
    
    if not st.session_state['profiles']:
        st.warning("NO PROFILES FOUND. PLEASE CREATE ONE.")
    else:
        profile = st.selectbox("ACTIVE PROFILE", list(st.session_state['profiles'].keys()))
        rules = st.session_state['profiles'][profile]
        
        c1, c2 = st.columns([2, 1])
        with c1:
            text_input = st.text_area("DRAFT TEXT", height=300, placeholder="PASTE DRAFT COPY HERE...")
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <h4>TARGET VOICE</h4>
                <h3>{profile}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        if text_input and st.button("ANALYZE & REWRITE", type="primary"):
            with st.spinner("EVALUATING SYNTAX AND TONE..."):
                result = logic.run_copy_editor(text_input, rules)
                st.markdown(result)

# --- MODULE 3: BRAND ARCHITECT ---
elif app_mode == "BRAND ARCHITECT":
    st.title("BRAND ARCHITECT")
    
    tab1, tab2 = st.tabs(["WIZARD", "PDF EXTRACT"])
    
    with tab1:
        # 1. STRATEGY
        with st.expander("1. STRATEGY (CORE)", expanded=True):
            wiz_name = st.text_input("BRAND NAME")
            wiz_archetype = st.selectbox("ARCHETYPE *", ARCHETYPES, index=None, placeholder="SELECT ARCHETYPE...")
            wiz_mission = st.text_area("MISSION STATEMENT")
            wiz_values = st.text_area("CORE VALUES")

        # 2. VOICE
        with st.expander("2. VOICE & CALIBRATION", expanded=True):
            wiz_tone_adjectives = st.text_input("TONE KEYWORDS", placeholder="Professional, Direct")
            wiz_voice_dos = st.text_area("DO'S & DON'TS")
            
            st.markdown("---")
            st.markdown("**GHOST-WRITER CALIBRATION**")
            st.caption("Paste 'Gold Standard' copy to calibrate Tone and Cadence.")
            wiz_voice_samples = st.text_area("REFERENCE CONTENT", height=150)

        # 3. VISUALS
        with st.expander("3. VISUALS"):
            vc1, vc2 = st.columns(2)
            with vc1:
                p_col1_name = st.text_input("PRIMARY COLOR NAME", "Brand Blue")
                p_col1_hex = st.color_picker("HEX CODE", "#0000FF")
            with vc2:
                s_col_list = st.text_area("SECONDARY PALETTE", placeholder="#EAA792, #618DAE")
            
            st.markdown("**TYPOGRAPHY**")
            tc1, tc2 = st.columns(2)
            with tc1:
                head_fam = st.selectbox("HEADLINE STYLE", ["Sans-Serif", "Serif", "Slab Serif", "Script", "Display"])
                head_name = st.text_input("FONT NAME", placeholder="Montserrat")
            with tc2:
                body_fam = st.selectbox("BODY STYLE", ["Sans-Serif", "Serif", "Monospace"])
                body_name = st.text_input("BODY FONT NAME", placeholder="Open Sans")

            st.markdown("**LOGO**")
            lc1, lc2 = st.columns(2)
            with lc1:
                wiz_logo_file = st.file_uploader("UPLOAD LOGO", type=["png", "jpg"])
            with lc2:
                wiz_logo_desc = st.text_input("OR DESCRIBE LOGO", placeholder="Blue shield icon...")

        if st.button("GENERATE SYSTEM", type="primary"):
            if not wiz_name or not wiz_archetype:
                st.error("NAME AND ARCHETYPE REQUIRED.")
            else:
                with st.spinner("CALIBRATING ENGINE..."):
                    logo_desc = wiz_logo_desc
                    if wiz_logo_file and not wiz_logo_desc:
                        img = Image.open(wiz_logo_file)
                        logo_desc = logic.describe_logo(img)
                        st.info(f"AI DETECTED LOGO: {logo_desc}")

                    prompt = f"""
                    Create profile for "{wiz_name}".
                    Archetype: {wiz_archetype}
                    Mission: {wiz_mission}
                    Values: {wiz_values}
                    Voice Samples: {wiz_voice_samples}
                    Tone: {wiz_tone_adjectives}
                    Primary Color: {p_col1_name} ({p_col1_hex})
                    Secondary Colors: {s_col_list}
                    Fonts: {head_name} / {body_name}
                    Logo: {logo_desc}
                    """
                    rules = logic.generate_brand_rules(prompt)
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = rules
                    st.success("PROFILE CREATED & CALIBRATED")
                    st.rerun()

    with tab2:
        pdf = st.file_uploader("UPLOAD PDF GUIDE", type=["pdf"])
        if pdf and st.button("EXTRACT RULES"):
            raw = logic.extract_text_from_pdf(pdf)
            rules = logic.generate_brand_rules(f"Extract rules: {raw[:20000]}")
            st.session_state['profiles'][f"{pdf.name} (PDF)"] = rules
            st.success("EXTRACTED")

# --- MODULE 4: MANAGER ---
elif app_mode == "PROFILE MANAGER":
    st.title("PROFILE MANAGER")
    
    if not st.session_state['profiles']:
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
