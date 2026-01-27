import os
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF
import streamlit as st
from dotenv import load_dotenv

# Load env variables
load_dotenv()

class SignetLogic:
    def __init__(self):
        self.api_key = self._get_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _get_api_key(self):
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
        elif os.getenv("GOOGLE_API_KEY"):
            return os.getenv("GOOGLE_API_KEY")
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
            
    def extract_text_from_image(self, image):
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        prompt = "Transcribe all the text in this image exactly as written."
        try:
            response = model.generate_content([prompt, image])
            return response.text
        except:
            return ""

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
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        prompt = "Describe this logo in technical detail for a Brand Guideline document. Focus on symbols, colors, layout, and vibe. Concise."
        try:
            response = model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            return "Logo analysis failed."

    def run_visual_audit(self, image, rules):
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        ### ROLE: Signet Compliance Engine.
        ### STRICT GUIDELINES:
        {rules}
        ### TASK: Audit the image against the guidelines.
        ### OUTPUT FORMAT:
        **STATUS:** [PASS / FAIL]
        **1. VISUAL IDENTITY:** [Pass/Fail]
        **2. TYPOGRAPHY:** [Pass/Fail]
        **3. QUALITY CHECK:** [Pass/Fail]
        **4. VOICE & TONE:** [Pass/Fail]
        **REQUIRED FIXES:** [Bullets]
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
        ### TASK: Correct spelling/grammar and rewrite to strictly match the Brand Voice.
        ### OUTPUT:
        **1. CRITICAL EDITS:**
        **2. POLISHED COPY:**
        **3. STRATEGY NOTE:**
        """
        response = model.generate_content(prompt)
        return response.text

    def run_content_generator(self, topic, format_type, key_points, audience, rules, samples=[]):
        """
        Generates content.
        samples: List of dicts [{'type': 'Internal', 'content': '...'}]
        """
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        
        # Filter samples to find relevant ones (Context-Aware)
        relevant_samples = ""
        if samples:
            # Simple keyword matching for context
            matches = [s['content'] for s in samples if s['type'].lower() in format_type.lower()]
            if not matches:
                # If no exact match, use all samples for tone
                matches = [s['content'] for s in samples]
            
            relevant_samples = "\n---\n".join(matches[:3]) # Limit to top 3 to avoid token overflow

        prompt = f"""
        ### ROLE: Executive Ghost Writer.
        ### BRAND RULES:
        {rules}
        
        ### REFERENCE VOICE SAMPLES (Mimic this specific tone):
        {relevant_samples}
        
        ### TASK: Write a {format_type} about "{topic}".
        ### TARGET AUDIENCE: {audience}
        ### KEY DETAILS:
        {key_points}
        ### INSTRUCTIONS:
        1. Adhere to Brand Voice/Archetype.
        2. Use standard formatting for {format_type}.
        3. Expand bullets into prose.
        ### OUTPUT:
        [Generate text]
        """
        response = model.generate_content(prompt)
        return response.text
        
    def run_social_assistant(self, platform, topic, image, rules):
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        inputs = [f"""
        ### ROLE: Social Media Manager.
        ### BRAND RULES:
        {rules}
        ### PLATFORM: {platform}
        ### TOPIC: {topic}
        ### TASK: Write caption & hashtags.
        """]
        if image: inputs.append(image)
        response = model.generate_content(inputs)
        return response.text

    def generate_brand_rules(self, inputs):
        model_name = self.get_model()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(f"""
        ### ROLE: Brand Strategist.
        ### TASK: Create brand guidelines.
        ### INPUTS: {inputs}
        ### FORMAT:
           1. STRATEGY (Mission, Values, Archetype)
           2. COLOR PALETTE
           3. TYPOGRAPHY
           4. LOGO RULES
           5. VOICE & TONE (Analyze provided samples for style signature)
        """)
        return response.text
