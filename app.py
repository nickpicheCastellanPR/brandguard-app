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
        "Demo Profile": "1. Colors: Black & White. 2. Tone: Professional. 3. Font: Sans-Serif."
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
        name = st.text_input("Brand Name")
        tone = st.text_input("Tone/Voice", "Professional, Trustworthy")
        colors = st.text_input("Key Colors", "Blue #0000FF, White #FFFFFF")
        
        if st.button("Generate from Inputs"):
            prompt = f"Create strict brand rules for {name}. Colors: {colors}. Tone: {tone}."
            rules = logic.generate_brand_rules(prompt)
            st.session_state['profiles'][f"{name} (Gen)"] = rules
            st.success(f"Created {name}!")

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
