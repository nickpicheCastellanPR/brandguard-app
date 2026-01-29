import os
import streamlit as st
import google.generativeai as genai
import json

class SignetLogic:
    def __init__(self):
        # 1. AUTH & CONFIG
        self.api_key = self._get_api_key()
        
        # 2. INITIALIZE MODEL
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # FIX: Switched to 'gemini-pro' (Stable) instead of 'gemini-1.5-flash'
                self.model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                print(f"Model Init Warning: {e}")

    def _get_api_key(self):
        # Safe environment loading
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        if "GOOGLE_API_KEY" in os.environ: return os.environ["GOOGLE_API_KEY"]
        if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets: return st.secrets["GOOGLE_API_KEY"]
        if "GEMINI_API_KEY" in os.environ: return os.environ["GEMINI_API_KEY"]
        return None

    def check_password(self, input_password):
        return input_password == "beta" 

    def get_model(self):
        # FIX: Fallback to 'models/gemini-pro'
        return 'models/gemini-pro'

    # --- PDF & INGESTION FUNCTIONS ---

    def extract_text_from_pdf(self, uploaded_file):
        try:
            import pypdf
        except ImportError:
            return "Error: 'pypdf' library is missing."

        try:
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"

    def create_pdf(self, brand_name, rules_text):
        try:
            from fpdf import FPDF
        except ImportError:
            return b"Error: 'fpdf' library is missing."

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Brand Guidelines: {brand_name}", ln=1, align='C')
            pdf.ln(10)
            pdf.multi_cell(0, 10, txt=rules_text)
            return pdf.output(dest='S').encode('latin-1')
        except Exception as e:
            return str(e).encode()

    def generate_brand_rules_from_pdf(self, pdf_text):
        """Analyzes PDF text and returns a Structured JSON object for the Wizard"""
        if not self.model:
            return {"wiz_name": "Error", "wiz_mission": "AI Model not connected."}

        # Initialize variable so it exists if the Try block fails
        response_text = ""
        import re
        
        parsing_prompt = f"""
        TASK: You are a Brand Strategy Architect. Analyze the raw text from a Brand Guidelines PDF and extract structured data.
        
        RAW CONTENT:
        {pdf_text[:50000]}
        
        INSTRUCTIONS:
        Return a VALID JSON object. Do not include markdown formatting.
        
        REQUIRED JSON STRUCTURE:
        {{
            "wiz_name": "Brand Name",
            "wiz_archetype": "The Sage",
            "wiz_tone": "Tone keywords",
            "wiz_mission": "Mission statement",
            "wiz_values": "Values",
            "wiz_guardrails": "Do's and Don'ts",
            "palette_primary": ["#000000"], 
            "palette_secondary": ["#ffffff"],
            "writing_sample": "Sample text"
        }}
        """
        
        try:
            # Call the model
            response = self.model.generate_content(parsing_prompt)
            response_text = response.text
            
            # Robust JSON Parsing
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            
            if json_match:
                clean_json = json_match.group(0)
                data = json.loads(clean_json)
                return data
            else:
                raise ValueError("No JSON object found in AI response")
            
        except Exception as e:
            print(f"Extraction Error: {e}")
            return {
                "wiz_name": "Extraction Failed",
                "wiz_mission": f"Error: {str(e)} \n\nRaw Output: {response_text[:100]}...",
                "wiz_archetype": "The Sage"
            }

    # --- AI VISION & TEXT TASKS ---

    def describe_logo(self, image):
        if not self.model: return "AI not ready."
        try:
            prompt = "Describe this logo in technical detail."
            # gemini-pro is text-only. If you need image analysis, we need gemini-pro-vision
            # But for stability, let's keep it simple for now or use a try/except switch
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception:
            return "Logo analysis failed (Model may not support images)."

    def analyze_social_post(self, image):
        if not self.model: return "AI not ready."
        try:
            prompt = "Analyze this social post."
            response = self.model.generate_content([prompt, image])
            return response.text
        except:
            return "No social data extracted."

    def run_visual_audit(self, image, rules):
        if not self.model: return "AI not ready."
        prompt = f"Audit image against rules: {rules}"
        try:
            response = self.model.generate_content([prompt, image])
            return response.text
        except:
            return "Audit failed."

    def run_copy_editor(self, text, rules):
        if not self.model: return "AI not ready."
        prompt = f"Rewrite this text: '{text}' using rules: {rules}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {e}"

    def run_content_generator(self, topic, format_type, key_points, rules):
        if not self.model: return "AI not ready."
        prompt = f"Write a {format_type} about {topic} using rules: {rules}. Points: {key_points}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {e}"
