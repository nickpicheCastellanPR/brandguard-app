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

# --- THE "NUCLEAR" CSS (FORCES THE LOOK) ---
st.markdown("""
<style>
    /* FORCE DARK THEME BACKGROUNDS */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #161a22;
        border-right: 1px solid #333;
    }
    
    /* SIGNET BUTTONS (The Gold Standard) */
    div.stButton > button {
        background-color: #1E1E1E !important;
        color: #D4AF37 !important; /* Gold Text */
        border: 1px solid #D4AF37 !important;
        border-radius: 0px !important; /* Sharp Edges */
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.15em !important;
        padding: 0.6rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background-color: #D4AF37 !important;
        color: #000000 !important;
        border-color: #D4AF37 !important;
    }
    
    /* PRIMARY BUTTONS (Generate, Audit) */
    div.stButton > button[kind="primary"] {
        background-color: #D4AF37 !important;
        color: #000000 !important;
        border: none !important;
    }
    
    /* HEADERS */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #E0E0E0 !important;
    }
    
    /* DASHBOARD CARDS */
    .metric-card {
        background: linear-gradient(145deg, #1a1a1a, #222);
        padding: 25px;
        border-left: 4px solid #D4AF37;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }
    .metric-card h3 { color: #888; font-size: 0.8rem !important; margin-bottom: 5px; }
    .metric-card h1 { color: #fff; font-size: 2.5rem !important; margin: 0; }
    .metric-card p { color: #aaa; font-size: 0.9rem; margin-top: 10px; }

    /* EXPANDER STYLING */
    div[data-testid="stExpander"] {
        background-color: #161a22 !important;
        border: 1px solid #333 !important;
        border-radius: 4px !important;
    }
    div[data-testid="stExpander"] p {
        font-weight: 600;
        color: #ccc;
    }

    /* INPUT FIELDS */
    div[data-baseweb="input"] {
        background-color: #0E1117 !important;
        border: 1px solid #444 !important;
        border-radius: 0px !important;
        color: white !important;
    }
    
    /* REMOVE BLOAT */
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
    "The Ruler: Control, leadership, responsibility (e.g., Mercedes-Benz, Rolex)",
    "The Creator: Innovation, imagination, expression (e.g., Apple, Lego)",
    "The Sage: Wisdom, truth, expertise (e.g., Google, BBC, MIT)",
    "The Innocent: Optimism, safety, simplicity (e.g., Dove, Coca-Cola)",
    "The Outlaw: Disruption, liberation, rebellion (e.g., Harley-Davidson, Virgin)",
    "The Magician: Transformation, vision, wonder (e.g., Disney, Dyson)",
    "The Hero: Mastery, action, courage (e.g., Nike, FedEx)",
    "The Lover: Intimacy, connection, indulgence (e.g., Victoria's Secret, Chanel)",
    "The Jester: Humor, play, enjoyment (e.g., Old Spice, M&Ms)",
    "The Everyman: Belonging, connection, down-to-earth (e.g., IKEA, Target)",
    "The Caregiver: Service, nurturing, protection (e.g., Johnson & Johnson, Volvo)",
    "The Explorer: Freedom, discovery, authenticity (e.g., Jeep, Patagonia)"
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

# --- LOGIN ---
if not st.session_state['authenticated']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", use_container_width=True)
        else:
            st.title("SIGNET")
        st.write("Authorized Access Only.")
        password = st.text_input("Access Code", type="password")
        if st.button("Enter System"):
            if logic.check_password(password):
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Access Denied.")
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
    
    st.caption("ENGINE CONFIDENCE")
    st.progress(cal_score / 100)
    if cal_score < 80:
        st.caption(f"⚠️ Low. Add: {', '.join(missing_items[:1])}")
    else:
        st.caption("✅ Optimized")

    st.divider()
    app_mode = st.radio("MODULES", [
        "Dashboard", 
        "Visual Compliance", 
        "Copy Editor", 
        "Content Generator", 
        "Brand Architect",
        "Profile Manager"
    ])
    st.divider()
    if st.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- DASHBOARD ---
if app_mode == "Dashboard":
    st.title("SYSTEM READINESS")
    
    if not active_profile:
        st.warning("No profiles found. Go to Brand Architect.")
    else:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🛡️ ACTIVE PROFILE: {active_profile}</h3>
            <h1>{cal_score}/100 CALIBRATION</h1>
            <p>Signet capability score based on ingested data points.</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("CAPABILITIES")
            if cal_score > 50: st.success("Strategy Engine: ONLINE")
            else: st.error("Strategy Engine: OFFLINE")
            
            if cal_score > 70: st.success("Voice Engine: ONLINE")
            else: st.warning("Voice Engine: CALIBRATING...")
            
            if cal_score > 90: st.success("Social Engine: ONLINE")
            else: st.error("Social Engine: NO DATA")
            
        with c2:
            st.subheader("RECOMMENDED ACTIONS")
            if missing_items:
                for item in missing_items:
                    st.info(f"UPLOAD: **{item}**")
            else:
                st.write("System is fully calibrated.")

# --- VISUAL COMPLIANCE ---
elif app_mode == "Visual Compliance":
    st.subheader("VISUAL COMPLIANCE AUDIT")
    uploaded_file = st.file_uploader("Upload Asset", type=["jpg", "png", "jpeg"])
    
    if uploaded_file and st.button("RUN AUDIT", type="primary"):
        image = Image.open(uploaded_file)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(image, caption="Asset Preview", use_container_width=True)
        with c2:
            with st.spinner("Analyzing pixels..."):
                result = logic.run_visual_audit(image, current_rules)
                st.markdown(result)

# --- COPY EDITOR ---
elif app_mode == "Copy Editor":
    st.subheader("COPY EDITOR & SCORING")
    text_input = st.text_area("Draft Text", height=300)
    
    if text_input and st.button("ANALYZE & SCORE", type="primary"):
        with st.spinner("Evaluating syntax and tone..."):
            result = logic.run_copy_editor(text_input, current_rules)
            st.markdown(result)

# --- CONTENT GENERATOR ---
elif app_mode == "Content Generator":
    st.subheader("CONTENT GENERATOR")
    
    if cal_score < 60:
        st.warning(f"⚠️ Confidence Low ({cal_score}%). Output may be generic.")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        format_type = st.selectbox("Asset Type", ["Press Release", "Email", "LinkedIn Post", "Article"])
    with c2:
        topic = st.text_input("Topic", placeholder="e.g. Q4 Earnings")
        
    key_points = st.text_area("Key Points", height=150)
    
    if st.button("GENERATE DRAFT", type="primary"):
        with st.spinner(f"Drafting {format_type}..."):
            result = logic.run_content_generator(topic, format_type, key_points, current_rules)
            st.markdown(result)

# --- BRAND ARCHITECT ---
elif app_mode == "Brand Architect":
    st.subheader("BRAND ARCHITECT")
    tab1, tab2 = st.tabs(["WIZARD", "PDF EXTRACT"])
    
    with tab1:
        with st.expander("1. STRATEGY", expanded=True):
            wiz_name = st.text_input("Brand Name")
            wiz_archetype = st.selectbox("Archetype *", ARCHETYPES, index=None, placeholder="Select...")
            wiz_mission = st.text_area("Mission Statement")

        with st.expander("2. VOICE & CALIBRATION", expanded=True):
            st.info("Upload samples to train the engine.")
            st.text_area("Paste Text Sample (Press Add to save & clear)", key="wiz_temp_sample", height=100)
            if st.button("➕ ADD SAMPLE"):
                add_voice_sample()
                st.success(f"Sample added! Buffer: {len(st.session_state['wiz_samples_list'])}")
            
            if st.session_state['wiz_samples_list']:
                st.caption(f"Ready to process {len(st.session_state['wiz_samples_list'])} samples.")

        with st.expander("3. SOCIAL MEDIA (NEW)", expanded=False):
            st.write("Upload high-performing post screenshots.")
            wiz_social_file = st.file_uploader("Upload Screenshot", type=["png", "jpg"])

        with st.expander("4. VISUALS"):
            vc1, vc2 = st.columns(2)
            with vc1:
                p_col = st.color_picker("Primary Color", "#000000")
            with vc2:
                wiz_logo_file = st.file_uploader("Upload Logo", type=["png", "jpg"])

        if st.button("GENERATE SYSTEM", type="primary"):
            if not wiz_name or not wiz_archetype:
                st.error("Name and Archetype required.")
            else:
                with st.spinner("Calibrating Engine..."):
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
                    st.session_state['wiz_samples_list'] = []
                    st.success("Profile Created & Calibrated!")
                    st.rerun()

    with tab2:
        pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf and st.button("EXTRACT"):
            raw = logic.extract_text_from_pdf(pdf)
            rules = logic.generate_brand_rules(f"Extract rules: {raw[:20000]}")
            st.session_state['profiles'][f"{pdf.name} (PDF)"] = rules
            st.success("Extracted!")

# --- MANAGER ---
elif app_mode == "Profile Manager":
    st.subheader("PROFILE MANAGER")
    if not active_profile:
        st.warning("No profiles found.")
    else:
        target = st.selectbox("Select Profile", list(st.session_state['profiles'].keys()))
        current_rules = st.session_state['profiles'][target]
        new_rules = st.text_area("Edit Rules", current_rules, height=400)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("SAVE CHANGES"):
                st.session_state['profiles'][target] = new_rules
                st.success("Saved!")
        with c2:
            pdf_bytes = logic.create_pdf(target, new_rules)
            st.download_button("DOWNLOAD PDF", pdf_bytes, f"{target}.pdf")
        with c3:
            if st.button("DELETE PROFILE"):
                del st.session_state['profiles'][target]
                st.rerun()
