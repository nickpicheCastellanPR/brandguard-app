import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
st.set_page_config(page_title="BrandGuard | Castellan PR", page_icon="🛡️", layout="wide")

# --- THE BRAND BRAIN (System Prompt) ---
SYSTEM_PROMPT = """
### ROLE:
You are BrandGuard, the strict, automated Brand Compliance Officer for the Northwest Regional Primary Care Association (NWRPCA).

### THE BRAND LAWS:
1. **COLOR PALETTE:** - Primary: Vermilion Orange (#F45D0D), Black (#000000), White (#FFFFFF)
   - Secondary: Dusk Pink (#EAA792), Cornflower Blue (#618DAE), Dark Olive Green (#394214), Tamarillo (#772621)
   - VIOLATION: Any other dominant color = FAIL.
2. **TYPOGRAPHY:**
   - Headlines: Montserrat Black.
   - Body: Montserrat Regular.
   - Accents: Kepler Std (Italic Display).
   - VIOLATION: Serif headlines or generic Sans-Serif = FAIL.
3. **LOGO SAFETY:**
   - Clearspace: 32% of height.
   - Min Size: 60px.
   - VIOLATION: Crowded or small logo = FAIL.
4. **VOICE:**
   - Keywords: Bold, Relevant, Authentic.
   - VIOLATION: Passive or corporate tone = FAIL.

### OUTPUT FORMAT:
**🛡️ BrandGuard Compliance Report**
**STATUS:** [PASS / FAIL]

**1. 🎨 Color Analysis:** [Pass/Fail] - [Verdict]
**2. 🔠 Typography Check:** [Pass/Fail] - [Verdict]
**3. 📐 Logo & Layout:** [Pass/Fail] - [Verdict]
**4. 🗣️ Voice & Vibe:** [Pass/Fail] - [Verdict]

**🔧 SUGGESTED FIXES:**
* [Actionable list]
"""

# --- SIDEBAR & MODEL SELECTOR ---
with st.sidebar:
    st.title("Settings")
    
    # 1. Get API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter Google API Key", type="password")

    # 2. Dynamic Model Fetcher
    st.divider()
    st.subheader("🤖 Model Selector")
    
    available_models = []
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Ask Google: What models do I have?
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as e:
            st.error(f"API Key Error: {e}")

    # If we found models, show a dropdown. If not, show a text input fallback.
    if available_models:
        # Default to the first one that looks like "flash" if possible
        default_index = 0
        for i, m in enumerate(available_models):
            if "flash" in m:
                default_index = i
                break
        
        selected_model = st.selectbox("Choose AI Model:", available_models, index=default_index)
    else:
        selected_model = st.text_input("Manually Type Model ID:", value="gemini-1.5-flash")

# --- MAIN APP ---
st.title("🛡️ BrandGuard")
st.write("Upload a creative draft to audit it against **NWRPCA Guidelines**.")

col1, col2 = st.columns([1, 1])
uploaded_file = None

with col1:
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview", use_container_width=True)

with col2:
    if st.button("Run Compliance Check", type="primary", use_container_width=True):
        if not api_key:
            st.warning("Please enter your API Key in the sidebar.")
        elif not uploaded_file:
            st.warning("Please upload an image first.")
        else:
            with st.spinner(f"Analyzing using {selected_model}..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(selected_model)
                    response = model.generate_content([SYSTEM_PROMPT, image])
                    st.markdown(response.text)
                    
                    if "FAIL" in response.text:
                        st.error("Compliance Issues Detected")
                    else:
                        st.success("Brand Safe! ✅")
                        
                except Exception as e:
                    st.error(f"Error: {e}")