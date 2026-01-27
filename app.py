import streamlit as st
from PIL import Image
import os
import json
from logic import SignetLogic

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Signet | Castellan PR", 
    page_icon="Signet_Icon_Color.png", 
    layout="wide",
    initial_sidebar_state="expanded"
)

logic = SignetLogic()

# --- PREMIUM CSS STYLING ---
st.markdown("""
<style>
    /* Global Font & Color */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Button Styling */
    .stButton>button {
        background-color: #24363b; /* Castellan Blue */
        color: white;
        border-radius: 6px;
        border: none;
        height: 3em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #D4AF37; /* Gold Accent */
        color: #1A1A1A;
        border: 1px solid #D4AF37;
    }
    
    /* Clean Input Fields */
    .stTextInput>div>div>input {
        border-radius: 4px;
    }
    
    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #1A1A1A;
        color: #888;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        border-top: 1px solid #333;
        z-index: 100;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE & CALLBACKS ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'check_count' not in st.session_state: st.session_state['check_count'] = 0
if 'profiles' not in st.session_state: st.session_state['profiles'] = {}
if 'wizard_samples' not in st.session_state: st.session_state['wizard_samples'] = []

# Callbacks to clear inputs
def clear_sample_inputs():
    st.session_state['v_type'] = "General Brand Voice"
    st.session_state['v_text'] = ""
    # Note: File uploader clearing is tricky in Streamlit, requires key hacking or just let it persist visually but ignore logic.

MAX_CHECKS = 50
ARCHETYPES = ["The Ruler", "The Creator", "The Sage", "The Innocent", "The Outlaw", "The Magician", "The Hero", "The Lover", "The Jester", "The Everyman", "The Caregiver", "The Explorer"]
FONT_HEAD_OPTS = ["Sans-Serif (Modern)", "Serif (Traditional)", "Slab Serif (Bold)", "Display (Loud)", "Script (Creative)"]
FONT_BODY_OPTS = ["Sans-Serif (Digital)", "Serif (Print-like)", "Monospace (Tech)"]

# --- LOGIN SCREEN ---
if not st.session_state['authenticated']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists("Signet_Logo_Color.png"): 
            st.image("Signet_Logo_Color.png", use_container_width=True)
        else: 
            st.markdown("<h1 style='text-align: center;'>SIGNET</h1>", unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; color: #666;'>Strategic Brand Governance Platform</p>", unsafe_allow_html=True)
        
        pwd = st.text_input("Access Code", type="password")
        if st.button("Initialize System"):
            if logic.check_password(pwd):
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Access Denied.")
    st.markdown('<div class="footer">POWERED BY CASTELLAN PR | CONFIDENTIAL</div>', unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("Signet_Logo_Color.png"): 
        st.image("Signet_Logo_Color.png", use_container_width=True)
    else: 
        st.header("SIGNET")
    
    st.caption("v1.2 | Enterprise Edition")
    st.divider()
    
    # Updated Menu Labels (Removed Emojis)
    app_mode = st.radio("CORE MODULES", [
        "Visual Compliance", 
        "Copy Editor", 
        "Content Generator", 
        "Social Media Assistant", 
        "Brand Architect", 
        "Profile Manager"
    ])
    
    st.divider()
    st.caption(f"API Usage: {st.session_state['check_count']}/{MAX_CHECKS}")
    if st.button("Logout"): 
        st.session_state['authenticated'] = False
        st.rerun()

if st.session_state['check_count'] >= MAX_CHECKS: st.error("Daily Limit Reached."); st.stop()

# --- 1. VISUAL COMPLIANCE ---
if app_mode == "Visual Compliance":
    st.subheader("Visual Compliance Audit")
    st.caption("Verify assets against strict brand guidelines.")
    if st.session_state['profiles']:
        profile = st.selectbox("Active Profile", list(st.session_state['profiles'].keys()))
        uploaded_file = st.file_uploader("Upload Creative Asset", type=["jpg", "png"])
        if uploaded_file and st.button("Run Compliance Check", type="primary"):
            rules = st.session_state['profiles'][profile]['rules']
            with st.spinner("Analyzing pixels & palettes..."):
                # Clean display
                raw_result = logic.run_visual_audit(Image.open(uploaded_file), rules)
                clean_result = logic.clean_markdown(raw_result)
                st.info("Analysis Complete")
                st.markdown(raw_result) # Keep markdown for display, clean for PDF later
                st.session_state['check_count'] += 1
    else: st.warning("No Profiles Found. Please visit the Brand Architect.")

# --- 2. COPY EDITOR ---
elif app_mode == "Copy Editor":
    st.subheader("Intelligent Copy Editor")
    st.caption("Align drafts with brand voice and strategy.")
    if st.session_state['profiles']:
        profile = st.selectbox("Active Profile", list(st.session_state['profiles'].keys()))
        text_input = st.text_area("Paste Draft Text", height=300)
        if text_input and st.button("Proof & Polish", type="primary"):
            rules = st.session_state['profiles'][profile]['rules']
            with st.spinner("Calibrating tone..."):
                st.markdown(logic.run_copy_editor(text_input, rules))
                st.session_state['check_count'] += 1
    else: st.warning("No Profiles Found.")

# --- 3. CONTENT GENERATOR ---
elif app_mode == "Content Generator":
    st.subheader("Content Generator")
    st.caption("Draft new on-brand assets from key points.")
    if st.session_state['profiles']:
        profile = st.selectbox("Active Profile", list(st.session_state['profiles'].keys()))
        c1, c2 = st.columns(2)
        with c1: format_type = st.selectbox("Asset Type", ["Press Release", "Internal Email (CEO)", "Blog Post", "Client Letter", "Speech"])
        with c2: audience = st.text_input("Target Audience", placeholder="e.g. Investors, Gen Z, Employees")
        topic = st.text_input("Subject / Headline", placeholder="e.g. Q4 Earnings")
        key_points = st.text_area("Key Points (Bullets)", height=150)
        
        if st.button("Generate Draft", type="primary"):
            p_data = st.session_state['profiles'][profile]
            with st.spinner("Drafting..."):
                st.markdown(logic.run_content_generator(topic, format_type, key_points, audience, p_data['rules'], p_data['samples']))
                st.session_state['check_count'] += 1
    else: st.warning("No Profiles Found.")

# --- 4. SOCIAL ASSISTANT ---
elif app_mode == "Social Media Assistant":
    st.subheader("Social Media Assistant")
    st.caption("Generate platform-optimized content with strategic rationale.")
    if st.session_state['profiles']:
        profile = st.selectbox("Active Profile", list(st.session_state['profiles'].keys()))
        c1, c2 = st.columns(2)
        with c1: platform = st.selectbox("Platform", ["LinkedIn (Thought Leadership)", "LinkedIn (Company News)", "Instagram", "X (Twitter)", "Facebook"])
        with c2: topic = st.text_input("Context / Topic", placeholder="e.g. Launching new sustainability initiative")
        img_file = st.file_uploader("Attach Image (Optional)", type=["jpg", "png"])
        
        if st.button("Generate Strategy & Content", type="primary"):
            rules = st.session_state['profiles'][profile]['rules']
            img = Image.open(img_file) if img_file else None
            with st.spinner(f"Optimizing for {platform}..."):
                st.markdown(logic.run_social_assistant(platform, topic, img, rules))
                st.session_state['check_count'] += 1
    else: st.warning("No Profiles Found.")

# --- 5. BRAND ARCHITECT ---
elif app_mode == "Brand Architect":
    st.subheader("Brand Architect")
    st.caption("Build comprehensive brand systems.")
    
    tab1, tab2 = st.tabs(["Deep-Dive Wizard", "PDF Extraction"])
    with tab1:
        st.markdown("#### 1. Core Strategy")
        wiz_name = st.text_input("Brand Name")
        c1, c2 = st.columns(2)
        with c1: wiz_mission = st.text_area("Mission Statement")
        with c2: wiz_values = st.text_area("Core Values")
        
        st.markdown("#### 2. Voice & Personality")
        wiz_archetype = st.selectbox("Brand Archetype *", ARCHETYPES, index=None, placeholder="Select Archetype...")
        wiz_tone = st.text_input("Tone Keywords", placeholder="e.g. Professional, Direct")
        
        st.markdown("---")
        st.markdown("##### 🗣️ Voice Calibration (Ghost-Writer)")
        st.info("Upload samples to train the AI on specific formats (e.g. 'Internal Email').")
        
        # STAGING AREA WITH AUTO-CLEAR
        with st.container():
            vc1, vc2 = st.columns([1, 1])
            with vc1: v_type = st.selectbox("Context", ["Internal Comms", "Press/Formal", "Social/Casual", "General"], key="v_type")
            with vc2: v_file = st.file_uploader("Upload (PDF/Img)", type=["pdf","png","jpg"], key="v_up")
            v_text = st.text_area("Or Paste Text", height=100, key="v_txt")
            
            if st.button("➕ Add Sample"):
                content = v_text
                if v_file:
                    if v_file.type == "application/pdf": content += "\n" + logic.extract_text_from_pdf(v_file)
                    else: content += "\n" + logic.extract_text_from_image(Image.open(v_file))
                
                if content.strip():
                    st.session_state['wizard_samples'].append({"type": v_type, "content": content})
                    st.success(f"Added {v_type} sample!")
                    # We can't force-clear widgets easily in pure Streamlit without rerun, 
                    # but we can rely on the user seeing it appear in the list below.
                else:
                    st.error("No text found.")

        # DISPLAY STAGED SAMPLES
        if st.session_state['wizard_samples']:
            st.markdown("###### Staged Samples:")
            for i, s in enumerate(st.session_state['wizard_samples']):
                c_del, c_info = st.columns([1, 5])
                with c_del:
                    if st.button("✖", key=f"del_{i}"):
                        st.session_state['wizard_samples'].pop(i)
                        st.rerun()
                with c_info:
                    st.caption(f"**[{s['type']}]** {s['content'][:60]}...")

        st.markdown("---")
        st.markdown("#### 3. Visual Identity")
        c1, c2 = st.columns(2)
        with c1: p_col = st.text_input("Primary Color")
        with c2: s_col = st.text_area("Secondary Palette")
        
        tc1, tc2 = st.columns(2)
        with tc1: head_font = st.selectbox("Headlines", FONT_HEAD_OPTS); head_name = st.text_input("Headline Font Name")
        with tc2: body_font = st.selectbox("Body", FONT_BODY_OPTS); body_name = st.text_input("Body Font Name")
        
        wiz_logo = st.file_uploader("Upload Logo", type=["png","jpg"])
        wiz_logo_desc = st.text_input("Or Describe Logo")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("GENERATE SYSTEM PROFILE", type="primary"):
            if not wiz_name or not wiz_archetype:
                st.error("Critical: Brand Name and Archetype are required.")
            else:
                with st.spinner("Architecting Brand System..."):
                    # Process Logo
                    logo_d = wiz_logo_desc
                    if wiz_logo and not logo_d: logo_d = logic.describe_logo(Image.open(wiz_logo))

                    voice_dump = "\n".join([f"[{s['type']}] {s['content']}" for s in st.session_state['wizard_samples']])

                    prompt = f"""
                    Brand: {wiz_name}
                    Strategy: {wiz_mission}, {wiz_values}
                    Voice: {wiz_archetype}, {wiz_tone}
                    Samples: {voice_dump}
                    Visuals: {p_col}, {s_col}, Logo: {logo_d}
                    Fonts: {head_name} ({head_font}), {body_name} ({body_font})
                    """
                    
                    raw_rules = logic.generate_brand_rules(prompt)
                    # Save Cleaned Version
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = {
                        "rules": logic.clean_markdown(raw_rules), # Store clean text
                        "samples": st.session_state['wizard_samples']
                    }
                    st.session_state['wizard_samples'] = []
                    st.success(f"Profile for {wiz_name} Created Successfully!")
                    st.rerun()

    with tab2:
        pdf = st.file_uploader("Upload Brand PDF", type=["pdf"])
        if pdf and st.button("Extract"):
            rules = logic.generate_brand_rules(f"Extract: {logic.extract_text_from_pdf(pdf)[:20000]}")
            st.session_state['profiles'][f"{pdf.name.split('.')[0]} (PDF)"] = {"rules": logic.clean_markdown(rules), "samples": []}
            st.success("Extracted!")

# --- 6. MANAGER ---
elif app_mode == "Profile Manager":
    st.subheader("Profile Manager")
    st.caption("Manage, Back-up, and Restore Brand Profiles.")
    
    # 1. Backup/Restore Section
    with st.expander("💾 Backup & Restore (JSON)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            # Download
            json_data = json.dumps(st.session_state['profiles'], indent=2)
            st.download_button("Download All Profiles (.json)", json_data, "signet_backup.json", "application/json")
        with c2:
            # Upload
            uploaded_json = st.file_uploader("Restore Profiles", type=["json"])
            if uploaded_json is not None:
                if st.button("Load Backup"):
                    try:
                        data = json.load(uploaded_json)
                        st.session_state['profiles'].update(data)
                        st.success("Profiles Restored!")
                        st.rerun()
                    except:
                        st.error("Invalid JSON file.")

    st.divider()

    # 2. Edit Section
    if st.session_state['profiles']:
        target = st.selectbox("Select Profile to Edit", list(st.session_state['profiles'].keys()))
        p_data = st.session_state['profiles'][target]
        
        c_edit, c_sample = st.columns([1, 1])
        
        with c_edit:
            st.markdown("##### 📝 Brand Rules")
            new_rules = st.text_area("Edit Rules Text", p_data['rules'], height=400)
        
        with c_sample:
            st.markdown("##### 🗣️ Voice Samples")
            if p_data['samples']:
                for i, s in enumerate(p_data['samples']):
                    with st.container():
                        st.info(f"**[{s['type']}]** {s['content'][:60]}...")
                        if st.button("Delete Sample", key=f"m_del_{i}"):
                            p_data['samples'].pop(i)
                            st.rerun()
            else:
                st.caption("No samples attached.")

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        if c1.button("Save Changes", type="primary"): 
            st.session_state['profiles'][target]['rules'] = new_rules
            st.success("Saved!")
        if c2.button("Download PDF Guide"): 
            st.download_button("Download PDF", logic.create_pdf(target, new_rules), f"{target}_Guidelines.pdf")
        if c3.button("🗑️ DELETE PROFILE"): 
            del st.session_state['profiles'][target]
            st.rerun()
    else: st.info("No profiles found.")

# --- FOOTER ---
st.markdown('<div class="footer">Signet v1.2 | Powered by Castellan PR | Enterprise Confidential</div>', unsafe_allow_html=True)
