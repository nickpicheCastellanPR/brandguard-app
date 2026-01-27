import streamlit as st
from PIL import Image
from logic import BrandGuardLogic  # Import your new brain

# --- PAGE CONFIG ---
st.set_page_config(page_title="BrandGuard MVP", page_icon="🛡️", layout="wide")

# Initialize Logic
logic = BrandGuardLogic()

# --- CSS POLISH ---
st.markdown("""
<style>
    .stDeployButton {display:none;}
    .block-container {padding-top: 2rem;}
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
        """,
        "Castellan PR (Internal)": """
        1. COLOR PALETTE: Dark Charcoal (#1A1A1A), Gold Accent (#D4AF37), Castellan Blue (#24363b), White.
        2. TYPOGRAPHY: Headlines: Clean Modern Sans-Serif (e.g., Inter, Helvetica). Body: High-readability Serif.
        3. VOICE: Strategic, Intelligent, "The Architect". Avoids "peppy" marketing fluff.
        """
    }

# DAILY LIMIT (Hardcoded for MVP)
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
    st.stop()  # Stop app here if not logged in

# --- MAIN APP (Only runs if authenticated) ---

# Sidebar
with st.sidebar:
    st.title("BrandGuard")
    st.caption(f"Usage: {st.session_state['check_count']} / {MAX_CHECKS} checks")
    
    # Navigation
    app_mode = st.radio("Toolbox", ["🚀 Visual Audit", "✍️ Copy Editor", "🏗️ Brand Builder", "📂 Manager"])
    
    st.divider()
    if st.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()

# Limit Check
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
                # Call Logic
                result = logic.run_visual_audit(image, rules)
                st.markdown(result)
                
                # Increment Counter
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
    st.header("🏗️ Builder")
    tab1, tab2 = st.tabs(["Wizard", "PDF Upload"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Brand Name")
            colors = st.text_input("Key Colors", "Blue #0000FF, White #FFFFFF")
            # NEW FIELD:
            logo_desc = st.text_input("Logo Description", placeholder="e.g. A stylized castle letter C")
        with c2:
            tone = st.text_input("Tone/Voice", "Professional, Trustworthy")
            # RENAMED for clarity:
            layout_rule = st.selectbox("Layout Rule", ["Standard Clearspace", "Heavy White Space", "Compact/Tight"])
        
        if st.button("Generate from Inputs"):
            # We now include the logo description in the prompt
            prompt = f"""
            Create strict brand rules for a brand named "{name}".
            - Colors: {colors}
            - Tone: {tone}
            - Logo Description: {logo_desc} (Enforce that the logo MUST match this description).
            - Layout Style: {layout_rule}
            """
            
            with st.spinner("Drafting Rules..."):
                rules = logic.generate_brand_rules(prompt)
                st.session_state['profiles'][f"{name} (Gen)"] = rules
                st.success(f"Created {name}!")
                with st.expander("View Generated Rules"):
                    st.write(rules)

    with tab2:
        pdf = st.file_uploader("Upload Brand PDF", type="pdf")
        if pdf and st.button("Extract from PDF"):
            with st.spinner("Reading..."):
                raw_text = logic.extract_text_from_pdf(pdf)
                prompt = f"Extract strict rules from this text: {raw_text[:20000]}"
                rules = logic.generate_brand_rules(prompt)
                
                name = pdf.name.split(".")[0]
                st.session_state['profiles'][f"{name} (PDF)"] = rules
                st.success("Extracted!")

# --- TOOL 4: MANAGER ---
elif app_mode == "📂 Manager":
    st.header("Manage Profiles")
    target = st.selectbox("Edit Profile", list(st.session_state['profiles'].keys()))
    
    current_rules = st.session_state['profiles'][target]
    new_rules = st.text_area("Edit Rules", current_rules, height=300)
    
    if st.button("Save Changes"):
        st.session_state['profiles'][target] = new_rules
        st.success("Saved!")
