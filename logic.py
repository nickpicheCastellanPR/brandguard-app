import google.generativeai as genai
import os
import json
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import io

# --- CONFIG ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- 1. BIOMETRIC EYE (Math Engine) ---
def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def extract_dominant_colors(image, num_colors=5):
    """Uses K-Means clustering to find exact hex codes."""
    try:
        # Resize for speed
        image = image.resize((150, 150))
        img_array = np.array(image)
        pixels = img_array.reshape(-1, 3)
        
        kmeans = KMeans(n_clusters=num_colors, n_init=10)
        kmeans.fit(pixels)
        
        colors = kmeans.cluster_centers_
        return [rgb_to_hex(c) for c in colors]
    except Exception as e:
        print(f"Color Error: {e}")
        return []

# --- 2. MAIN LOGIC ---
class SignetLogic:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def run_visual_audit(self, image, profile_text):
        """
        The Judge: Scans image, compares to profile, returns Score + Analysis.
        """
        # A. Math Check
        hex_codes = extract_dominant_colors(image)
        hex_str = ", ".join(hex_codes)
        
        # B. AI Vibe Check
        prompt = f"""
        ROLE: Chief Brand Officer.
        TASK: Audit this image against the Brand Profile.
        
        BRAND PROFILE:
        {profile_text}
        
        DETECTED HEX CODES (Mathematical):
        {hex_str}
        
        OUTPUT FORMAT:
        Return a strict JSON object (no markdown formatting) with these keys:
        - "score": (Integer 0-100)
        - "verdict": (String) "COMPLIANT" or "NON-COMPLIANT" or "NEEDS REVIEW"
        - "color_analysis": (String) Review of the hex codes vs brand palette.
        - "style_analysis": (String) Review of the vibe/archetype.
        - "recommendations": (List of Strings) Bullet points on how to fix it.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            # Clean response
            txt = response.text.replace("```json", "").replace("```", "")
            return json.loads(txt)
        except:
            return {
                "score": 0,
                "verdict": "ERROR",
                "color_analysis": "AI could not process.",
                "style_analysis": "N/A",
                "recommendations": ["Try again."]
            }

    # (Keep your existing PDF extraction/Wizard functions below if they were working well, 
    #  or I can provide the full file if you prefer.)
    # ... [Rest of logic.py placeholders] ...
    
    def extract_text_from_pdf(self, file):
        import PyPDF2
        reader = PyPDF2.PdfReader(file)
        return "".join([p.extract_text() for p in reader.pages])

    def generate_brand_rules_from_pdf(self, text):
        # ... (Use previous JSON extractor) ...
        pass
