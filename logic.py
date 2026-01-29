import os
import streamlit as st
import google.generativeai as genai
import json

class SignetLogic:
    def __init__(self):
        # 1. AUTH & CONFIG
        self.api_key = self._get_api_key()
        
        # 2. INITIALIZE MODEL (Simplified to prevent startup timeouts)
        # We default to Flash directly to avoid calling the API during startup
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                print(f"Model Init Warning: {e}")

    def _get_api_key(self):
        # Safe environment loading (Import inside function)
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        # Check Railway/System variables
        if "GOOGLE_API_KEY" in os.environ:
            return os.environ["GOOGLE_API_KEY"]
        
        if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
        
        if "GEMINI_API_KEY" in os.environ:
             return os.environ["GEMINI_API_KEY"]

        return None

    def check_password(self, input_password):
        return input_password == "beta" 

    def get_model(self):
        return 'models/gemini-1.5-flash'

    # --- PDF & INGESTION FUNCTIONS (With Lazy Imports) ---

    def extract_text_from_pdf(self, uploaded_file):
        """Helper to pull raw string data from a PDF file object"""
        # LAZY IMPORT: Only loads pypdf when this specific function is called
        try:
            import pypdf
        except ImportError:
            return "Error: 'pypdf' library is missing. Check requirements.txt."

        try:
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"

    def create_pdf(self, brand_name, rules_text):
        # LAZY IMPORT
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
            # Call the model
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
                "wiz_archetype": "The Sage", 
                "raw_dump": response_text
            }

    # --- AI VISION & TEXT TASKS ---

    def describe_logo(self, image):
        if not self.model: return "AI not ready."
        try:
            prompt = "Describe this logo in technical detail. Focus on Symbols, Colors, Vibe."
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception:
            return "Logo analysis failed."

    def analyze_social_post(self, image):
        if not self.model: return "AI not ready."
        try:
            prompt = "Analyze this social post. Identify Best Practices and Social Style Signature."
            response = self.model.generate_content([prompt, image])
            return response.text
        except:
            return "No social data extracted."

    def run_visual_audit(self, image, rules):
        if not self.model: return "AI not ready."
        prompt = f"""
        ### ROLE: Signet Compliance Engine.
        ### RULES: {rules}
        ### TASK: Audit image against guidelines.
        """
        try:
            response = self.model.generate_content([prompt, image])
            return response.text
        except:
            return "Audit failed."

    def run_copy_editor(self, text, rules):
        if not self.model: return "AI not ready."
        prompt = f"""
        ### ROLE: Senior Copy Editor.
        ### RULES: {rules}
        ### DRAFT: "{text}"
        ### TASK: Rewrite to match Brand Voice.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {e}"

    def run_content_generator(self, topic, format_type, key_points, rules):
        if not self.model: return "AI not ready."
        prompt = f"""
        ### ROLE: Executive Ghost Writer.
        ### RULES: {rules}
        ### TASK: Write a {format_type} about "{topic}".
        ### POINTS: {key_points}
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {e}"
