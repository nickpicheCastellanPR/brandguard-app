import os
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF
import streamlit as st
from dotenv import load_dotenv

# Load env variables (for local testing)
load_dotenv()

class SignetLogic:
    def __init__(self):
        # 1. AUTH & CONFIG
        self.api_key = self._get_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _get_api_key(self):
        # Check Railway/System variables first
        if "GOOGLE_API_KEY" in os.environ:
            return os.environ["GOOGLE_API_KEY"]
        
        # If not found there, check local secrets file (for when you run on your laptop)
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
        
        st.error("API Key not found!")
        return None

    def check_password(self, input_password):
        CORRECT_PASSWORD = "beta" 
        return input_password == CORRECT_PASSWORD

    def get_model(self):
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

    def describe_logo(self, image):
        """Generates a technical description of an uploaded logo."""
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        prompt = """
        Describe this logo in technical detail for a Brand Guideline document.
        Focus on: Symbols, Colors, Layout, Vibe.
        Keep it concise (2-3 sentences).
        """
        try:
            response = model.generate_content([prompt, image])
            return response.text
        except Exception:
            return "Logo analysis failed."

    def analyze_social_post(self, image):
        """Analyzes a social media screenshot for best practices."""
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        prompt = """
        Analyze this social media screenshot.
        Identify the "Best Practices" used here (Formatting, Hook style, CTA).
        Summarize the "Social Style Signature" in 2 sentences.
        """
        try:
            response = model.generate_content([prompt, image])
            return response.text
        except:
            return "No social data extracted."

    def run_visual_audit(self, image, rules):
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        ### ROLE: Signet Compliance Engine.
        ### RULES: {rules}
        ### TASK: Audit image against guidelines.
        ### OUTPUT FORMAT:
        **STATUS:** [PASS / FAIL]
        **1. VISUAL IDENTITY:** [Pass/Fail]
        **2. TYPOGRAPHY:** [Pass/Fail]
        **3. VOICE & TONE:** [Pass/Fail]
        **REQUIRED FIXES:** [Bullets]
        """
        try:
            response = model.generate_content([prompt, image])
            return response.text
        except:
            return "Audit failed. Please try again."

    def run_copy_editor(self, text, rules):
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        ### ROLE: Senior Copy Editor.
        ### RULES: {rules}
        ### DRAFT: "{text}"
        ### TASK: Rewrite to match Brand Voice & Style Signature.
        ### OUTPUT:
        **1. CRITICAL EDITS:** [List]
        **2. POLISHED COPY:** [Rewrite]
        **3. STRATEGY NOTE:** [Rationale]
        """
        response = model.generate_content(prompt)
        return response.text

    def run_content_generator(self, topic, format_type, key_points, rules):
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        ### ROLE: Executive Ghost Writer.
        ### RULES: {rules}
        ### TASK: Write a {format_type} about "{topic}".
        ### POINTS: {key_points}
        ### INSTRUCTIONS: Strictly adhere to Archetype and Style Signature.
        """
        response = model.generate_content(prompt)
        return response.text

    def generate_brand_rules_from_pdf(self, pdf_text):
        # 1. Initialize variable to prevent "UnboundLocalError"
        response_text = ""
        
        parsing_prompt = f"""
        TASK: You are a Brand Strategy Architect. Analyze the raw text from a Brand Guidelines PDF and extract structured data.
        
        RAW CONTENT:
        {pdf_text[:50000]}
        
        INSTRUCTIONS:
        Return a VALID JSON object with the following keys. Do not include markdown formatting (like ```json), just the raw JSON string.
        
        REQUIRED JSON STRUCTURE:
        {{
            "wiz_name": "Extract the brand name",
            "wiz_archetype": "Infer the closest Archetype from this list: The Ruler, The Creator, The Sage, The Innocent, The Outlaw, The Magician, The Hero, The Lover, The Jester, The Everyman, The Caregiver, The Explorer",
            "wiz_tone": "Extract 3-5 keywords describing the tone (e.g. Professional, Witty)",
            "wiz_mission": "Extract the mission statement or purpose. If none, write a 1-sentence summary based on the text.",
            "wiz_values": "Extract core values (comma separated)",
            "wiz_guardrails": "Extract 'Don'ts' or negative constraints (e.g. 'Do not use jargon')",
            "palette_primary": ["#Hex1", "#Hex2"], 
            "palette_secondary": ["#Hex3", "#Hex4"],
            "writing_sample": "Extract a representative paragraph of copy to serve as a style sample."
        }}
        """
        
        try:
            # 2. Call the AI (Using standard Gemini syntax)
            response = self.model.generate_content(parsing_prompt)
            response_text = response.text
            
            # 3. Clean and Parse
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            
            import json
            data = json.loads(cleaned_text)
            return data
            
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            # Fallback: Return a partial object so the app doesn't crash
            return {
                "wiz_name": "New Brand (Extraction Failed)",
                "wiz_mission": f"Could not auto-extract due to error: {str(e)}",
                "raw_dump": response_text # Now safe to reference
            }
