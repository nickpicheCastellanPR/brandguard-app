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

# --- CUSTOM CSS (RESTORED POLISH) ---
st.markdown("""
<style>
    /* Global Cleanliness */
    .block-container {padding-top: 2rem;}
    
    /* Signet Buttons: Uppercase, Bold, Clean */
    .stButton>button {
        width: 100%; 
        border-radius: 4px; 
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 0.5rem 1rem;
    }
    
    /* Expander Headers: Clean, Grey */
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: 600;
        color: #A0A0A0;
    }
    
    /* Clean Alert Styling */
    .stAlert {
        border-radius: 4px; 
        border-left: 5px solid #D4AF37; /* Gold Accent */
    }
    
    /* Dashboard Metric Cards */
    .metric-card {
        background-color: #1E1E1E;
        padding: 24px;
        border-radius: 8px;
        border-left: 4px solid #D4AF37; /* Gold Accent */
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .metric-card h3 {
        color: #888;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0;
    }
    .metric-card h1 {
        color: #FFF;
        font-size: 2.5rem;
        margin: 10px 0;
    }
    .metric-card p {
        color: #CCC;
        font-size: 0.9rem;
    }

    /* Remove Streamlit Branding */
    .reportview-container { margin-top: -2em; }
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
# Initialize the wizard temp text if not exists
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

# --- ARCHETYPE DEFINITIONS ---
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
    """Deterministically calculates how 'ready' the engine is."""
    score = 0
    missing = []
    
    # Check for core elements (Basic 50%)
    if "STRATEGY" in profile_data: score += 10
    if "VOICE" in profile_data: score += 10
    if "VISUALS" in profile_data: score += 10
    if "LOGO RULES" in profile_data: score += 10
    if "TYPOGRAPHY" in profile_data: score += 10
    
    # Check for Advanced calibration (The other 50%)
    if "Style Signature" in profile_data: 
        score += 25
    else:
        missing.append("Text Samples (Voice Calibration)")
        
    if "SOCIAL MEDIA" in profile_data or "Social Style Signature" in profile_data: 
        score += 25
    else:
        missing.append("Social Media Screenshots")
        
    return score, missing

def add_voice_sample():
    """Callback to add sample and clear box"""
    if st.session_state.wiz_temp_sample:
        st.session_state['wiz_samples_list'].append(st.session_state.wiz_temp_sample)
        st.session_state.wiz_temp_sample = "" # Clear the input

# --- LOGIN SCREEN ---
if not st.session_state['authenticated']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", width=300)
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

# --- MAIN SIDEBAR ---
with st.sidebar:
    if os.path.exists("Signet_Logo_Color.png"):
        st.image("Signet_Logo_Color.png", use_container_width=True)
    else:
        st.header("SIGNET")
    
    # Calculate Active Score
    if st.session_state['profiles']:
        active_profile = st.selectbox("ACTIVE PROFILE", list(st.session_state['profiles'].keys()))
        current_rules = st.session_state['profiles'][active_profile]
        cal_score, missing_items = calculate_calibration_score(current_rules)
    else:
        active_profile = None
        cal_score = 0
    
    # Sidebar Metrics
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

# --- MODULE 1: DASHBOARD (The "Readiness" Center) ---
if app_mode == "Dashboard":
    st.title("System Readiness")
    
    if not active_profile:
        st.warning("No profiles found. Go to Brand Architect.")
    else:
        # Score Card
        st.markdown(f"""
        <div class="metric-card">
            <h3>🛡️ {active_profile}</h3>
            <h1>{cal_score}/100 Calibration Score</h1>
            <p>This score represents Signet's ability to accurately mimic this brand.</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("✅ Capabilities")
            if cal_score > 50: st.success("Basic Strategy Defined")
            if cal_score > 70: st.success("Voice Signature Calibrated")
            if cal_score > 90: st.success("Social Media Optimized")
            if cal_score < 50: st.warning("Profile Incomplete")
            
        with c2:
            st.subheader("🔧 Recommended Actions")
            if missing_items:
                for item in missing_items:
                    st.info(f"Upload **{item}** to improve confidence.")
            else:
                st.write("System is fully calibrated.")

# --- MODULE 2: VISUAL COMPLIANCE ---
elif app_mode == "Visual Compliance":
    st.subheader("Visual Compliance Audit")
    uploaded_file = st.file_uploader("Upload Asset", type=["jpg", "png", "jpeg"])
    
    if uploaded_file and st.button("Calculate Alignment Score", type="primary"):
        image = Image.open(uploaded_file)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(image, caption="Asset Preview", use_container_width=True)
        with c2:
            with st.spinner("Calculating Signet Score..."):
                result = logic.run_visual_audit(image, current_rules)
                st.markdown(result)

# --- MODULE 3: COPY EDITOR ---
elif app_mode == "Copy Editor":
    st.subheader("Copy Editor & Alignment Scoring")
    text_input = st.text_area("Draft Text", height=300)
    
    if text_input and st.button("Analyze & Score", type="primary"):
        with st.spinner("Calculating Signet Score..."):
            result = logic.run_copy_editor(text_input, current_rules)
            st.markdown(result)

# --- MODULE 4: CONTENT GENERATOR ---
elif app_mode == "Content Generator":
    st.subheader("Content Generator")
    
    # Confidence Warning
    if cal_score < 60:
        st.warning(f"⚠️ Engine Confidence is {cal_score}%. Result may be generic. Improve calibration in 'Brand Architect'.")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        format_type = st.selectbox("Asset Type", ["Press Release", "Email", "LinkedIn Post", "Article"])
    with c2:
        topic = st.text_input("Topic", placeholder="e.g. Q4 Earnings")
        
    key_points = st.text_area("Key Points", height=150)
    
    if st.button("Generate Draft", type="primary"):
        with st.spinner(f"Drafting {format_type}..."):
            result = logic.run_content_generator(topic, format_type, key_points, current_rules)
            st.markdown(result)

# --- MODULE 5: BRAND ARCHITECT ---
elif app_mode == "Brand Architect":
    st.subheader("Brand Architect")
    tab1, tab2 = st.tabs(["Deep-Dive Wizard", "PDF Extraction"])
    
    with tab1:
        # 1. STRATEGY
        with st.expander("1. Strategy", expanded=True):
            wiz_name = st.text_input("Brand Name")
            wiz_archetype = st.selectbox("Archetype *", ARCHETYPES, index=None, placeholder="Select...")
            wiz_mission = st.text_area("Mission")

        # 2. VOICE (With Resetting Widget)
        with st.expander("2. Voice & Calibration", expanded=True):
            st.info("Upload samples to train the engine. More samples = Higher Confidence.")
            
            # THE FIX: Text area bound to session state, button clears it
            st.text_area("Paste Text Sample (Press Add to save & clear)", key="wiz_temp_sample", height=100)
            if st.button("➕ Add Sample"):
                add_voice_sample()
                st.success(f"Sample added! Total samples: {len(st.session_state['wiz_samples_list'])}")
            
            # Show collected samples
            if st.session_state['wiz_samples_list']:
                st.caption(f"Buffer: {len(st.session_state['wiz_samples_list'])} samples ready to process.")

        # 3. SOCIAL MEDIA INGESTION
        with st.expander("3. Social Media Optimization (New)", expanded=False):
            st.write("Upload screenshots of high-performing posts to train the social engine.")
            wiz_social_file = st.file_uploader("Upload Screenshot", type=["png", "jpg"])

        # 4. VISUALS
        with st.expander("4. Visuals"):
            vc1, vc2 = st.columns(2)
            with vc1:
                p_col = st.color_picker("Primary Color", "#000000")
            with vc2:
                wiz_logo_file = st.file_uploader("Upload Logo", type=["png", "jpg"])

        if st.button("Generate System", type="primary"):
            if not wiz_name or not wiz_archetype:
                st.error("Name and Archetype required.")
            else:
                with st.spinner("Calibrating Engine..."):
                    # Logic to handle logo and social screenshots
                    logo_desc = "None"
                    social_desc = "None"
                    
                    if wiz_logo_file:
                        logo_desc = logic.describe_logo(Image.open(wiz_logo_file))
                    
                    if wiz_social_file:
                        social_desc = logic.analyze_social_post(Image.open(wiz_social_file))

                    # Compile samples from list
                    all_samples = "\n\n".join(st.session_state['wiz_samples_list'])
                    
                    prompt = f"""
                    Create profile for "{wiz_name}".
                    Archetype: {wiz_archetype}
                    Mission: {wiz_mission}
                    Voice Samples: {all_samples}
                    Social Media Style Analysis: {social_desc}
                    Primary Color: {p_col}
                    Logo: {logo_desc}
                    """
                    
                    rules = logic.generate_brand_rules(prompt)
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = rules
                    
                    # Clear the sample buffer after generation
                    st.session_state['wiz_samples_list'] = []
                    st.success("Profile Created & Calibrated!")
                    st.rerun()

    with tab2:
        # PDF Logic (Same as before)
        pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf and st.button("Extract"):
            raw = logic.extract_text_from_pdf(pdf)
            rules = logic.generate_brand_rules(f"Extract rules: {raw[:20000]}")
            st.session_state['profiles'][f"{pdf.name} (PDF)"] = rules
            st.success("Extracted!")

# --- MODULE 6: PROFILE MANAGER ---
elif app_mode == "Profile Manager":
    st.subheader("Profile Manager")
    
    if not active_profile:
        st.warning("No profiles found.")
    else:
        target = st.selectbox("Select Profile", list(st.session_state['profiles'].keys()))
        current_rules = st.session_state['profiles'][target]
        new_rules = st.text_area("Edit Rules", current_rules, height=400)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Save"):
                st.session_state['profiles'][target] = new_rules
                st.success("Saved!")
        with c2:
            pdf_bytes = logic.create_pdf(target, new_rules)
            st.download_button("Download PDF", pdf_bytes, f"{target}.pdf")
        with c3:
            if st.button("Delete"):
                del st.session_state['profiles'][target]
                st.rerun()
