import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
st.set_page_config(page_title="BrandGuard | Castellan PR", page_icon="🛡️", layout="wide")

# --- SESSION STATE INITIALIZATION ---
# This acts as the app's "Short-Term Memory"
if 'generated_rules' not in st.session_state:
    st.session_state['generated_rules'] = None
if 'generated_profile_name' not in st.session_state:
    st.session_state['generated_profile_name'] = "Custom Profile"

# --- STATIC PRESETS ---
PRESETS = {
    "NWRPCA (Official)": """
    1. COLOR PALETTE: Primary: Vermilion Orange (#F45D0D), Black (#000000), White (#FFFFFF). Secondary: Dusk Pink (#EAA792), Cornflower Blue (#618DAE), Dark Olive Green (#394214), Tamarillo (#772621). VIOLATION: Any other dominant color.
    2. TYPOGRAPHY: Headlines: Montserrat Black. Body: Montserrat Regular. Accents: Kepler Std (Italic Display). VIOLATION: Serif headlines or generic Sans-Serif.
    3. LOGO SAFETY: Clearspace: 32% of height. Min Size: 60px.
    4. VOICE: Bold, Relevant, Authentic. No passive tone.
    """,
    "Castellan PR (Internal)": """
    1. COLOR PALETTE: Dark Charcoal (#1A1A1A), Gold Accent (#D4AF37), White.
    2. TYPOGRAPHY: Headlines: Clean Modern Sans-Serif (e.g., Inter, Helvetica). Body: High-readability Serif.
    3. VOICE: Strategic, Intelligent, "The Architect". Avoids "peppy" marketing fluff.
    """
}

# --- SIDEBAR: GLOBAL SETTINGS ---
with st.sidebar:
    st.title("⚙️ System Control")
    
    # API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter Google API Key", type="password")

    st.divider()
    
    # NAVIGATION
    app_mode = st.radio("Select Mode:", ["🚀 Run Audit", "🏗️ Build Brand Profile"])

    # MODEL SELECTOR
    st.divider()
    st.caption("AI Engine Configuration")
    available_models = []
    if api_key:
        try:
            genai.configure(api_key=api_key)
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except:
            pass
            
    if available_models:
        default_index = 0
        for i, m in enumerate(available_models):
            if "flash" in m:
                default_index = i
                break
        model_name = st.selectbox("Model:", available_models, index=default_index)
    else:
        model_name = st.text_input("Model ID:", value="gemini-1.5-flash")

# --- LOGIC: BUILDER MODE ---
if app_mode == "🏗️ Build Brand Profile":
    st.title("🏗️ Brand Identity Builder")
    st.markdown("Create a codified rule set from raw text or start from scratch.")
    
    tab1, tab2 = st.tabs(["📝 Extract from Text", "✨ Create New (Wizard)"])
    
    # OPTION A: EXTRACT FROM TEXT
    with tab1:
        st.write("Paste raw text from a PDF, website, or email. The AI will extract the rules.")
        raw_text = st.text_area("Paste Brand Text Here:", height=200)
        
        if st.button("Extract & Encode Rules"):
            if not api_key or not raw_text:
                st.warning("Need API Key and Text.")
            else:
                with st.spinner("Decoding brand DNA..."):
                    extraction_prompt = f"""
                    Role: Expert Brand Strategist.
                    Task: Convert the following raw text into a strict "BrandGuard Rule Block".
                    Output Format: Pure text, 4 numbered points (Colors, Typography, Logo, Voice).
                    
                    RAW TEXT:
                    {raw_text}
                    """
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(extraction_prompt)
                    
                    st.session_state['generated_rules'] = response.text
                    st.session_state['generated_profile_name'] = "Extracted Profile"
                    st.success("Rules Extracted! Switch to 'Run Audit' mode to use them.")
                    st.text_area("Preview:", value=response.text, height=200)

    # OPTION B: THE WIZARD
    with tab2:
        st.write("Fill in the basics, and we'll compile the technical guidelines.")
        
        c1, c2 = st.columns(2)
        with c1:
            brand_name = st.text_input("Brand Name")
            primary_color = st.color_picker("Primary Color", "#FF4B4B")
            secondary_color = st.color_picker("Secondary Color", "#000000")
        with c2:
            font_style = st.selectbox("Typography Style", ["Modern Sans-Serif (Clean)", "Classic Serif (Trustworthy)", "Tech/Monospace (Bold)", "Handwritten (Playful)"])
            voice_tone = st.text_input("Voice Adjectives", placeholder="e.g., Friendly, Professional, Urgent")
        
        logo_rule = st.selectbox("Logo Clearspace Strictness", ["Standard (Breathable)", "Tight (Compact)", "Loose (Premium/White Space)"])
        
        if st.button("Compile Guidelines"):
            if not api_key:
                st.warning("Need API Key.")
            else:
                with st.spinner("Synthesizing Brand Book..."):
                    wizard_prompt = f"""
                    Create a strict BrandGuard Rule Block for a brand named "{brand_name}".
                    - Primary Color: {primary_color}
                    - Secondary Color: {secondary_color}
                    - Font Style: {font_style}
                    - Voice: {voice_tone}
                    - Layout Vibe: {logo_rule}
                    
                    Format: 4 numbered points (Colors, Typography, Logo, Voice). Include specific Hex codes.
                    """
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(wizard_prompt)
                    
                    st.session_state['generated_rules'] = response.text
                    st.session_state['generated_profile_name'] = f"{brand_name} (Generated)"
                    st.success(f"Profile Created for {brand_name}! Switch to 'Run Audit' mode.")
                    st.text_area("Generated Rules:", value=response.text, height=200)

# --- LOGIC: AUDIT MODE ---
elif app_mode == "🚀 Run Audit":
    st.title("🚀 Compliance Audit")
    
    # 1. Determine available profiles
    profile_options = list(PRESETS.keys())
    # Add the generated profile if it exists in memory
    if st.session_state['generated_rules']:
        profile_options.insert(0, st.session_state['generated_profile_name'])
        
    selected_profile = st.selectbox("Select Brand Profile:", profile_options)
    
    # 2. Get the rule text
    if selected_profile == st.session_state['generated_profile_name']:
        active_rules = st.session_state['generated_rules']
    else:
        active_rules = PRESETS[selected_profile]
        
    st.info(f"**Active Rules:** {active_rules[:100]}...")

    # 3. Upload & Run
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_file = st.file_uploader("Upload Draft", type=["jpg", "png", "pdf"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Preview", use_container_width=True)

    with col2:
        if st.button("Run Audit", type="primary", use_container_width=True):
            if not api_key or not uploaded_file:
                st.warning("Missing Inputs.")
            else:
                with st.spinner("Auditing..."):
                    try:
                        audit_prompt = f"""
                        ### ROLE: BrandGuard.
                        ### LAWS:
                        {active_rules}
                        
                        ### TASK:
                        Audit the image against these laws.
                        
                        ### OUTPUT:
                        **🛡️ Audit Report**
                        **STATUS:** [PASS / FAIL]
                        
                        **1. 🎨 Color:** [Verdict]
                        **2. 🔠 Type:** [Verdict]
                        **3. 📐 Logo:** [Verdict]
                        **4. 🗣️ Voice:** [Verdict]
                        
                        **🔧 FIXES:**
                        * [List]
                        """
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content([audit_prompt, image])
                        st.markdown(response.text)
                        
                        if "FAIL" in response.text:
                            st.error("Violations Found")
                        else:
                            st.success("Compliant ✅")
                    except Exception as e:
                        st.error(f"Error: {e}")
