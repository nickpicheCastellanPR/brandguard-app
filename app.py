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

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    .stButton>button {
        width: 100%; 
        border-radius: 4px; 
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1rem;
        font-weight: 600;
        color: #888888;
    }
    .reportview-container { margin-top: -2em; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Clean Alert Styling */
    .stAlert {border-radius: 4px; border: 1px solid #333;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'check_count' not in st.session_state:
    st.session_state['check_count'] = 0
if 'profiles' not in st.session_state:
    st.session_state['profiles'] = {
        "NWRPCA (Official)": """
        1. COLOR PALETTE: Primary: Vermilion Orange (#F45D0D), Black (#000000), White (#FFFFFF). Secondary: Dusk Pink (#EAA792), Cornflower Blue (#618DAE), Dark Olive Green (#394214), Tamarillo (#772621).
        2. TYPOGRAPHY: Headlines: Montserrat Black. Body: Montserrat Regular. Accents: Kepler Std (Italic Display).
        3. LOGO SAFETY: Clearspace: 32% of height. Min Size: 60px.
        4. VOICE: Bold, Relevant, Authentic. No passive tone. Active verbs only.
        5. STRATEGY: Mission: Strengthen community health centers. Values: Health Equity, Social Justice.
        """,
        "Castellan PR (Internal)": """
        1. COLOR PALETTE: Dark Charcoal (#1A1A1A), Gold Accent (#D4AF37), Castellan Blue (#24363b), White.
        2. TYPOGRAPHY: Headlines: Clean Modern Sans-Serif (e.g., Inter, Helvetica). Body: High-readability Serif.
        3. VOICE: Strategic, Intelligent, "The Architect". Avoids "peppy" marketing fluff.
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
    
    st.caption(f"System Status: Online | Usage: {st.session_state['check_count']}/{MAX_CHECKS}")
    st.divider()
    
    app_mode = st.radio("SELECT MODULE", [
        "Visual Compliance", 
        "Copy Editor", 
        "Content Generator", # NEW MODULE
        "Brand Architect", 
        "Profile Manager"
    ])
    
    st.divider()
    if st.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- LIMIT CHECK ---
if st.session_state['check_count'] >= MAX_CHECKS:
    st.error("🚫 Daily API limit reached. Contact Administrator.")
    st.stop()

# ==========================================
# MODULE 1: VISUAL COMPLIANCE
# ==========================================
if app_mode == "Visual Compliance":
    st.subheader("Visual Compliance Audit")
    st.caption("Upload creative assets to verify brand alignment.")
    
    if not st.session_state['profiles']:
        st.warning("No profiles found. Go to 'Brand Architect' to create one.")
    else:
        profile = st.selectbox("Active Brand Profile", list(st.session_state['profiles'].keys()))
        rules = st.session_state['profiles'][profile]
        
        uploaded_file = st.file_uploader("Upload Asset (JPG/PNG)", type=["jpg", "png", "jpeg"])
        
        if uploaded_file and st.button("Run Audit", type="primary"):
            image = Image.open(uploaded_file)
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(image, caption="Preview", use_container_width=True)
            with c2:
                with st.spinner("Analyzing against Brand Guidelines..."):
                    result = logic.run_visual_audit(image, rules)
                    st.session_state['check_count'] += 1
                    
                    st.markdown("### Audit Report")
                    st.markdown(result)

# ==========================================
# MODULE 2: COPY EDITOR
# ==========================================
elif app_mode == "Copy Editor":
    st.subheader("Intelligent Copy Editor")
    st.caption("Rewrite drafts to match the brand voice and strategy.")
    
    profile = st.selectbox("Active Brand Profile", list(st.session_state['profiles'].keys()))
    rules = st.session_state['profiles'][profile]
    
    c1, c2 = st.columns(2)
    with c1:
        text_input = st.text_area("Original Draft", height=300, placeholder="Paste your draft text here...")
    with c2:
        st.write("**Polished Output**")
        if text_input and st.button("Proof & Polish", type="primary"):
            with st.spinner("Rewriting..."):
                result = logic.run_copy_editor(text_input, rules)
                st.session_state['check_count'] += 1
                st.markdown(result)

# ==========================================
# MODULE 3: CONTENT GENERATOR (NEW)
# ==========================================
elif app_mode == "Content Generator":
    st.subheader("Content Generator")
    st.caption("Generate new on-brand assets from bullet points.")
    
    profile = st.selectbox("Active Brand Profile", list(st.session_state['profiles'].keys()))
    rules = st.session_state['profiles'][profile]
    
    c1, c2 = st.columns([1, 1])
    with c1:
        content_format = st.selectbox("Asset Type", ["Press Release", "Email to Staff", "LinkedIn Post", "Website Article", "Client Letter"])
    with c2:
        topic = st.text_input("Topic / Headline", placeholder="e.g. Q4 Earnings Results")
        
    key_points = st.text_area("Key Points / Bullets", height=200, placeholder="- Record revenue growth\n- Expanding to Europe\n- Thanking the team\n- CEO quote about future")
    
    if st.button("Generate Draft", type="primary"):
        if not key_points or not topic:
            st.error("Please provide a topic and key points.")
        else:
            with st.spinner(f"Drafting {content_format}..."):
                result = logic.run_content_generator(topic, content_format, key_points, rules)
                st.session_state['check_count'] += 1
                st.markdown("### Generated Draft")
                st.markdown(result)

# ==========================================
# MODULE 4: BRAND ARCHITECT (WIZARD)
# ==========================================
elif app_mode == "Brand Architect":
    st.subheader("Brand Architect")
    st.caption("Create a new brand system from scratch or existing files.")
    
    tab1, tab2 = st.tabs(["Deep-Dive Wizard", "PDF Extraction"])
    
    # --- DEEP DIVE WIZARD ---
    with tab1:
        with st.expander("1. Strategy (The Core)", expanded=True):
            wiz_name = st.text_input("Brand Name", placeholder="e.g. Zenith Financial")
            c1, c2 = st.columns(2)
            with c1:
                wiz_mission = st.text_area("Mission", placeholder="To empower...")
            with c2:
                wiz_values = st.text_area("Values", placeholder="Transparency, Agility...")
        
        with st.expander("2. Voice (The Personality)", expanded=False):
            c3, c4 = st.columns(2)
            with c3:
                # UPDATED: New Archetype List
                wiz_archetype = st.selectbox(
                    "Archetype * (Required)", 
                    ARCHETYPES,
                    index=None,
                    placeholder="Select an Archetype..."
                )
            with c4:
                wiz_tone_adjectives = st.text_input("Tone Keywords", placeholder="Professional, Direct")
            wiz_voice_dos = st.text_area("Do's & Don'ts", placeholder="Do use active verbs...")
            
            st.markdown("---")
            st.markdown("**Voice Calibration (Ghost-Writing Engine)**")
            st.caption("Paste 'Gold Standard' copy to calibrate **Tone and Cadence**. Note: For accurate Archetype detection, use 'About Us' or 'Mission' text.")
            wiz_voice_samples = st.text_area("Reference Content", placeholder="Paste 2-3 paragraphs of 'Gold Standard' text here...", height=150)

        with st.expander("3. Visuals (The Look)", expanded=False):
            st.markdown("**Colors**")
            vc1, vc2 = st.columns(2)
            with vc1:
                p_col1_name = st.text_input("Primary Color Name", "Brand Blue")
                p_col1_hex = st.color_picker("Hex", "#0000FF")
            with vc2:
                s_col_list = st.text_area("Secondary Palette", placeholder="#EAA792, #618DAE")

            st.markdown("**Typography**")
            tc1, tc2 = st.columns(2)
            with tc1:
                head_fam = st.selectbox("Headline Style", ["Sans-Serif", "Serif", "Slab Serif", "Script", "Display"])
                head_name = st.text_input("Head Font Name", placeholder="Montserrat")
            with tc2:
                body_fam = st.selectbox("Body Style", ["Sans-Serif", "Serif", "Monospace"])
                body_name = st.text_input("Body Font Name", placeholder="Open Sans")

            st.markdown("**Logo**")
            lc1, lc2 = st.columns(2)
            with lc1:
                wiz_logo_file = st.file_uploader("Upload Logo", type=["png", "jpg"])
            with lc2:
                wiz_logo_desc = st.text_input("Or Describe Logo", placeholder="Blue shield icon...")

        if st.button("Generate System", type="primary"):
            if not wiz_name:
                st.error("⚠️ Error: Brand Name is required.")
            elif not wiz_archetype:
                st.error("⚠️ Error: Please select a Brand Archetype (Step 2).")
            else:
                with st.spinner("Architecting Brand System..."):
                    # Logo Logic
                    final_logo_desc = wiz_logo_desc
                    if wiz_logo_file and not wiz_logo_desc:
                        img = Image.open(wiz_logo_file)
                        final_logo_desc = logic.describe_logo(img)
                        st.info(f"AI Detected Logo: {final_logo_desc}")

                    prompt = f"""
                    Create a comprehensive technical brand profile for "{wiz_name}".
                    ### 1. STRATEGY
                    - Mission: {wiz_mission}
                    - Values: {wiz_values}
                    ### 2. VOICE
                    - Archetype: {wiz_archetype}
                    - Tone Keywords: {wiz_tone_adjectives}
                    - Do's/Don'ts: {wiz_voice_dos}
                    - VOICE SAMPLES (ANALYZE THESE): "{wiz_voice_samples}"
                    ### 3. VISUALS
                    - Primary Color: {p_col1_name} ({p_col1_hex})
                    - Secondary Palette: {s_col_list}
                    - Headline Font: {head_name} ({head_fam})
                    - Body Font: {body_name} ({body_fam})
                    - Logo Description: {final_logo_desc}
                    """
                    
                    rules = logic.generate_brand_rules(prompt)
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = rules
                    st.success(f"Profile for {wiz_name} created!")
                    st.text_area("Result", rules, height=400)

    # --- PDF EXTRACT ---
    with tab2:
        pdf = st.file_uploader("Upload PDF Brand Guide", type=["pdf"])
        if pdf and st.button("Extract Rules"):
            with st.spinner("Extracting..."):
                raw_text = logic.extract_text_from_pdf(pdf)
                prompt = f"Extract strict rules from this text: {raw_text[:25000]}"
                rules = logic.generate_brand_rules(prompt)
                
                name = pdf.name.split(".")[0]
                st.session_state['profiles'][f"{name} (PDF)"] = rules
                st.success("Extracted!")
                st.text_area("Result", rules, height=400)

# ==========================================
# MODULE 5: PROFILE MANAGER
# ==========================================
elif app_mode == "Profile Manager":
    st.subheader("Profile Manager")
    st.caption("Edit, Delete, or Export your brand profiles.")
    
    if st.session_state['profiles']:
        target = st.selectbox("Select Profile", list(st.session_state['profiles'].keys()))
        current_rules = st.session_state['profiles'][target]
        
        # Edit Area
        new_rules = st.text_area("Edit Rules (Markdown Supported)", current_rules, height=500)
        
        # Action Buttons
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            if st.button("Save Changes", type="primary"):
                st.session_state['profiles'][target] = new_rules
                st.success("Saved!")
        
        with c2:
            # EXPORT BUTTON
            pdf_bytes = logic.create_pdf(target, new_rules)
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"{target}_Guidelines.pdf",
                mime='application/pdf'
            )
            
        with c3:
            if st.button("Delete Profile"):
                del st.session_state['profiles'][target]
                st.rerun()
    else:
        st.info("No profiles found.")
