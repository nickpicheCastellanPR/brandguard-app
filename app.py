import streamlit as st
from PIL import Image
import os
import json
from logic import SignetLogic

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Signet | Enterprise", 
    page_icon="Signet_Icon_Color.png", 
    layout="wide",
    initial_sidebar_state="expanded"
)

logic = SignetLogic()

# --- PREMIUM CSS OVERHAUL (V2.1 - Contrast Fix) ---
st.markdown("""
<style>
    /* 1. GLOBAL FONTS & THEME */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
        background-color: #0E1117; /* Deepest Dark Blue/Black */
    }
    
    /* 2. SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #050505; /* Pure Black for high contrast */
        border-right: 1px solid #2A2A2A;
    }
    
    /* LOGO CONTAINER FIX: 
       This targets the First Image in the Sidebar (The Logo).
       It adds a light background so the Dark Text is visible. */
    section[data-testid="stSidebar"] [data-testid="stImage"] {
        background-color: #E0E0E0; /* Light Grey Background */
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }

    /* NAVIGATION MENU STYLING */
    div[role="radiogroup"] > label > div:first-of-type {display: None;} /* Hide circles */
    div[role="radiogroup"] label {
        background: transparent;
        padding: 12px 15px;
        border-radius: 6px;
        margin-bottom: 6px;
        border: 1px solid transparent;
        transition: all 0.2s ease;
        color: #CCCCCC !important; /* High Contrast Grey */
        font-weight: 500;
        cursor: pointer;
        display: block; 
    }
    div[role="radiogroup"] label:hover {
        background: #1E1E1E;
        color: #FFFFFF !important; /* Pure White on Hover */
        border-color: #333;
        transform: translateX(4px); 
    }
    /* Active State styling */
    div[role="radiogroup"] label[data-checked="true"] {
        background: #1E1E1E;
        color: #D4AF37 !important; /* Gold */
        border-left: 3px solid #D4AF37;
    }
    
    /* 3. INPUT FIELDS (Forced High Contrast) */
    /* Force text to be white and background to be dark charcoal */
    input[type="text"], input[type="password"], textarea {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        border-radius: 6px;
    }
    /* Focus state */
    input:focus, textarea:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 0 1px #D4AF37 !important;
        color: #FFFFFF !important;
    }
    /* Select Box / Dropdown Text */
    div[data-baseweb="select"] > div {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
    }

    /* 4. BUTTONS (Castellan Gold & Blue) */
    .stButton>button {
        background-color: #24363b; 
        color: white;
        border: 1px solid #333;
        border-radius: 4px;
        height: 3em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #D4AF37; 
        color: #000;
        border-color: #D4AF37;
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.3); 
    }
    
    /* 5. DASHBOARD CARDS */
    div[data-testid="stMetric"] {
        background-color: #161616;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 8px;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #D4AF37 !important;
    }
    
    /* 6. WARNING BOX */
    .custom-warning {
        background-color: #1E1E1E;
        border-left: 4px solid #D4AF37;
        padding: 15px;
        border-radius: 4px;
        color: #E0E0E0;
        margin-bottom: 20px;
    }

    /* UTILITIES */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0E0E0E;
        color: #444;
        text-align: right;
        padding: 8px 30px;
        font-size: 10px;
        border-top: 1px solid #222;
        z-index: 999;
        letter-spacing: 1px;
    }
    .block-container { padding-bottom: 50px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'check_count' not in st.session_state: st.session_state['check_count'] = 0
if 'profiles' not in st.session_state: st.session_state['profiles'] = {}
if 'wizard_samples' not in st.session_state: st.session_state['wizard_samples'] = []

MAX_CHECKS = 50
ARCHETYPES = ["The Ruler", "The Creator", "The Sage", "The Innocent", "The Outlaw", "The Magician", "The Hero", "The Lover", "The Jester", "The Everyman", "The Caregiver", "The Explorer"]
FONT_HEAD_OPTS = ["Sans-Serif (Modern)", "Serif (Traditional)", "Slab Serif (Bold)", "Display (Loud)", "Script (Creative)"]
FONT_BODY_OPTS = ["Sans-Serif (Digital)", "Serif (Print-like)", "Monospace (Tech)"]

# --- LOGIN SCREEN ---
if not st.session_state['authenticated']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # FIX: Restrict logo width so it doesn't explode
        if os.path.exists("Signet_Logo_Color.png"): 
            st.image("Signet_Logo_Color.png", width=300) 
        else: 
            st.markdown("<h1 style='text-align: center; color: #D4AF37; letter-spacing: 5px;'>SIGNET</h1>", unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; color: #666; font-size: 0.9rem; margin-top: -10px;'>ENTERPRISE BRAND GOVERNANCE</p><br>", unsafe_allow_html=True)
        
        # Input color fixed via CSS
        pwd = st.text_input("SECURE ACCESS CODE", type="password", label_visibility="collapsed", placeholder="Enter Access Code")
        if st.button("AUTHENTICATE"):
            if logic.check_password(pwd):
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("ACCESS DENIED")
    st.markdown('<div class="footer">CASTELLAN PR | SYSTEM LOCKED</div>', unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    # Logo is now styled by CSS to have a light background container
    if os.path.exists("Signet_Logo_Color.png"): 
        st.image("Signet_Logo_Color.png", use_container_width=True)
    else: 
        st.header("SIGNET")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    app_mode = st.radio("MENU", [
        "Dashboard",
        "Visual Compliance", 
        "Copy Editor", 
        "Content Generator", 
        "Social Media Assistant", 
        "Brand Architect", 
        "Profile Manager"
    ], label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"API Usage: {st.session_state['check_count']}/{MAX_CHECKS}")
    st.progress(st.session_state['check_count'] / MAX_CHECKS)
    
    st.divider()
    if st.button("LOGOUT"): 
        st.session_state['authenticated'] = False
        st.rerun()

if st.session_state['check_count'] >= MAX_CHECKS: st.error("Daily API Limit Reached."); st.stop()

# ==========================================
# 0. DASHBOARD
# ==========================================
if app_mode == "Dashboard":
    st.title("Command Center")
    st.caption("Real-time governance overview.")
    st.markdown("<br>", unsafe_allow_html=True)

    # METRICS
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Active Profiles", len(st.session_state['profiles']))
    with m2: st.metric("Audits Run", st.session_state['check_count'])
    with m3: st.metric("System Status", "ONLINE")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # QUICK ACTIONS
    if not st.session_state['profiles']:
        st.markdown("""
        <div class="custom-warning">
            <strong>⚠️ No Brand Profiles Detected</strong><br>
            The system is standing by. Please initialize a profile to begin governance.
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.subheader("🏗️ Architect New Profile")
                st.caption("Define mission, voice, and visuals from scratch.")
                if st.button("Launch Wizard"): 
                    st.info("Select 'Brand Architect' from the sidebar.")
        with c2:
             with st.container(border=True):
                st.subheader("📄 Import Guidelines")
                st.caption("Extract rules directly from an existing PDF.")
                if st.button("Upload PDF"):
                    st.info("Select 'Brand Architect' -> 'PDF Extraction'.")
    else:
        st.subheader("Quick Actions")
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True):
                st.markdown("**Visual Audit**")
                st.caption("Validate creative assets.")
        with c2:
            with st.container(border=True):
                st.markdown("**Ghost Writer**")
                st.caption("Draft executive comms.")
        with c3:
            with st.container(border=True):
                st.markdown("**Social Strategy**")
                st.caption("Generate posts.")

# ==========================================
# 1. VISUAL COMPLIANCE
# ==========================================
elif app_mode == "Visual Compliance":
    st.subheader("Visual Compliance Audit")
    if st.session_state['profiles']:
        profile = st.selectbox("Select Brand Profile", list(st.session_state['profiles'].keys()))
        uploaded_file = st.file_uploader("Upload Creative Asset", type=["jpg", "png"])
        
        if uploaded_file and st.button("RUN COMPLIANCE CHECK", type="primary"):
            rules = st.session_state['profiles'][profile]['rules']
            with st.spinner("Analyzing pixels & palettes..."):
                raw_result = logic.run_visual_audit(Image.open(uploaded_file), rules)
                st.success("Audit Complete")
                st.markdown(logic.clean_markdown(raw_result)) 
                st.session_state['check_count'] += 1
    else: 
        st.markdown('<div class="custom-warning">⚠️ No Profiles Found. Visit Brand Architect.</div>', unsafe_allow_html=True)

# ==========================================
# 2. COPY EDITOR
# ==========================================
elif app_mode == "Copy Editor":
    st.subheader("Intelligent Copy Editor")
    if st.session_state['profiles']:
        profile = st.selectbox("Select Brand Profile", list(st.session_state['profiles'].keys()))
        text_input = st.text_area("Paste Draft Text", height=300, placeholder="Enter text to proofread...")
        
        if text_input and st.button("PROOF & POLISH", type="primary"):
            rules = st.session_state['profiles'][profile]['rules']
            with st.spinner("Calibrating tone..."):
                st.markdown("### 🛡️ Signet Report")
                st.markdown(logic.run_copy_editor(text_input, rules))
                st.session_state['check_count'] += 1
    else: 
        st.markdown('<div class="custom-warning">⚠️ No Profiles Found. Visit Brand Architect.</div>', unsafe_allow_html=True)

# ==========================================
# 3. CONTENT GENERATOR
# ==========================================
elif app_mode == "Content Generator":
    st.subheader("Content Generator")
    if st.session_state['profiles']:
        profile = st.selectbox("Select Brand Profile", list(st.session_state['profiles'].keys()))
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1: format_type = st.selectbox("Asset Type", ["Press Release", "Internal Email (CEO)", "Blog Post", "Client Letter", "Speech"])
            with c2: audience = st.text_input("Target Audience", placeholder="e.g. Investors")
            topic = st.text_input("Subject / Headline", placeholder="e.g. Q4 Earnings")
            key_points = st.text_area("Key Points (Bullets)", height=150)
        
        if st.button("GENERATE DRAFT", type="primary"):
            p_data = st.session_state['profiles'][profile]
            with st.spinner("Consulting Ghost-Writer Engine..."):
                st.markdown("### 📝 Generated Draft")
                st.markdown(logic.run_content_generator(topic, format_type, key_points, audience, p_data['rules'], p_data['samples']))
                st.session_state['check_count'] += 1
    else: 
        st.markdown('<div class="custom-warning">⚠️ No Profiles Found. Visit Brand Architect.</div>', unsafe_allow_html=True)

# ==========================================
# 4. SOCIAL ASSISTANT
# ==========================================
elif app_mode == "Social Media Assistant":
    st.subheader("Social Media Assistant")
    if st.session_state['profiles']:
        profile = st.selectbox("Select Brand Profile", list(st.session_state['profiles'].keys()))
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1: platform = st.selectbox("Platform", ["LinkedIn (Thought Leadership)", "LinkedIn (Company News)", "Instagram", "X (Twitter)", "Facebook"])
            with c2: topic = st.text_input("Context / Topic", placeholder="e.g. Sustainability Launch")
            img_file = st.file_uploader("Attach Image (Optional)", type=["jpg", "png"])
        
        if st.button("GENERATE STRATEGY", type="primary"):
            rules = st.session_state['profiles'][profile]['rules']
            img = Image.open(img_file) if img_file else None
            with st.spinner(f"Optimizing for {platform}..."):
                st.markdown("### 📱 Social Strategy")
                st.markdown(logic.run_social_assistant(platform, topic, img, rules))
                st.session_state['check_count'] += 1
    else: 
        st.markdown('<div class="custom-warning">⚠️ No Profiles Found. Visit Brand Architect.</div>', unsafe_allow_html=True)

# ==========================================
# 5. BRAND ARCHITECT
# ==========================================
elif app_mode == "Brand Architect":
    st.subheader("Brand Architect")
    st.caption("Define the immutable laws of your brand.")
    
    tab1, tab2 = st.tabs(["Deep-Dive Wizard", "PDF Extraction"])
    with tab1:
        with st.container(border=True):
            st.markdown("#### 1. Core Strategy")
            wiz_name = st.text_input("Brand Name", placeholder="e.g. Castellan PR")
            c1, c2 = st.columns(2)
            with c1: wiz_mission = st.text_area("Mission Statement", height=100)
            with c2: wiz_values = st.text_area("Core Values", height=100)
        
        with st.container(border=True):
            st.markdown("#### 2. Voice & Personality")
            wiz_archetype = st.selectbox("Brand Archetype *", ARCHETYPES, index=None, placeholder="Select Archetype...")
            wiz_tone = st.text_input("Tone Keywords", placeholder="e.g. Professional, Direct")
            
            st.markdown("---")
            st.markdown("##### 🗣️ Voice Calibration (Ghost-Writer)")
            st.caption("Upload 'Gold Standard' samples (PDFs/Screenshots) to train the AI on specific formats.")
            
            # STAGING AREA
            col_in1, col_in2 = st.columns([1,2])
            with col_in1: v_type = st.selectbox("Context", ["Internal Comms", "Press/Formal", "Social/Casual", "General"], key="v_type")
            with col_in2: v_file = st.file_uploader("Upload File", type=["pdf","png","jpg"], key="v_up", label_visibility="collapsed")
            v_text = st.text_area("Or Paste Text", height=80, key="v_txt", placeholder="Paste text here...")
            
            if st.button("➕ Add Sample to Training Set"):
                content = v_text
                if v_file:
                    if v_file.type == "application/pdf": content += "\n" + logic.extract_text_from_pdf(v_file)
                    else: content += "\n" + logic.extract_text_from_image(Image.open(v_file))
                
                if content.strip():
                    st.session_state['wizard_samples'].append({"type": v_type, "content": content})
                    st.success(f"Added {v_type} sample!")
                else:
                    st.error("No text detected.")

            # STAGED LIST
            if st.session_state['wizard_samples']:
                st.markdown("**Staged Samples:**")
                for i, s in enumerate(st.session_state['wizard_samples']):
                    st.text(f"• [{s['type']}] {s['content'][:50]}...")
                    if st.button(f"Remove Sample {i+1}", key=f"del_{i}"):
                        st.session_state['wizard_samples'].pop(i)
                        st.rerun()

        with st.container(border=True):
            st.markdown("#### 3. Visual Identity")
            c1, c2 = st.columns(2)
            with c1: p_col = st.text_input("Primary Color Hex", placeholder="#000000")
            with c2: s_col = st.text_area("Secondary Palette", height=68, placeholder="#FFFFFF, #333333")
            
            tc1, tc2 = st.columns(2)
            with tc1: head_font = st.selectbox("Headline Style", FONT_HEAD_OPTS); head_name = st.text_input("Headline Font Name")
            with tc2: body_font = st.selectbox("Body Style", FONT_BODY_OPTS); body_name = st.text_input("Body Font Name")
            
            wiz_logo = st.file_uploader("Upload Logo", type=["png","jpg"])
            wiz_logo_desc = st.text_input("Or Describe Logo")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("GENERATE SYSTEM PROFILE", type="primary"):
            if not wiz_name or not wiz_archetype:
                st.error("Error: Brand Name and Archetype are required.")
            else:
                with st.spinner("Architecting Brand System..."):
                    logo_d = wiz_logo_desc
                    if wiz_logo and not logo_d: logo_d = logic.describe_logo(Image.open(wiz_logo))
                    voice_dump = "\n".join([f"[{s['type']}] {s['content']}" for s in st.session_state['wizard_samples']])
                    prompt = f"Brand: {wiz_name}\nStrategy: {wiz_mission}, {wiz_values}\nVoice: {wiz_archetype}, {wiz_tone}\nSamples: {voice_dump}\nVisuals: {p_col}, {s_col}, Logo: {logo_d}\nFonts: {head_name} ({head_font}), {body_name} ({body_font})"
                    
                    raw_rules = logic.generate_brand_rules(prompt)
                    st.session_state['profiles'][f"{wiz_name} (Gen)"] = {
                        "rules": logic.clean_markdown(raw_rules), 
                        "samples": st.session_state['wizard_samples']
                    }
                    st.session_state['wizard_samples'] = []
                    st.success(f"Profile for {wiz_name} Created!")
                    st.rerun()

    with tab2:
        pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf and st.button("EXTRACT RULES", type="primary"):
            with st.spinner("Reading PDF..."):
                rules = logic.generate_brand_rules(f"Extract: {logic.extract_text_from_pdf(pdf)[:20000]}")
                st.session_state['profiles'][f"{pdf.name.split('.')[0]} (PDF)"] = {"rules": logic.clean_markdown(rules), "samples": []}
                st.success("Extraction Complete!")

# ==========================================
# 6. PROFILE MANAGER
# ==========================================
elif app_mode == "Profile Manager":
    st.subheader("Profile Manager")
    
    with st.expander("💾 System Backup & Restore", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            json_data = json.dumps(st.session_state['profiles'], indent=2)
            st.download_button("Download Database (.json)", json_data, "signet_backup.json", "application/json")
        with c2:
            uploaded_json = st.file_uploader("Restore Database", type=["json"])
            if uploaded_json and st.button("RESTORE"):
                try:
                    data = json.load(uploaded_json)
                    st.session_state['profiles'].update(data)
                    st.success("Database Restored.")
                    st.rerun()
                except: st.error("Invalid File.")

    st.divider()

    if st.session_state['profiles']:
        target = st.selectbox("Select Profile to Manage", list(st.session_state['profiles'].keys()))
        p_data = st.session_state['profiles'][target]
        
        with st.container(border=True):
            c_edit, c_sample = st.columns([1, 1])
            with c_edit:
                st.markdown("**Brand Rules**")
                new_rules = st.text_area("Edit Rules", p_data['rules'], height=400, label_visibility="collapsed")
            with c_sample:
                st.markdown("**Voice Sample Bank**")
                if p_data['samples']:
                    for i, s in enumerate(p_data['samples']):
                        with st.container(border=True):
                            c_a, c_b = st.columns([4,1])
                            with c_a: st.caption(f"[{s['type']}] {s['content'][:40]}...")
                            with c_b: 
                                if st.button("Del", key=f"m_del_{i}"):
                                    p_data['samples'].pop(i)
                                    st.rerun()
                else: st.caption("No samples attached.")

            c1, c2, c3 = st.columns(3)
            if c1.button("SAVE CHANGES", type="primary"): 
                st.session_state['profiles'][target]['rules'] = new_rules
                st.success("Saved.")
            if c2.button("DOWNLOAD PDF GUIDE"): 
                st.download_button("Download PDF", logic.create_pdf(target, new_rules), f"{target}_Guidelines.pdf")
            if c3.button("DELETE PROFILE"): 
                del st.session_state['profiles'][target]
                st.rerun()
    else:
        st.markdown('<div class="custom-warning">⚠️ No Profiles Found.</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown('<div class="footer">SIGNET v1.2 | POWERED BY CASTELLAN PR | ENTERPRISE CONFIDENTIAL</div>', unsafe_allow_html=True)
