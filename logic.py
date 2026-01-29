import os
import streamlit as st
import google.generativeai as genai
import json
import re

class SignetLogic:
    def __init__(self):
        # 1. AUTH & CONFIG
        self.api_key = self._get_api_key()
        
        # 2. DYNAMIC MODEL INITIALIZATION
        # We don't hardcode the name anymore. We find what's available.
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                
                # AUTO-DISCOVERY: Pick the best model you actually have access to
                model_name = self._auto_select_model()
                print(f"✅ CONNECTED TO MODEL: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                
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

    def _auto_select_model(self):
        """Finds the best available model to prevent 404 errors."""
        try:
            # Get all models your API key can see
            available = list(genai.list_models())
            
            # Priority 1: 1.5 Flash (Best for speed & long PDFs)
            for m in available:
                if 'generateContent' in m.supported_generation_methods and 'flash' in m.name and '1.5' in m.name:
                    return m.name
            
            # Priority 2: 1.5 Pro (Best for reasoning)
            for m in available:
                if 'generateContent' in m.supported_generation_methods and 'pro' in m.name and '1.5' in m.name:
                    return m.name
                    
            # Priority 3: Gemini Pro (Legacy 1.0)
            for m in available:
                if 'generateContent' in m.supported_generation_methods and 'pro' in m.name:
                    return m.name

            # Fallback: Just take the first one that generates text
            for m in available:
                if 'generateContent' in m.supported_generation_methods:
                    return m.name
                    
            return 'models/gemini-1.5-flash' # Absolute fallback
            
        except Exception as e:
            print(f"Auto-Discovery Failed: {e}")
            return 'models/gemini-1.5-flash'

    def check_password(self, input_password):
        return input_password == "beta" 

    # --- PDF & INGESTION FUNCTIONS ---

    def extract_text_from_pdf(self, uploaded_file):
        """Helper to pull raw string data from a PDF file object"""
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
            # Call the auto-selected model
            response = self.model.generate_content(parsing_prompt)
            response_text = response.text
            
            # ROBUST JSON PARSING (Regex Hunter)
            # Finds the first '{' and last '}' to ignore conversational fluff
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
    # These also use self.model now for simplicity and stability.
    
    def describe_logo(self, image):
        if not self.model: return "AI not ready."
        try:
            prompt = "Describe this logo in technical detail. Focus on Symbols, Colors, Vibe."
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception:
            # Graceful fallback if the selected model is Text-Only
            return "Logo analysis unavailable (Model does not support images)."

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
