import streamlit as st
from PIL import Image
import os
from logic import SignetLogic

# --- PAGE CONFIG ---
st.set_page_config(page_title="Signet", page_icon="Signet_Icon_Color.png", layout="wide", initial_sidebar_state="expanded")
logic = SignetLogic()

# --- CSS ---
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    .stButton>button {width: 100%; border-radius: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;}
    div[data-testid="stExpander"] div[role="button"] p {font-size: 1rem; font-weight: 600; color: #888888;}
    .stAlert {border-radius: 4px; border: 1px solid #333;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'check_count' not in st.session_state: st.session_state['check_count'] = 0

# New Profile Structure: Dict with 'rules' and 'samples'
if 'profiles' not in st.session_state:
    st.session_state['profiles'] = {} 

if 'wizard_samples' not in st.session_state:
    st.session_state['wizard_samples'] = []

MAX_CHECKS = 50
ARCHETYPES = ["The Ruler", "The Creator", "The Sage", "The Innocent", "The Outlaw", "The Magician", "The Hero", "The Lover", "The Jester", "The Everyman", "The Caregiver", "The Explorer"]
FONT_HEAD_OPTS = ["Sans-Serif (Modern)", "Serif (Traditional)", "Slab Serif (Bold)", "Display (Loud)", "Script (Creative)"]
FONT_BODY_OPTS = ["Sans-Serif (Digital)", "Serif (Print-like)", "Monospace (Tech)"]

# --- LOGIN ---
if not st.session_state['authenticated']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("Signet_Logo_Color.png"): st.image("Signet_Logo_Color.png", width=300)
        else: st.title("SIGNET")
        if st.button("Enter System") and logic.check_password(st.text_input("Access Code", type="password")):
            st.session_state['authenticated'] = True
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("Signet_Logo_Color.png"): st.image("Signet_Logo_Color.png", use_container_width=True)
    else: st.header("SIGNET")
    st.caption(f"Usage: {st.session_state['check_count']}/{MAX_CHECKS}")
    st.divider()
    app_mode = st.radio("MODULES", ["Visual Compliance", "Copy Editor", "Content Generator", "📱 Social Media Assistant", "Brand Architect", "Profile Manager"])
    st.divider()
    if st.button("Logout"): st.session_state['authenticated'] = False; st.rerun()

if st.session_state['check_count'] >= MAX_CHECKS: st.error("Limit reached."); st.stop()

# --- MODULES ---

if app_mode == "Visual Compliance":
    st.subheader("Visual Compliance Audit")
    if st.session_state['profiles']:
        profile = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        uploaded_file = st.file_uploader("Upload Asset", type=["jpg", "png"])
        if uploaded_file and st.button("Run Audit", type="primary"):
            rules = st.session_state['profiles'][profile]['rules']
            with st.spinner("Analyzing..."):
                st.markdown(logic.run_visual_audit(Image.open(uploaded_file), rules))
                st.session_state['check_count'] += 1
    else: st.warning("Create a profile first.")

elif app_mode == "Copy Editor":
    st.subheader("Intelligent Copy Editor")
    if st.session_state['profiles']:
        profile = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        text_input = st.text_area("Draft Text", height=300)
        if text_input and st.button("Proof & Polish", type="primary"):
            rules = st.session_state['profiles'][profile]['rules']
            with st.spinner("Editing..."):
                st.markdown(logic.run_copy_editor(text_input, rules))
                st.session_state['check_count'] += 1
    else: st.warning("Create a profile first.")

elif app_mode == "Content Generator":
    st.subheader("Content Generator")
    if st.session_state['profiles']:
        profile = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        c1, c2 = st.columns(2)
        with c1: format_type = st.selectbox("Type", ["Press Release", "Internal Email", "Blog Post", "Client Letter"])
        with c2: audience = st.text_input("Target Audience", placeholder="e.g. Investors")
        topic = st.text_input("Topic", placeholder="e.g. Q4 Earnings")
        key_points = st.text_area("Key Points", height=150)
        if st.button("Generate Draft", type="primary"):
            p_data = st.session_state['profiles'][profile]
            with st.spinner("Drafting..."):
                # Pass both rules AND raw samples to the generator
                st.markdown(logic.run_content_generator(topic, format_type, key_points, audience, p_data['rules'], p_data['samples']))
                st.session_state['check_count'] += 1
    else: st.warning("Create a profile first.")

elif app_mode == "📱 Social Media Assistant":
    st.subheader("Social Media Assistant")
    if st.session_state['profiles']:
        profile = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        c1, c2 = st.columns(2)
        with c1: platform = st.selectbox("Platform", ["LinkedIn", "Instagram", "X (Twitter)", "Facebook"])
        with c2: topic = st.text_input("Context", placeholder="e.g. Launching new product")
        img_file = st.file_uploader("Image (Optional)", type=["jpg", "png"])
        if st.button("Generate Content", type="primary"):
            rules = st.session_state['profiles'][profile]['rules']
            img = Image.open(img_file) if img_file else None
            with st.spinner(f"Optimizing for {platform}..."):
                st.markdown(logic.run_social_assistant(platform, topic, img, rules))
                st.session_state['check_count'] += 1
    else: st.warning("Create a profile first.")

elif app_mode == "Brand Architect":
    st.subheader("Brand Architect")
    tab1, tab2 = st.tabs(["Deep-Dive Wizard", "PDF Extraction"])
    with tab1:
        with st.expander("1. Strategy", expanded=True):
            wiz_name = st.text_input("Brand Name")
            c1, c2 = st.columns(2)
            with c1: wiz_mission = st.text_area("Mission")
            with c2: wiz_values = st.text_area("Values")
        
        with st.expander("2. Voice & Tone", expanded=True):
            wiz_archetype = st.selectbox("Archetype *", ARCHETYPES, index=None, placeholder="Select...")
            wiz_tone = st.text_input("Tone Keywords")
            
            st.markdown("---")
            st.markdown("**Voice Calibration (Voice Bank)**")
            st.caption("Add samples (Emails, Press Releases) to train the Ghost-Writer.")
            
            # STAGING AREA
            vc1, vc2 = st.columns([1, 1])
            with vc1: v_type = st.selectbox("Context Tag", ["Internal Comms", "Press/Formal", "Social/Casual", "General"])
            with vc2: v_file = st.file_uploader("Upload (PDF/Img)", type=["pdf","png","jpg"], key="v_up")
            v_text = st.text_area("Or Paste Text", height=100, key="v_txt")
            
            if st.button("➕ Add to Calibration"):
                content = v_text
                if v_file:
                    if v_file.type == "application/pdf": content += "\n" + logic.extract_text_from_pdf(v_file)
                    else: content += "\n" + logic.extract_text_from_image(Image.open(v_file))
                
                if content.strip():
                    st.session_state['wizard_samples'].append({"type": v_type, "content": content})
                    st.success(f"Added {v_type} sample!")
                else:
                    st.error("No text found.")

            # DISPLAY STAGED SAMPLES
            if st.session_state['wizard_samples']:
                st.markdown("##### 📥 Staged Samples:")
                for i, s in enumerate(st.session_state['wizard_samples']):
                    c_del, c_info = st.columns([1, 5])
                    with c_del:
                        if st.button("🗑️", key=f"del_{i}"):
                            st.session_state['wizard_samples'].pop(i)
                            st.rerun()
                    with c_info:
                        st.caption(f"**[{s['type']}]** {s['content'][:50]}...")

        with st.expander("3. Visuals", expanded=False):
            c1, c2 = st.columns(2)
            with c1: p_col = st.text_input("Primary Color")
            with c2: s_col = st.text_area("Secondary Palette")
            
            tc1, tc2 = st.columns(2)
            with tc1: head_font = st.selectbox("Headlines", FONT_HEAD_OPTS); head_name = st.text_input("Headline Name")
            with tc2: body_font = st.selectbox("Body", FONT_BODY_OPTS); body_name = st.text_input("Body Name")
            
            wiz_logo = st.file_uploader("Logo", type=["png","jpg"])
            wiz_logo_desc = st.text_input("Or Describe Logo")

        if st.button("Generate System", type="primary"):
            if not wiz_name or not wiz_archetype:
                st.error("Name and Archetype required.")
            else:
                with st.spinner("Architecting..."):
                    # Process Logo
                    logo_d = wiz_logo_desc
                    if wiz_logo and not logo_d: logo_d = logic.describe_logo(Image.open(wiz_logo))

                    # Compile Voice Samples for Prompt
                    voice_dump = "\n".join([f"[{s['type']}] {s['content']}" for s in st.session_state['wizard_samples']])

                    prompt = f"""
                    Brand: {wiz_name}
                    Strategy: {wiz_mission}, {wiz_values}
                    Voice: {wiz_archetype}, {wiz_tone}
                    Samples: {voice_dump}
                    Visuals: {p_col}, {s_col}, Logo: {logo_d}
                    Fonts: {head_name} ({head_font}), {body_name} ({body_font})
                    """
                    
                    # SAVE OBJECT
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = {
                        "rules": logic.generate_brand_rules(prompt),
                        "samples": st.session_state['wizard_samples']
                    }
                    st.session_state['wizard_samples'] = [] # Clear staging
                    st.success(f"Created {wiz_name}!")
                    st.rerun()

    with tab2:
        pdf = st.file_uploader("PDF Guide", type=["pdf"])
        if pdf and st.button("Extract"):
            rules = logic.generate_brand_rules(f"Extract: {logic.extract_text_from_pdf(pdf)[:20000]}")
            st.session_state['profiles'][f"{pdf.name} (PDF)"] = {"rules": rules, "samples": []}
            st.success("Extracted!")

elif app_mode == "Profile Manager":
    st.subheader("Profile Manager")
    if st.session_state['profiles']:
        target = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        p_data = st.session_state['profiles'][target]
        
        # RULES EDITOR
        new_rules = st.text_area("Brand Rules", p_data['rules'], height=400)
        
        # SAMPLE MANAGER
        st.markdown("### 🗣️ Voice Samples")
        if p_data['samples']:
            for i, s in enumerate(p_data['samples']):
                c1, c2 = st.columns([5, 1])
                with c1: st.info(f"**[{s['type']}]** {s['content'][:100]}...")
                with c2: 
                    if st.button("Delete", key=f"m_del_{i}"):
                        p_data['samples'].pop(i)
                        st.rerun()
        else:
            st.caption("No samples stored.")

        c1, c2, c3 = st.columns(3)
        if c1.button("Save Changes"): 
            st.session_state['profiles'][target]['rules'] = new_rules
            st.success("Saved!")
        if c2.button("Download PDF"): 
            st.download_button("Download", logic.create_pdf(target, new_rules), f"{target}.pdf")
        if c3.button("Delete Profile"): 
            del st.session_state['profiles'][target]
            st.rerun()
    else: st.info("No profiles.")
