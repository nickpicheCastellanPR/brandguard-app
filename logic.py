import os
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF
import streamlit as st
from dotenv import load_dotenv

# Load env variables (for local testing)
load_dotenv()

class BrandGuardLogic:
    def __init__(self):
        # 1. AUTH & CONFIG
        self.api_key = self._get_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _get_api_key(self):
        """Robust API Key Fetcher"""
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
        elif os.getenv("GOOGLE_API_KEY"):
            return os.getenv("GOOGLE_API_KEY")
        return None

    def check_password(self, input_password):
        """Simple Beta Gatekeeper"""
        # Hardcoded for MVP. In production, use st.secrets or a DB.
        CORRECT_PASSWORD = "beta" 
        return input_password == CORRECT_PASSWORD

    def get_model(self):
        """Silently finds the best Flash model"""
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
                    return m.name
            return 'models/gemini-1.5-flash'
        except:
            return 'models/gemini-1.5-flash'

    # --- CORE FUNCTIONS ---

    def extract_text_from_pdf(self, uploaded_file):
        try:
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"

    def create_pdf(self, brand_name, rules_text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Brand Guidelines: {brand_name}", ln=1, align='C')
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt=rules_text)
        return pdf.output(dest='S').encode('latin-1')

    # --- AI TASKS ---

    def run_visual_audit(self, image, rules):
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        ### ROLE: BrandGuard Compliance Officer.
        ### STRICT GUIDELINES:
        {rules}
        
        ### TASK:
        Audit the image against the guidelines. 
        
        ### CRITICAL INSTRUCTION ON COLORS:
        - Treat the Color Palette as a list of ALLOWED colors, not a list of REQUIRED colors.
        - A single asset (like a logo) does NOT need to use every color in the palette.
        - FAIL only if the image uses a dominant color that is NOT in the palette (e.g., using Red when only Blue is allowed).
        - If the image uses a subset of the allowed colors (e.g., only Blue and White), that is a PASS.
        
        ### OUTPUT FORMAT:
        **STATUS:** [PASS / FAIL]
        
        **1. 🎨 Visual Identity:** [Pass/Fail] - [Analyze if the colors used are VALID. Do not penalize for missing colors.]
        **2. 🔠 Typography:** [Pass/Fail] - [Analyze Fonts]
        **3. ✍️ Quality Check:** [Pass/Fail] - [Check for typos or grammar errors in the design]
        **4. 🗣️ Voice/Tone:** [Pass/Fail] - [Does the text match the brand voice?]
        
        **🔧 REQUIRED FIXES:**
        * [Actionable bullet points. Only list fixes for actual violations.]
        """
        response = model.generate_content([prompt, image])
        return response.text

    def run_copy_editor(self, text, rules):
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        ### ROLE: Senior Copy Editor.
        ### BRAND RULES:
        {rules}
        
        ### DRAFT TEXT:
        "{text}"
        
        ### TASK:
        1. Correct all spelling/grammar.
        2. Rewrite the text to strictly match the Brand Voice defined above.
        
        ### OUTPUT:
        **1. 🔴 Edits Made:** [List errors]
        **2. 🟢 Polished Copy:** [ The Rewrite ]
        **3. 💡 Strategy Note:** [Why this fits better]
        """
        response = model.generate_content(prompt)
        return response.text

def generate_brand_rules(self, inputs):
        """Inputs is a string prompt constructed in the UI"""
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        
        # We wrap the user's input in a strict "Grounding System Prompt"
        grounded_prompt = f"""
        ### ROLE: Brand Strategist.
        ### TASK: Create a brand guideline document based STRICTLY on the user's provided inputs.
        
        ### USER INPUTS:
        {inputs}
        
        ### CRITICAL INSTRUCTIONS:
        1. **NO OUTSIDE KNOWLEDGE:** Do not use external facts. If the brand name matches a famous company (e.g., "Starbucks" or "Pizza Planet"), IGNORE the real-world brand. Only use the attributes provided in the inputs.
        2. **NO HALLUCINATION:** If the user did not specify a font name, do not invent one (like "SpaceAge"). Instead, prescribe a category (e.g., "Fun, thick display font").
        3. **NO INVENTED LOGOS:** Do not describe a logo (like "Rocket Ship") unless the user explicitly described it. If not described, set the rule as "Logo must be clear and legible."
        
        ### OUTPUT FORMAT:
        Produce a standard 4-point rule block (Colors, Typography, Logo, Voice).
        """
        
        response = model.generate_content(grounded_prompt)
        return response.text
