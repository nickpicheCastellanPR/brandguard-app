import google.generativeai as genai
import os
import json
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter

# --- CONFIG ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- 1. COLOR MATH ENGINE (THE BIOMETRIC EYE) ---
def rgb_to_hex(rgb):
    """Converts a tuple (R, G, B) to HEX string."""
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def extract_dominant_colors(image, num_colors=5):
    """
    Mathematically extracts the top N dominant colors from an image.
    Returns a list of HEX codes.
    """
    try:
        # 1. Resize image for speed (don't process 4k pixels)
        image = image.resize((150, 150))
        img_array = np.array(image)
        
        # 2. Reshape to a list of pixels
        # (Height * Width, 3 RGB channels)
        pixels = img_array.reshape(-1, 3)
        
        # 3. Use K-Means Clustering to find "centers" of color groups
        kmeans = KMeans(n_clusters=num_colors, n_init=10)
        kmeans.fit(pixels)
        
        # 4. Get the dominant colors
        colors = kmeans.cluster_centers_
        
        # 5. Convert to HEX
        hex_colors = [rgb_to_hex(color) for color in colors]
        return hex_colors
        
    except Exception as e:
        print(f"Color Extraction Error: {e}")
        return []

# --- 2. MAIN LOGIC CLASS ---
class SignetLogic:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def extract_text_from_pdf(self, uploaded_file):
        """Extracts raw text from PDF for the Ingest module."""
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
        """
        AI Analyst: Reads raw PDF text and structures it into the Signet Profile format.
        """
        prompt = f"""
        TASK: You are a Senior Brand Strategist. Analyze this raw text from a Brand Guidelines PDF.
        
        OUTPUT: Return a purely valid JSON object with these keys:
        - "wiz_name": (String) Brand Name
        - "wiz_archetype": (String) One of: The Ruler, The Creator, The Sage, The Innocent, The Outlaw, The Magician, The Hero, The Lover, The Jester, The Everyman, The Caregiver, The Explorer. (Pick the closest fit).
        - "wiz_mission": (String) Mission statement found.
        - "wiz_values": (String) Core values found.
        - "wiz_tone": (String) Tone of voice keywords (comma separated).
        - "wiz_guardrails": (String) Do's and Don'ts found.
        - "palette_primary": (List of Strings) Hex codes found (e.g. ["#24363b"]). If none, guess based on descriptions.
        - "palette_secondary": (List of Strings) Secondary hex codes.
        - "writing_sample": (String) A representative paragraph of text from the document to use as a voice sample.

        RAW TEXT:
        {pdf_text[:15000]}
        """
        try:
            response = self.model.generate_content(prompt)
            cleaned = response.text.replace("```json", "").replace("```", "")
            return json.loads(cleaned)
        except Exception as e:
            # Fallback if JSON fails
            return {
                "wiz_name": "New Brand",
                "wiz_archetype": "The Sage", 
                "wiz_mission": "Error extracting mission.",
                "wiz_values": "Error extracting values.",
                "palette_primary": ["#000000"]
            }

    def generate_brand_rules(self, prompt_text):
        """Generates the Master Text Profile from the Wizard inputs."""
        response = self.model.generate_content(prompt_text)
        return response.text

    def run_visual_audit(self, image, profile_text):
        """
        THE JUDGE: Compares the image against the Brand Profile.
        NOW POWERED BY BIOMETRICS.
        """
        # 1. MATHEMATICALLY EXTRACT COLORS
        detected_hexes = extract_dominant_colors(image)
        hex_str = ", ".join(detected_hexes)
        
        # 2. CONSTRUCT THE EVIDENCE
        prompt = f"""
        ROLE: You are the Chief Brand Officer. You are auditing a creative asset for strict compliance.
        
        EVIDENCE A: THE BRAND RULES
        {profile_text}
        
        EVIDENCE B: THE ASSET DATA
        - The image has been mathematically analyzed.
        - DOMINANT HEX CODES FOUND: {hex_str}
        
        TASK:
        1. Compare the 'Dominant Hex Codes' found in the image against the 'Palette' in the Brand Rules.
        2. Are they close? (Note: Lighting can shift hex codes slightly, so allow for minor variance, but flag obvious mismatches).
        3. Analyze the Style/Vibe of the image. Does it match the Archetype?
        4. Check for Logo usage (if visible).
        
        OUTPUT FORMAT (Markdown):
        ### 🚨 COMPLIANCE REPORT
        **Pass/Fail Status**
        
        **1. COLOR FORENSICS**
        * **Detected:** `{hex_str}`
        * **Verdict:** [Explain if these match the approved palette. Be specific.]
        
        **2. STYLE & ARCHETYPE**
        * [Analysis of the visual vibe vs the brand voice]
        
        **3. RECOMMENDATION**
        * [Actionable advice to fix or approve]
        """
        
        # 3. CALL THE AI JUDGE
        response = self.model.generate_content([prompt, image])
        return response.text

    def run_copy_editor(self, user_draft, profile_text):
        """Rewrites text to match the brand voice."""
        prompt = f"""
        ROLE: You are an Executive Ghostwriter.
        GOAL: Rewrite the 'Draft' to perfectly match the 'Brand Voice'.
        
        BRAND VOICE RULES:
        {profile_text}
        
        DRAFT CONTENT:
        {user_draft}
        
        INSTRUCTIONS:
        1. Keep the core message.
        2. Change the tone, vocabulary, and sentence structure to match the profile.
        3. Output ONLY the rewritten text.
        """
        response = self.model.generate_content(prompt)
        return response.text

    def run_content_generator(self, topic, format_type, key_points, profile_text):
        """Generates new content from scratch."""
        prompt = f"""
        ROLE: Brand Content Studio.
        TASK: Create a {format_type}.
        TOPIC: {topic}
        KEY POINTS: {key_points}
        
        BRAND GUIDELINES:
        {profile_text}
        """
        response = self.model.generate_content(prompt)
        return response.text

    def describe_logo(self, image):
        """Helper to analyze a logo file during Wizard setup."""
        prompt = "Describe this logo in detail (colors, shapes, text, vibe) for a brand style guide."
        response = self.model.generate_content([prompt, image])
        return response.text

    def analyze_social_post(self, image):
        """Helper to analyze a social media screenshot."""
        prompt = "Analyze this social media post. What is the tone? What is the visual style? What makes it successful?"
        response = self.model.generate_content([prompt, image])
        return response.text
