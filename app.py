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

# --- SVG ICON LIBRARY (Color Updated to Castellan Blue for Light Sidebar) ---
def get_svg_icon(name):
    # Castellan Blue: #24363b
    icons = {
        "dashboard": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#24363b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>''',
        "eye": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#24363b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>''',
        "pen": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#24363b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>''',
        "share": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#24363b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>''',
        "architect": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#24363b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 22h20"></path><path d="M12 2v20"></path><path d="M2 12h20"></path><path d="M12 2L2 22h20L12 2z"></path></svg>''',
        "upload": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#24363b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>''',
        "manage": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#24363b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>'''
    }
    return icons.get(name, "")

# --- PREMIUM CSS OVERHAUL (V5.0 - HYBRID THEME) ---
st.markdown("""
<style>
    /* 1. GLOBAL FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* 2. SIDEBAR STYLING (The Cream Panel) */
    /* Forces the sidebar to Castellan Cream (#f5f5f0) */
    section[data-testid="stSidebar"] {
        background-color: #f5f5f0 !important;
        border-right: 1px solid #dcdcd9;
    }
    
    /* Sidebar Text Elements - Forced to Castellan Blue (#24363b) */
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div {
        color: #24363b !important;
    }
    
    /* Logo Container - No background needed now because sidebar is light! */
    section[data-testid="stSidebar"] [data-testid="stImage"] {
        background: transparent;
        padding: 0px;
        border: none;
        box-shadow: none;
    }

    /* NAVIGATION MENU (Hybrid Style) */
    div[role="radiogroup"] > label > div:first-of-type {display: None;}
    div[role="radiogroup"] label {
        padding: 12px 15px;
        border-radius: 6px;
        margin-bottom: 6px;
        border: 1px solid transparent;
        transition: all 0.2s ease;
        color: #5c6b61 !important; /* Sage Green for inactive */
        font-weight: 500;
        cursor: pointer;
    }
    div[role="radiogroup"] label:hover {
        background: #e6e6e1; /* Slightly darker cream */
        color: #24363b !important; /* Blue on hover */
        border-left: 3px solid #ab8f59; /* Gold accent */
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background: #FFFFFF;
        color: #24363b !important; /* Blue active */
        border-left: 4px solid #24363b; /* Blue accent */
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        font-weight: 600;
    }

    /* 3. MAIN APP AREA (The Dark Workspace) */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #0E1117 !important; /* Deep Dark */
        color: #E0E0E0 !important;
    }
    
    /* 4. INPUT FIELD NORMALIZER (The Edge Fix) */
    /* Aggressively targets all inputs to force Dark Mode styling */
    input, textarea, select, div[data-baseweb="select"] > div {
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        border-radius: 6px !important;
    }
    /* Focus States */
    input:focus, textarea:focus, div[data-baseweb="select"] > div:focus-within {
        border-color: #ab8f59 !important; /* Gold Focus */
        box-shadow: 0 0 0 1px #ab8f59 !important;
    }
    /* Placeholder Text */
    ::placeholder { color: #666 !important; opacity: 1; }
    
    /* Fix specific Streamlit input wrappers */
    .stTextInput > div > div { background-color: #1A1A1A !important; }
    .stTextArea > div > div { background-color: #1A1A1A !important; }
    
    /* 5. CARDS & CONTAINERS (Castellan Blue) */
    div[data-testid="stMetric"], div[data-testid="stVerticalBlock"] > [style*="border"] {
        background-color: #24363b !important; /* Brand Blue Background */
        border: 1px solid #354a50 !important;
    }
    
    /* 6. BUTTONS (Gold Action) */
    .stButton>button {
        background-color: #ab8f59; /* Gold */
        color: #000; /* Black Text */
        border: none;
        border-radius: 4px;
        height: 3em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #c4a76a; 
        color: #000;
        box-shadow: 0px 4px 12px rgba(171, 143, 89, 0.4); 
    }
    .stButton>button:active {
        background-color: #967d4d;
        color: #fff;
    }

    /* 7. UTILITIES */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #24363b; /* Blue Footer */
        color: #ab8f59; /* Gold Text */
        text-align: right;
        padding: 10px 30px;
        font-size: 11px;
        border-top: 1px solid #354a50;
        z-index: 999;
        letter-spacing: 1px;
    }
    .block-container { padding-bottom: 80px; }
    
    /* Warning Box */
    .custom-warning {
        background-color: #24363b;
        border-left: 4px solid #ab8f59;
        padding: 20px;
        border-radius: 4px;
        color: #fff;
        margin-bottom: 20px;
    }
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
        if os.path.exists("Signet_Logo_Color.png"): 
            st.image("Signet_Logo_Color.png", width=300) 
        else: 
            # Fallback text needs to be visible on Dark Background
            st.markdown("<h1 style='text-align: center; color: #ab8f59; letter-spacing: 5px;'>SIGNET</h1>", unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; color: #888; font-size: 0.9rem; margin-top: -10px;'>ENTERPRISE BRAND GOVERNANCE</p><br>", unsafe_allow_html=True)
        
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
    # Logo sits natively on Cream background
    if os.path.exists("Signet_Logo_Color.png"): 
        st.image("Signet_Logo_Color.png", use_container_width=True)
    else: 
        st.header("SIGNET")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # NAVIGATION
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
    
    # Progress Bar (Custom Colors needed via Streamlit Theme or just accept default)
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
                st.markdown(f"{get_svg_icon('architect')} &nbsp; <strong>Architect New Profile</strong>", unsafe_allow_html=True)
                st.caption("Define mission, voice, and visuals from scratch.")
                if st.button("Launch Wizard"): 
                    st.info("Select 'Brand Architect' from the sidebar.")
        with c2:
             with st.container(border=True):
                st.markdown(f"{get_svg_icon('upload')} &nbsp; <strong>Import Guidelines</strong>", unsafe_allow_html=True)
                st.caption("Extract rules directly from an existing PDF.")
                if st.button("Upload PDF"):
                    st.info("Select 'Brand Architect' -> 'PDF Extraction'.")
    else:
        st.subheader("Quick Actions")
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True):
                st.markdown(f"{get_svg_icon('eye')} &nbsp; <strong>Visual Audit</strong>", unsafe_allow_html=True)
                st.caption("Validate creative assets.")
        with c2:
            with st.container(border=True):
                st.markdown(f"{get_svg_icon('pen')} &nbsp; <strong>Ghost Writer</strong>", unsafe_allow_html=True)
                st.caption("Draft executive comms.")
        with c3:
            with st.container(border=True):
                st.markdown(f"{get_svg_icon('share')} &nbsp; <strong>Social Strategy</strong>", unsafe_allow_html=True)
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
