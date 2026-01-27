import streamlit as st
from PIL import Image
from logic import BrandGuardLogic

# --- PAGE CONFIG ---
st.set_page_config(page_title="BrandGuard Pro", page_icon="🛡️", layout="wide")

# Initialize Logic
logic = BrandGuardLogic()

# --- CSS POLISH ---
st.markdown("""
<style>
    .stDeployButton {display:none;}
    .block-container {padding-top: 2rem;}
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: 600;
        color: #E0E0E0;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE & LIMITS ---
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

# DAILY LIMIT
MAX_CHECKS = 50

# --- LOGIN SCREEN ---
if not st.session_state['authenticated']:
    st.title("🛡️ BrandGuard Private Beta")
    st.write("Please enter the access code to continue.")
    
    password = st.text_input("Access Code", type="password")
    if st.button("Enter"):
        if logic.check_password(password):
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("Invalid Code. Try 'beta'")
    st.stop()

# --- MAIN APP ---

with st.sidebar:
    st.title("BrandGuard")
    st.caption(f"Usage: {st.session_state['check_count']} / {MAX_CHECKS} checks")
    
    app_mode = st.radio("Toolbox", ["🚀 Visual Audit", "✍️ Copy Editor", "🏗️ Brand Builder", "📂 Manager"])
    
    st.divider()
    if st.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()

if st.session_state['check_count'] >= MAX_CHECKS:
    st.error("🚫 Daily limit reached. Please upgrade or contact support.")
    st.stop()

# --- TOOL 1: VISUAL AUDIT ---
if app_mode == "🚀 Visual Audit":
    st.header("🚀 Visual Compliance")
    
    if not st.session_state['profiles']:
        st.warning("Create a profile first!")
    else:
        profile = st.selectbox("Select Profile", list(st.session_state['profiles'].keys()))
        rules = st.session_state['profiles'][profile]
        
        uploaded_file = st.file_uploader("Upload Creative", type=["jpg", "png"])
        
        if uploaded_file and st.button("Run Audit"):
            image = Image.open(uploaded_file)
            st.image(image, width=300)
            
            with st.spinner("Analyzing..."):
                result = logic.run_visual_audit(image, rules)
                st.markdown(result)
                st.session_state['check_count'] += 1

# --- TOOL 2: COPY EDITOR ---
elif app_mode == "✍️ Copy Editor":
    st.header("✍️ Smart Copy Editor")
    
    profile = st.selectbox("Select Profile", list(st.session_state['profiles'].keys()))
    rules = st.session_state['profiles'][profile]
    
    text_input = st.text_area("Paste Draft Copy", height=200)
    
    if st.button("Proof & Polish"):
        if text_input:
            with st.spinner("Editing..."):
                result = logic.run_copy_editor(text_input, rules)
                st.markdown(result)
                st.session_state['check_count'] += 1
        else:
            st.warning("Paste text first.")

# --- TOOL 3: BRAND BUILDER ---
elif app_mode == "🏗️ Brand Builder":
    st.header("🏗️ Brand Identity Builder")
    tab1, tab2 = st.tabs(["✨ Deep-Dive Wizard", "📄 PDF Extraction"])
    
    # --- DEEP DIVE WIZARD ---
    with tab1:
        st.write("Build a comprehensive brand system from scratch.")
        
        # 1. STRATEGY SECTION
        with st.expander("1. Brand Strategy (The Core)", expanded=True):
            wiz_name = st.text_input("Brand Name", placeholder="e.g. Northwest Regional PCA")
            
            c1, c2 = st.columns(2)
            with c1:
                wiz_mission = st.text_area("Mission Statement", placeholder="e.g. To strengthen community health centers...")
            with c2:
                wiz_values = st.text_area("Core Values", placeholder="e.g. Social Justice, Health Equity, Collaboration...")
        
        # 2. VOICE SECTION
        with st.expander("2. Voice & Tone (The Personality)", expanded=False):
            st.caption("Based on the '12 Brand Archetypes' framework (Jungian).")
            c3, c4 = st.columns(2)
            with c3:
                wiz_archetype = st.selectbox("Brand Archetype", 
                    ["The Ruler (Control, Leadership)", "The Creator (Innovation, Art)", 
                     "The Sage (Wisdom, Truth)", "The Innocent (Safety, Optimism)", 
                     "The Outlaw (Disruption, Liberation)", "The Magician (Vision, Transformation)", 
                     "The Hero (Mastery, Action)", "The Lover (Intimacy, Connection)", 
                     "The Jester (Pleasure, Humor)", "The Everyman (Belonging, Down-to-earth)", 
                     "The Caregiver (Service, Nurturing)", "The Explorer (Freedom, Discovery)"])
            with c4:
                wiz_tone_adjectives = st.text_input("Tone Adjectives", placeholder="e.g. Professional, Empathetic, Authoritative")
            
            wiz_voice_dos = st.text_area("Voice Do's & Don'ts", placeholder="Do: Use active verbs. Don't: Use passive voice or slang.")

        # 3. VISUALS SECTION
        with st.expander("3. Visual Identity (The Look)", expanded=False):
            st.subheader("🎨 Colors")
            vc1, vc2 = st.columns(2)
            with vc1:
                st.markdown("**Primary Palette**")
                p_col1_name = st.text_input("Primary Color 1 Name", "Brand Blue")
                p_col1_hex = st.color_picker("Hex", "#0000FF", key="p1")
            with vc2:
                st.markdown("**Secondary/Accent**")
                s_col_list = st.text_area("Additional Hex Codes (List)", placeholder="#EAA792 (Dusk Pink)\n#618DAE (Cornflower)\n#394214 (Olive)")

            st.divider()
            
            st.subheader("🔠 Typography")
            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown("**Headlines**")
                head_fam = st.selectbox("Headline Style", ["Sans-Serif (Modern/Clean)", "Serif (Traditional/Trustworthy)", "Slab Serif (Bold/Industrial)", "Script (Personal/Elegant)", "Display (Unique/Stylized)"])
                head_name = st.text_input("Font Name", placeholder="e.g. Montserrat")
            with tc2:
                st.markdown("**Body Copy**")
                body_fam = st.selectbox("Body Style", ["Sans-Serif (High Readability)", "Serif (High Readability)", "Monospace (Tech)"])
                body_name = st.text_input("Body Font Name", placeholder="e.g. Open Sans")

            st.divider()
            st.subheader("🖼️ Logo")
            
            # LOGO UPLOADER & DESCRIBER
            logo_col1, logo_col2 = st.columns(2)
            with logo_col1:
                 wiz_logo_file = st.file_uploader("Upload Logo (Optional)", type=["png", "jpg", "jpeg"])
            with logo_col2:
                 wiz_logo_desc = st.text_input("Logo Description (Optional if uploaded)", placeholder="e.g. A pine tree inside a blue shield")

        # GENERATE BUTTON
        if st.button("✨ Generate Comprehensive Profile", type="primary"):
            if not wiz_name:
                st.error("Brand Name is required.")
            else:
                with st.spinner("Analyzing Brand DNA..."):
                    
                    # LOGO LOGIC: If file uploaded but no desc, ask AI to describe it
                    final_logo_desc = wiz_logo_desc
                    if wiz_logo_file and not wiz_logo_desc:
                        with st.spinner("👀 Analyzing Logo Image..."):
                            img = Image.open(wiz_logo_file)
                            final_logo_desc = logic.describe_logo(img)
                            st.info(f"AI Detected Logo: {final_logo_desc}")

                    # Construct the Mega-Prompt
                    prompt = f"""
                    Create a comprehensive technical brand profile for "{wiz_name}".
                    
                    ### 1. STRATEGY
                    - Mission: {wiz_mission}
                    - Values: {wiz_values}
                    
                    ### 2. VOICE
                    - Archetype: {wiz_archetype}
                    - Tone Keywords: {wiz_tone_adjectives}
                    - Do's/Don'ts: {wiz_voice_dos}
                    
                    ### 3. VISUALS
                    - Primary Color: {p_col1_name} ({p_col1_hex})
                    - Secondary Palette: {s_col_list}
                    - Headline Font: {head_name} ({head_fam})
                    - Body Font: {body_name} ({body_fam})
                    - Logo Description: {final_logo_desc}
                    """
                    
                    rules = logic.generate_brand_rules(prompt)
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = rules
                    st.success(f"Profile for {wiz_name} created successfully!")
                    with st.expander("View Generated Rules"):
                        st.write(rules)

    # --- PDF EXTRACT TAB ---
    with tab2:
        st.write("Upload an existing PDF Brand Guide to automatically extract and encode the rules.")
        pdf = st.file_uploader("Choose PDF", type=["pdf"])
        if pdf and st.button("Extract from PDF"):
            with st.spinner("Reading..."):
                raw_text = logic.extract_text_from_pdf(pdf)
                prompt = f"Extract strict rules from this text: {raw_text[:25000]}"
                rules = logic.generate_brand_rules(prompt)
                
                name = pdf.name.split(".")[0]
                st.session_state['profiles'][f"{name} (PDF)"] = rules
                st.success("Extracted!")

# --- TOOL 4: MANAGER ---
elif app_mode == "📂 Manager":
    st.header("Manage Profiles")
    if st.session_state['profiles']:
        target = st.selectbox("Edit Profile", list(st.session_state['profiles'].keys()))
        
        current_rules = st.session_state['profiles'][target]
        new_rules = st.text_area("Edit Rules", current_rules, height=600) # Made bigger for detail
        
        col1, col2 = st.columns([1, 4])
        with col1:
             if st.button("🗑️ Delete"):
                del st.session_state['profiles'][target]
                st.rerun()
        with col2:
            if st.button("Save Changes"):
                st.session_state['profiles'][target] = new_rules
                st.success("Saved!")
    else:
        st.info("No profiles available.")
