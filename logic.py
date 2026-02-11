import google.generativeai as genai
import os
import json
import re
import math
import colorsys
from collections import Counter
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

# --- CONFIG ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- 1. BIOMETRIC MATH ENGINE (Color Science) ---

def hex_to_rgb(hex_code):
    """Converts #RRGGBB to (r, g, b)"""
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """Converts (r, g, b) to #RRGGBB"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def extract_dominant_colors(image, num_colors=5):
    """
    K-Means clustering to find distinct dominant hex codes.
    """
    try:
        # Resize for speed
        img = image.copy()
        img.thumbnail((150, 150))
        img = img.convert("RGB")
        
        # Convert to numpy array
        img_array = np.array(img)
        pixels = img_array.reshape(-1, 3)
        
        # Use KMeans to find clusters
        kmeans = KMeans(n_clusters=num_colors, n_init=10)
        kmeans.fit(pixels)
        
        # Convert centers back to hex
        return [rgb_to_hex(c) for c in kmeans.cluster_centers_]
    except Exception as e:
        print(f"Color Extraction Error: {e}")
        return []

class ColorScorer:
    @staticmethod
    def grade_color_match(detected_hexes, profile_text):
        """
        OBJECTIVE MATH: Compares detected colors vs. extracted profile colors.
        Includes Vector Math for Tints & Shades.
        """
        # 1. Parse Brand Hexes from Profile Text (Regex Hunt)
        brand_hexes = list(set(re.findall(r'#[0-9a-fA-F]{6}', profile_text)))
        
        if not brand_hexes:
            return 100, "No strict brand colors defined in profile."
        
        if not detected_hexes:
            return 0, "No colors detected in the image."

        matches = []
        logs = []

        for d_hex in detected_hexes:
            d_rgb = hex_to_rgb(d_hex)
            best_match_score = 0
            match_type = "None"
            matched_brand_color = None

            for b_hex in brand_hexes:
                b_rgb = hex_to_rgb(b_hex)
                
                # A. EXACT MATCH (Euclidean Distance in RGB)
                # Max distance is ~441. We consider < 50 a "close" match.
                distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(d_rgb, b_rgb)))
                dist_score = max(0, 100 - (distance * 2))
                
                if dist_score > best_match_score:
                    best_match_score = dist_score
                    match_type = "Direct"
                    matched_brand_color = b_hex

                # B. TINT/SHADE MATH (The Vector Upgrade)
                # Convert to HLS (Hue, Lightness, Saturation)
                d_h, d_l, d_s = colorsys.rgb_to_hls(*[x/255.0 for x in d_rgb])
                b_h, b_l, b_s = colorsys.rgb_to_hls(*[x/255.0 for x in b_rgb])
                
                # Logic:
                # 1. Hue must be very close (within 5% / 18 degrees)
                # 2. Lightness/Saturation can vary (that's what makes it a tint/shade)
                hue_diff = abs(d_h - b_h)
                if hue_diff > 0.5: hue_diff = 1.0 - hue_diff # Handle color wheel wrap-around
                
                if hue_diff < 0.05: # 5% Tolerance on Hue Family
                    tint_score = 90 # High score for correct color family
                    if tint_score > best_match_score:
                        best_match_score = tint_score
                        match_type = "Tint/Shade"
                        matched_brand_color = b_hex

            matches.append(best_match_score)
            if best_match_score > 60:
                logs.append(f"Detected {d_hex} matches {matched_brand_color} ({match_type})")
        
        # Final Score is average of the top 3 dominant colors found
        matches.sort(reverse=True)
        top_matches = matches[:3]
        final_score = int(sum(top_matches) / max(len(top_matches), 1))
        
        reasoning = f"Math Analysis: {final_score}/100 match. "
        if logs:
            reasoning += ", ".join(logs[:2]) + "..."
        else:
            reasoning += f"Colors {detected_hexes[:3]} deviation from palette."
            
        return final_score, reasoning


# --- 2. MAIN LOGIC CLASS --- #
import time
from google.api_core import exceptions

class SignetLogic:
    def __init__(self):
        # 1. THE STABLE CORE (Upgraded to Confirmed Model)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 2. THE RESEARCHER (Stabilized)
        self.search_model = genai.GenerativeModel('gemini-2.0-flash')

    def _safe_generate(self, model_instance, prompt, image=None, retries=3):
        """
        Internal helper to handle 429 Quota errors with exponential backoff.
        """
        for i in range(retries):
            try:
                if image:
                    return model_instance.generate_content([prompt, image])
                else:
                    return model_instance.generate_content(prompt)
            except exceptions.ResourceExhausted:
                # If quota hits, wait exponentially (2s, 4s, 8s)
                wait_time = 2 ** (i + 1)
                time.sleep(wait_time)
                continue
            except Exception as e:
                # If it's a different error (like 400), fail immediately
                raise e
        
        # If we run out of retries, try one last time and let it fail if it must
        if image:
            return model_instance.generate_content([prompt, image])
        return model_instance.generate_content(prompt)

# --- NEW: STRICT REVERSE ENGINEERING ---
    def analyze_social_style(self, image):
        """
        REVERSE ENGINEER: Extracts style/aesthetic from an image.
        Strictly forbids generation of new content.
        Used for Brand DNA Ingestion.
        Includes 429/Quota Retry Logic.
        """
        import time
        from google.api_core.exceptions import ResourceExhausted

        prompt = """
        ROLE: Brand Strategist.
        TASK: Reverse-engineer the 'Social DNA' of this post.
        
        INSTRUCTIONS:
        1. TRANSCRIPT: Read the exact caption text visible in the image. Ignore user comments.
        2. ANALYZE: Break down the strategy used.
        
        CONSTRAINTS:
        - DO NOT chat (e.g. "Here is the analysis"). Start directly with the output.
        - DO NOT use emojis.
        - DO NOT offer improvements or generate new options.
        
        OUTPUT FORMAT (Strictly follow this structure):
        [CAPTION TRANSCRIPT]
        (Paste the exact text found in the image here)
        
        [STRATEGY ANALYSIS]
        - VISUAL AESTHETIC: (e.g. Minimalist, High Contrast, Candid, Stock Photo)
        - CAPTION STRUCTURE: (e.g. Short & Punchy, Long Storytelling, Bullet Points)
        - HASHTAG STRATEGY: (e.g. Brand-specific, Niche, Broad)
        - TONE OF VOICE: (e.g. Professional, Direct, Educational)
        """
        
        # RETRY LOOP (Safeguard for 429 Errors)
        max_retries = 3
        backoff_factor = 2  # Seconds
        
        for attempt in range(max_retries):
            try:
                # Use Safe Generate
                response = self._safe_generate(self.model, prompt, image)
                text = response.text
                
                # Post-processing: Strict Filter for Chatty Intros
                # If the model ignores the system instruction and adds a preamble, strip it.
                if "Here is" in text or "Okay" in text:
                    # Split by newline and take the rest
                    parts = text.split('\n', 1)
                    if len(parts) > 1:
                        text = parts[1].strip()
                
                return text

            except ResourceExhausted:
                # HIT RATE LIMIT - WAIT AND RETRY
                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2 ** attempt) # 2s, 4s, 8s...
                    time.sleep(wait_time)
                    continue
                else:
                    return "⚠️ System Busy: The AI is currently overloaded. Please wait 30 seconds and try again."
            
            except Exception as e:
                return f"Error extracting style: {e}"
    def run_visual_audit(self, image, profile_text):
        """
        THE JUDGE: Combines Math + Vision + Text Reading for 5-Pillar Score.
        """
        # A. MATH: RUN COLOR SCIENCE
        color_raw = 50 
        color_logic = "Visual inspection only."
        detected_hexes = []
        
        try:
            detected_hexes = extract_dominant_colors(image)
            color_raw, color_logic = ColorScorer.grade_color_match(detected_hexes, profile_text)
        except Exception as e:
            color_logic = f"Math Error: {str(e)}"
        
        # B. AI: RUN VISION & TEXT ANALYSIS
        prompt = f"""
        ROLE: Chief Brand Officer.
        TASK: Audit this image against the Brand Profile.
        
        BRAND PROFILE:
        {profile_text}
        
        DETECTED HEX CODES: {", ".join(detected_hexes) if detected_hexes else "N/A"}
        
        INSTRUCTIONS:
        1. READ ANY TEXT visible in the image. Check for spelling, grammar, tone, and forbidden words.
        2. ANALYZE VISUALS (Logo, Typography, Vibe).
        
        SCORING RUBRIC (0-100 per category):
        - IDENTITY (25%): Logo usage, placement, distortion. If no logo but valid asset (e.g. pattern), score high.
        - COLOR (25%): Check against hex codes. IMPORTANT: Accept tints (lighter) and shades (darker) of the Primary Palette as COMPLIANT. Do not penalize for opacity changes.
        - TYPOGRAPHY (15%): Font family, hierarchy, legibility.
        - VIBE (15%): Archetype match (e.g. Ruler vs Jester).
        - TONE & COPY (20%): Does the text match the brand voice? Are there forbidden words? Is it typo-free?
        
        OUTPUT FORMAT: Return a PURE JSON object (no markdown) with these exact keys:
        - "identity_score": (int 0-100)
        - "identity_reason": (string)
        - "type_score": (int 0-100)
        - "type_reason": (string)
        - "vibe_score": (int 0-100)
        - "vibe_reason": (string)
        - "tone_score": (int 0-100)
        - "tone_reason": (string) If no text found, give 100 (Neutral).
        - "critical_fixes": (List of strings) Absolute failures (e.g. Wrong Logo).
        - "minor_fixes": (List of strings) Polish items.
        - "brand_wins": (List of strings) What is working well.
        """
        
        try:
            # UPGRADE: Wrapper used
            response = self._safe_generate(self.model, prompt, image)
            txt = response.text.replace("```json", "").replace("```", "").strip()
            ai_result = json.loads(txt)
            
            # --- C. WEIGHTED CALCULATION ---
            s_color = color_raw
            s_identity = ai_result.get('identity_score', 0)
            s_tone = ai_result.get('tone_score', 100)
            s_type = ai_result.get('type_score', 0)
            s_vibe = ai_result.get('vibe_score', 0)
            
            final_score = int(
                (s_color * 0.25) + 
                (s_identity * 0.25) + 
                (s_tone * 0.20) + 
                (s_type * 0.15) + 
                (s_vibe * 0.15)
            )
            
            verdict = "COMPLIANT"
            if final_score < 85: verdict = "NEEDS REVIEW"
            if final_score < 60: verdict = "NON-COMPLIANT"
            
            return {
                "score": final_score,
                "verdict": verdict,
                "breakdown": {
                    "color": {"score": s_color, "reason": color_logic},
                    "identity": {"score": s_identity, "reason": ai_result.get('identity_reason')},
                    "tone": {"score": s_tone, "reason": ai_result.get('tone_reason')},
                    "typography": {"score": s_type, "reason": ai_result.get('type_reason')},
                    "vibe": {"score": s_vibe, "reason": ai_result.get('vibe_reason')}
                },
                "critical_fixes": ai_result.get('critical_fixes', []),
                "minor_fixes": ai_result.get('minor_fixes', []),
                "brand_wins": ai_result.get('brand_wins', [])
            }
            
        except Exception as e:
            return {
                "score": 0, 
                "verdict": "ERROR", 
                "breakdown": {}, 
                "critical_fixes": [f"System Error: {str(e)}"], 
                "minor_fixes": [], 
                "brand_wins": []
            }

    # --- WIZARD & PDF TOOLS ---
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
        found_hexes = re.findall(r'#[0-9a-fA-F]{6}', pdf_text)
        unique_hexes = list(set(found_hexes))
        
        prompt = f"""
        TASK: Extract Brand Rules from this PDF text.
        CONTEXT: I have already detected these Hex Codes: {unique_hexes}. 
        OUTPUT: Return a PURE JSON object (no markdown) with these keys: 
        wiz_name, wiz_archetype, wiz_mission, wiz_values, wiz_tone, wiz_guardrails, palette_primary (list of hex), palette_secondary (list of hex), writing_sample.
        RAW TEXT: {pdf_text[:15000]}
        """
        try:
            # UPGRADE: Wrapper used
            response = self._safe_generate(self.model, prompt)
            cleaned = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            return {
                 "wiz_name": "Error Logs", 
                 "wiz_mission": f"ERROR: {str(e)}", 
                 "wiz_archetype": "Error",
                 "palette_primary": unique_hexes[:5] if unique_hexes else ["#000000"],
                 "palette_secondary": [],
                 "writing_sample": pdf_text[:500] 
             }

    def generate_brand_rules(self, prompt_text):
        # UPGRADE: Wrapper used
        response = self._safe_generate(self.model, prompt_text)
        return response.text

    # --- COPY EDITOR & GENERATOR ---
    def run_copy_editor(self, user_draft, profile_text):
        prompt = f"Rewrite this draft to match the brand voice:\n\nBRAND RULES:\n{profile_text}\n\nDRAFT:\n{user_draft}"
        try:
            # UPGRADE: Wrapper used
            response = self._safe_generate(self.model, prompt)
            return response.text
        except Exception as e:
            return f"Error generating copy: {e}"

    def run_content_generator(self, topic, format_type, key_points, profile_text):
        prompt = f"Create a {format_type} about {topic}. Key points: {key_points}.\n\nBRAND RULES:\n{profile_text}"
        try:
            # UPGRADE: Wrapper used
            response = self._safe_generate(self.search_model, prompt)
            return response.text
        except Exception as e:
            return f"Error generating content: {e}"
    
    def analyze_social_post(self, image):
        try:
            # UPGRADE: Wrapper used
            response = self._safe_generate(self.model, "Analyze this social post and suggest a caption.", image)
            return response.text
        except Exception as e:
            return "Error analyzing image."

    def describe_logo(self, image):
        try:
            # UPGRADE: Wrapper used
            response = self._safe_generate(self.model, "Describe this logo in detail (colors, shapes, text).", image)
            return response.text
        except Exception as e:
            return "Logo analysis failed."
