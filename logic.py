import os
import streamlit as st
import google.generativeai as genai
import pypdf
import io
import json
from fpdf import FPDF
from dotenv import load_dotenv

# Load env variables (for local testing)
load_dotenv()

class SignetLogic:
    def __init__(self):
        # 1. AUTH & CONFIG
        self.api_key = self._get_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
        # 2. INITIALIZE MODEL (THE FIX)
        # We must define self.model here so other functions can use it.
        model_name = self.get_model()
        self.model = genai.GenerativeModel(model_name)

    def _get_api_key(self):
        # Check Railway/System variables first
        if "GOOGLE_API_KEY" in os.environ:
            return os.environ["GOOGLE_API_KEY"]
        
        # If not found there, check local secrets file (for local dev)
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
        
        # Fallback to internal/Railway variable name if distinct
        if "GEMINI_API_KEY" in os.environ:
             return os.environ["GEMINI_API_KEY"]

        st.error("API Key not found! Please check your Railway variables.")
        return None

    def check_password(self, input_password):
        # Simple auth for prototype
        CORRECT_PASSWORD = "beta" 
        return input_password == CORRECT_PASSWORD

    def get_model(self):
        # Helper to find the best available model
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
                    return m.name
            return 'models/gemini-1.5-flash'
        except:
            return 'models/gemini-1.5-flash'

    # --- PDF & INGESTION FUNCTIONS ---

    def extract_text_from_pdf(self, uploaded_file):
        """Helper to pull raw string data from a PDF file object"""
        try:
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
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

    def generate_brand_rules_from_pdf(self, pdf_text):
        """Analyzes PDF text and returns a Structured JSON object for the Wizard"""
        
        # Initialize safe fallback
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
            # Call the model defined in __init__
            response = self.model.generate_content(parsing_prompt)
            response_text = response.text
            
            # Clean and Parse JSON
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_text)
            return data
            
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            # Fallback object so app doesn't crash
            return {
                "wiz_name": "New Brand (Extraction Failed)",
                "wiz_mission": f"Could not auto-extract. Error: {str(e)}",
                "wiz_archetype": "The Sage", # Default
                "raw_dump": response_text
            }

    # --- AI VISION & TEXT TASKS ---

    def describe_logo(self, image):
        """Generates a technical description of an uploaded logo."""
        prompt = """
        Describe this logo in technical detail for a Brand Guideline document.
        Focus on: Symbols, Colors, Layout, Vibe.
        Keep it concise (2-3 sentences).
        """
        try:
            # Uses self.model from __init__
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception:
            return "Logo analysis failed."

    def analyze_social_post(self, image):
        """Analyzes a social media screenshot for best practices."""
        prompt = """
        Analyze this social media screenshot.
        Identify the "Best Practices" used here (Formatting, Hook style, CTA).
        Summarize the "Social Style Signature" in 2 sentences.
        """
        try:
            response = self.model.generate_content([prompt, image])
            return response.text
        except:
            return "No social data extracted."

    def run_visual_audit(self, image, rules):
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
            response = self.model.generate_content([prompt, image])
            return response.text
        except:
            return "Audit failed. Please try again."

    def run_copy_editor(self, text, rules):
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
        response = self.model.generate_content(prompt)
        return response.text

    def run_content_generator(self, topic, format_type, key_points, rules):
        prompt = f"""
        ### ROLE: Executive Ghost Writer.
        ### RULES: {rules}
        ### TASK: Write a {format_type} about "{topic}".
        ### POINTS: {key_points}
        ### INSTRUCTIONS: Strictly adhere to Archetype and Style Signature.
        """
        response = self.model.generate_content(prompt)
        return response.text
