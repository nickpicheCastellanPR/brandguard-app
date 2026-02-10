import google.generativeai as genai
import os
import json
import re
import math
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

# --- CONFIG ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- 1. BIOMETRIC MATH ENGINE (Color Science) ---
class ColorScorer:
    @staticmethod
    def hex_to_rgb(hex_code):
        """Converts #RRGGBB to (R, G, B) tuple."""
        hex_code = hex_code.lstrip('#')
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    @staticmethod
    def calculate_distance(color1, color2):
        """Calculates Euclidean distance between two RGB colors."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))

    @staticmethod
    def grade_color_match(detected_hexes, profile_text):
        """
        Comparing Detected Colors vs. Profile Colors mathematically.
        Returns a score (0-100) and a logic string.
        """
        # 1. Extract Target Hexes from Profile Text (Regex)
        target_hexes = re.findall(r'#[0-9a-fA-F]{6}', profile_text)
        if not target_hexes:
            return 100, "No strict color palette defined in profile. Passed by default."

        target_rgbs = [ColorScorer.hex_to_rgb(h) for h in target_hexes]
        detected_rgbs = [ColorScorer.hex_to_rgb(h) for h in detected_hexes]
        
        # 2. Find the best match for each detected color
        matches = []
        scores = []
        
        for d_rgb in detected_rgbs:
            # Find closest brand color
            distances = [ColorScorer.calculate_distance(d_rgb, t_rgb) for t_rgb in target_rgbs]
            min_dist = min(distances)
            
            # SCORING LOGIC (Granular Option A)
            # Distance 0 (Exact) = 100%
            # Distance 50 (Distinctly Different) = 50%
            # Distance 100+ (Wrong Color) = 0%
            match_score = max(0, 100 - (min_dist * 2)) # Slope: -2 points per distance unit
            scores.append(match_score)
            matches.append(f"{ColorScorer.rgb_to_hex(d_rgb)}->{int(match_score)}%")

        # Average score of the top dominant colors
        final_score = int(sum(scores) / len(scores)) if scores else 0
        return final_score, f"Math Analysis: {final_score}/100 match against {target_hexes[:3]}..."

def extract_dominant_colors(image, num_colors=4):
    """Uses K-Means clustering to find exact hex codes."""
    try:
        image = image.resize((150, 150))
        img_array = np.array(image)
        pixels = img_array.reshape(-1, 3)
        kmeans = KMeans(n_clusters=num_colors, n_init=10)
        kmeans.fit(pixels)
        return [ColorScorer.rgb_to_hex(c) for c in kmeans.cluster_centers_]
    except Exception as e:
        print(f"Color Logic Error: {e}")
        return []

# --- 2. MAIN LOGIC CLASS ---
class SignetLogic:
    def __init__(self):
        # Using Flash for speed/cost
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def run_visual_audit(self, image, profile_text):
        """
        THE JUDGE: Combines Math + Vision + Text Reading for 5-Pillar Score.
        """
        # A. MATH: RUN COLOR SCIENCE
        detected_hexes = extract_dominant_colors(image)
        color_score, color_logic = ColorScorer.grade_color_match(detected_hexes, profile_text)
        
        # B. AI: RUN VISION & TEXT ANALYSIS
        prompt = f"""
        ROLE: Chief Brand Officer.
        TASK: Audit this image against the Brand Profile.
        
        BRAND PROFILE:
        {profile_text}
        
        DETECTED HEX CODES: {", ".join(detected_hexes)}
        
        INSTRUCTIONS:
        1. READ ANY TEXT visible in the image. Check for spelling, grammar, tone, and forbidden words.
        2. ANALYZE VISUALS (Logo, Typography, Vibe).
        
        SCORING RUBRIC (0-100 per category):
        - IDENTITY (25%): Logo usage, placement, distortion. If no logo but valid asset (e.g. pattern), score high.
        - COLOR (25%): (Already calculated via Math, but verify context).
        - TYPOGRAPHY (15%): Font family, hierarchy, legibility.
        - VIBE (15%): Archetype match (e.g. Ruler vs Jester).
        - TONE & COPY (20%): Does the text match the brand voice? Are there forbidden words? Is it typo-free?
        
        OUTPUT FORMAT: Return a PURE JSON object (no markdown) with these exact keys:
        - "identity_score": (int)
        - "identity_reason": (string)
        - "type_score": (int)
        - "type_reason": (string)
        - "vibe_score": (int)
        - "vibe_reason": (string)
        - "tone_score": (int)
        - "tone_reason": (string) If no text found, give 100 (Neutral).
        - "critical_fixes": (List of strings) Absolute failures (e.g. Wrong Logo).
        - "minor_fixes": (List of strings) Polish items.
        - "brand_wins": (List of strings) What is working well.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            txt = response.text.replace("```json", "").replace("```", "").strip()
            ai_result = json.loads(txt)
            
            # --- C. WEIGHTED CALCULATION (5 Pillars) ---
            # Color (25%) + Identity (25%) + Tone (20%) + Type (15%) + Vibe (15%)
            
            c_score = color_score * 0.25
            i_score = ai_result.get('identity_score', 0) * 0.25
            txt_score = ai_result.get('tone_score', 100) * 0.20
            t_score = ai_result.get('type_score', 0) * 0.15
            v_score = ai_result.get('vibe_score', 0) * 0.15
            
            final_score = int(c_score + i_score + txt_score + t_score + v_score)
            
            # Verdict Logic
            verdict = "COMPLIANT"
            if final_score < 85: verdict = "NEEDS REVIEW"
            if final_score < 60: verdict = "NON-COMPLIANT"
            
            return {
                "score": final_score,
                "verdict": verdict,
                "breakdown": {
                    "color": {"score": color_score, "reason": color_logic},
                    "identity": {"score": ai_result.get('identity_score'), "reason": ai_result.get('identity_reason')},
                    "tone": {"score": txt_score, "reason": ai_result.get('tone_reason')},
                    "typography": {"score": ai_result.get('type_score'), "reason": ai_result.get('type_reason')},
                    "vibe": {"score": ai_result.get('vibe_score'), "reason": ai_result.get('vibe_reason')}
                },
                "critical_fixes": ai_result.get('critical_fixes', []),
                "minor_fixes": ai_result.get('minor_fixes', []),
                "brand_wins": ai_result.get('brand_wins', [])
            }
            
        except Exception as e:
            # Fallback for errors
            return {
                "score": 0, 
                "verdict": "ERROR", 
                "breakdown": {}, 
                "critical_fixes": [f"System Error: {str(e)}"], 
                "minor_fixes": [], 
                "brand_wins": []
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
        """Extracts structured brand data from raw PDF text with Regex Backup."""
        import re
        import json
        
        # 1. REGEX HUNT: Forcefully find hex codes (6 chars) before AI tries
        # This catches #F45D0D even if the AI misses it.
        found_hexes = re.findall(r'#[0-9a-fA-F]{6}', pdf_text)
        
        # Clean duplicates
        unique_hexes = list(set(found_hexes))
        
        # 2. AI EXTRACTION WITH HINTS
        prompt = f"""
        TASK: Extract Brand Rules from this PDF text.
        
        CONTEXT: I have already mathematically detected these Hex Codes in the document: {unique_hexes}. 
        Please assign them correctly to 'palette_primary' and 'palette_secondary' based on the text context.
        
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
            # Fallback using the found hexes so the user isn't left with nothing
             return {
                 "wiz_name": "Extracted Brand", 
                 "wiz_mission": "Could not extract details.",
                 "palette_primary": unique_hexes[:5] if unique_hexes else ["#000000"],
                 "palette_secondary": [],
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
