import google.generativeai as genai
import os
import json
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

# --- CONFIG ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- 1. BIOMETRIC EYE (Math Engine) ---
def rgb_to_hex(rgb):
    """Converts a tuple (R, G, B) to HEX string."""
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def extract_dominant_colors(image, num_colors=5):
    """
    Mathematically extracts the top N dominant colors from an image using K-Means Clustering.
    Returns a list of HEX codes.
    """
    try:
        # Resize image for speed (don't process 4k pixels)
        image = image.resize((150, 150))
        img_array = np.array(image)
        
        # Reshape to a list of pixels (Height * Width, 3 RGB channels)
        pixels = img_array.reshape(-1, 3)
        
        # Use K-Means Clustering to find "centers" of color groups
        kmeans = KMeans(n_clusters=num_colors, n_init=10)
        kmeans.fit(pixels)
        
        # Get the dominant colors and convert to HEX
        colors = kmeans.cluster_centers_
        hex_colors = [rgb_to_hex(color) for color in colors]
        return hex_colors
        
    except Exception as e:
        print(f"Color Extraction Error: {e}")
        return []

# --- 2. MAIN LOGIC CLASS ---
class SignetLogic:
    def __init__(self):
        # Using Flash for speed/cost, Pro for depth if needed
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def run_visual_audit(self, image, profile_text):
        """
        THE JUDGE: Scans image, compares to profile, returns Score + Analysis.
        """
        # A. MATHEMATICAL COLOR SCAN
        hex_codes = extract_dominant_colors(image)
        hex_str = ", ".join(hex_codes)
        
        # B. AI VIBE CHECK & SCORING
        prompt = f"""
        ROLE: Chief Brand Officer.
        TASK: Audit this image against the Brand Profile.
        
        BRAND PROFILE:
        {profile_text}
        
        EVIDENCE (MATHEMATICAL):
        - DOMINANT HEX CODES FOUND IN IMAGE: {hex_str}
        
        OUTPUT FORMAT:
        Return a PURE JSON object (no markdown, no extra text) with these keys:
        - "score": (Integer 0-100 based on strictness. 100 = Perfect Match).
        - "verdict": (String) "COMPLIANT", "NON-COMPLIANT", or "NEEDS REVIEW".
        - "color_analysis": (String) Specific analysis of the Hex codes found vs. the Approved Palette.
        - "style_analysis": (String) Analysis of the visual style/archetype match.
        - "recommendations": (List of Strings) 3 actionable bullet points to fix or improve.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            # Clean response to ensure valid JSON
            txt = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(txt)
        except Exception as e:
            # Fallback if AI fails to generate valid JSON
            return {
                "score": 0,
                "verdict": "ERROR",
                "color_analysis": f"AI Parsing Error: {e}",
                "style_analysis": "N/A",
                "recommendations": ["Please try again."]
            }

    # --- WIZARD & PDF TOOLS (Preserved) ---
    def extract_text_from_pdf(self, uploaded_file):
        import PyPDF2
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"

    def generate_brand_rules_from_pdf(self, pdf_text):
        """Extracts structured brand data from raw PDF text."""
        prompt = f"""
        TASK: Extract Brand Rules from this PDF text.
        OUTPUT: Return a JSON object (no markdown) with these exact keys: 
        wiz_name, wiz_archetype, wiz_mission, wiz_values, wiz_tone, wiz_guardrails, palette_primary (list of hex), palette_secondary (list of hex), writing_sample.
        
        RAW TEXT: 
        {pdf_text[:15000]}
        """
        try:
            response = self.model.generate_content(prompt)
            cleaned = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            # Fallback for empty extraction
             return {
                 "wiz_name": "Extracted Brand", 
                 "wiz_mission": "Could not extract.",
                 "palette_primary": ["#000000"],
                 "writing_sample": pdf_text[:500]
             }

    def generate_brand_rules(self, prompt_text):
        """Standard text generation helper"""
        response = self.model.generate_content(prompt_text)
        return response.text

    # --- COPY EDITOR & GENERATOR (Preserved) ---
    def run_copy_editor(self, user_draft, profile_text):
        """Rewrites text to match voice."""
        prompt = f"Rewrite this draft to match the brand voice:\n\nBRAND RULES:\n{profile_text}\n\nDRAFT:\n{user_draft}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating copy: {e}"

    def run_content_generator(self, topic, format_type, key_points, profile_text):
        """Generates fresh content."""
        prompt = f"Create a {format_type} about {topic}. Key points: {key_points}.\n\nBRAND RULES:\n{profile_text}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating content: {e}"
    
    def analyze_social_post(self, image):
        """Simple image analysis for captions."""
        try:
            response = self.model.generate_content(["Analyze this social post and suggest a caption.", image])
            return response.text
        except Exception as e:
            return "Error analyzing image."
