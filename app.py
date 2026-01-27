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

logic = SignetLogic()

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    .stButton>button {width: 100%; border-radius: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;}
    div[data-testid="stExpander"] div[role="button"] p {font-size: 1rem; font-weight: 600; color: #888888;}
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
        "Castellan PR (Internal)": """
        1. COLOR PALETTE: Dark Charcoal (#1A1A1A), Gold Accent (#D4AF37), Castellan Blue (#24363b), White.
        2. TYPOGRAPHY: Headlines: Clean Modern Sans-Serif. Body: High-readability Serif.
        3. VOICE: Strategic, Intelligent, "The Architect". Avoids "peppy" marketing fluff.
        """
    }

MAX_CHECKS = 50
ARCHETYPES = [
    "The Ruler: Control, leadership (e.g. Mercedes)", "The Creator: Innovation (e.g. Apple)", 
    "The Sage: Wisdom (e.g. Google)", "The Innocent: Optimism (e.g. Dove)", 
    "The Outlaw: Disruption (e.g. Virgin)", "The Magician: Vision (e.g. Disney)", 
    "The Hero: Action (e.g. Nike)", "The Lover: Intimacy (e.g. Chanel)", 
    "The Jester: Humor (e.g. Old Spice)", "The Everyman: Belonging (e.g. IKEA)", 
    "The Caregiver: Service (e.g. Volvo)", "The Explorer: Freedom (e.g. Jeep)"
]

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

# --- 1. VISUAL COMPLIANCE ---
if app_mode == "Visual Compliance":
    st.subheader("Visual Compliance Audit")
    if st.session_state['profiles']:
        profile = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        uploaded_file = st.file_uploader("Upload Asset", type=["jpg", "png"])
        if uploaded_file and st.button("Run Audit", type="primary"):
            with st.spinner("Analyzing..."):
                st.markdown(logic.run_visual_audit(Image.open(uploaded_file), st.session_state['profiles'][profile]))
                st.session_state['check_count'] += 1
    else: st.warning("Create a profile first.")

# --- 2. COPY EDITOR ---
elif app_mode == "Copy Editor":
    st.subheader("Intelligent Copy Editor")
    if st.session_state['profiles']:
        profile = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        text_input = st.text_area("Draft Text", height=300)
        if text_input and st.button("Proof & Polish", type="primary"):
            with st.spinner("Editing..."):
                st.markdown(logic.run_copy_editor(text_input, st.session_state['profiles'][profile]))
                st.session_state['check_count'] += 1
    else: st.warning("Create a profile first.")

# --- 3. CONTENT GENERATOR ---
elif app_mode == "Content Generator":
    st.subheader("Content Generator")
    if st.session_state['profiles']:
        profile = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        c1, c2 = st.columns(2)
        with c1: format_type = st.selectbox("Type", ["Press Release", "Internal Email", "Blog Post", "Client Letter"])
        with c2: audience = st.text_input("Target Audience", placeholder="e.g. Investors, Employees, Gen Z")
        topic = st.text_input("Topic", placeholder="e.g. Q4 Earnings")
        key_points = st.text_area("Key Points", height=150)
        if st.button("Generate Draft", type="primary"):
            with st.spinner("Drafting..."):
                st.markdown(logic.run_content_generator(topic, format_type, key_points, audience, st.session_state['profiles'][profile]))
                st.session_state['check_count'] += 1
    else: st.warning("Create a profile first.")

# --- 4. SOCIAL ASSISTANT (NEW) ---
elif app_mode == "📱 Social Media Assistant":
    st.subheader("Social Media Assistant")
    st.caption("Generate platform-optimized captions and hashtags.")
    if st.session_state['profiles']:
        profile = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        c1, c2 = st.columns(2)
        with c1: platform = st.selectbox("Platform", ["LinkedIn", "Instagram", "X (Twitter)", "Facebook"])
        with c2: topic = st.text_input("Topic/Context", placeholder="e.g. Launching our new sustainability initiative")
        img_file = st.file_uploader("Attach Image (Optional but recommended)", type=["jpg", "png"])
        
        if st.button("Generate Social Content", type="primary"):
            image = Image.open(img_file) if img_file else None
            with st.spinner(f"Optimizing for {platform}..."):
                st.markdown(logic.run_social_assistant(platform, topic, image, st.session_state['profiles'][profile]))
                st.session_state['check_count'] += 1
    else: st.warning("Create a profile first.")

# --- 5. BRAND ARCHITECT ---
elif app_mode == "Brand Architect":
    st.subheader("Brand Architect")
    tab1, tab2 = st.tabs(["Deep-Dive Wizard", "PDF Extraction"])
    with tab1:
        with st.expander("1. Strategy", expanded=True):
            wiz_name = st.text_input("Brand Name")
            c1, c2 = st.columns(2)
            with c1: wiz_mission = st.text_area("Mission")
            with c2: wiz_values = st.text_area("Values")
        
        with st.expander("2. Voice & Tone", expanded=False):
            wiz_archetype = st.selectbox("Archetype *", ARCHETYPES, index=None, placeholder="Select Archetype...")
            wiz_tone = st.text_input("Tone Keywords")
            
            st.markdown("---")
            st.markdown("**Voice Calibration (Ghost-Writer)**")
            
            # MULTI-MODAL INPUT FOR VOICE
            voice_col1, voice_col2 = st.columns([1, 1])
            with voice_col1:
                voice_type = st.selectbox("Sample Context", ["General Brand Voice", "Internal Comms (CEO)", "Press/Formal", "Social/Casual"])
            with voice_col2:
                voice_file = st.file_uploader("Upload Sample (PDF/Image)", type=["pdf", "png", "jpg"])
            
            wiz_voice_text = st.text_area("Or Paste Text", height=100, placeholder="Paste sample text here if not uploading...")

        with st.expander("3. Visuals", expanded=False):
            c1, c2 = st.columns(2)
            with c1: p_col = st.text_input("Primary Color", "Brand Blue")
            with c2: s_col = st.text_area("Secondary Palette")
            wiz_logo_file = st.file_uploader("Upload Logo", type=["png", "jpg"])
            wiz_logo_desc = st.text_input("Or Describe Logo")

        if st.button("Generate System", type="primary"):
            if not wiz_name or not wiz_archetype:
                st.error("Name and Archetype required.")
            else:
                with st.spinner("Architecting..."):
                    # 1. Process Voice Sample
                    final_voice_sample = wiz_voice_text
                    if voice_file:
                        if voice_file.type == "application/pdf":
                            final_voice_sample += "\n" + logic.extract_text_from_pdf(voice_file)
                        else:
                            final_voice_sample += "\n" + logic.extract_text_from_image(Image.open(voice_file))
                    
                    final_voice_input = f"CONTEXT: {voice_type}\nCONTENT: {final_voice_sample}"

                    # 2. Process Logo
                    final_logo_desc = wiz_logo_desc
                    if wiz_logo_file and not wiz_logo_desc:
                        final_logo_desc = logic.describe_logo(Image.open(wiz_logo_file))

                    prompt = f"""
                    Create brand profile for "{wiz_name}".
                    STRATEGY: Mission: {wiz_mission}, Values: {wiz_values}
                    VOICE: Archetype: {wiz_archetype}, Tone: {wiz_tone}
                    VOICE SAMPLES: {final_voice_input}
                    VISUALS: Primary: {p_col}, Secondary: {s_col}, Logo: {final_logo_desc}
                    """
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = logic.generate_brand_rules(prompt)
                    st.success(f"Created {wiz_name}!")
                    st.text_area("Result", st.session_state['profiles'][f"{wiz_name} (Gen)"], height=400)

    with tab2:
        pdf = st.file_uploader("Upload Brand PDF", type=["pdf"])
        if pdf and st.button("Extract"):
            st.session_state['profiles'][f"{pdf.name.split('.')[0]} (PDF)"] = logic.generate_brand_rules(f"Extract rules: {logic.extract_text_from_pdf(pdf)[:20000]}")
            st.success("Extracted!")

# --- 6. MANAGER ---
elif app_mode == "Profile Manager":
    st.subheader("Profile Manager")
    if st.session_state['profiles']:
        target = st.selectbox("Profile", list(st.session_state['profiles'].keys()))
        new_rules = st.text_area("Edit Rules", st.session_state['profiles'][target], height=500)
        c1, c2, c3 = st.columns(3)
        if c1.button("Save"): st.session_state['profiles'][target] = new_rules; st.success("Saved!")
        if c2.button("Download PDF"): st.download_button("Download", logic.create_pdf(target, new_rules), f"{target}.pdf")
        if c3.button("Delete"): del st.session_state['profiles'][target]; st.rerun()
    else: st.info("No profiles.")
