import os
import json
from google import genai
from google.genai import types
from groq import Groq
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# ==========================================
# 1. THE PYDANTIC SCHEMA (STRUCTURED OUTPUT)
# ==========================================

class Scene(BaseModel):
    scene_number: int
    asset_type: Literal["ai", "archive_wikimedia", "archive_nasa"] = Field(
        description="Choose 'ai' for abstract/cinematic scenes. Choose 'archive_wikimedia' for history/people. Choose 'archive_nasa' for space/physics."
    )
    visual_description: str = Field(
        description="A plain-English description of what is happening on screen. Use the persona's thematic style to frame this description."
    )
    ai_prompt: str = Field(
        description="The highly detailed Flux image prompt. Frame the aesthetic choices using the persona's perspective. YOU MUST GENERATE THIS FOR EVERY SCENE as a fallback."
    )
    archive_query: Optional[str] = Field(
        description="The precise search query for the archive. Leave null if asset_type is 'ai'."
    )
    voiceover: str = Field(
        description="The spoken text. Rely strictly on the pacing and vocabulary provided in the persona instructions, but do not announce the persona directly."
    )

class Script(BaseModel):
    title: str
    scenes: List[Scene]

# ==========================================
# 2. THE GENERATION LOGIC
# ==========================================

def generate_narrative_premise(raw_keywords, persona_instruction):
    """Dynamically assumes a persona based on keywords to generate a premise."""
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an elite YouTube Shorts creative director.
    I will give you raw YouTube search keywords: "{raw_keywords}"
    
    STEP 1: Analyze the keywords and determine the core subject.
    STEP 2: Return a crisp working title for the video. 
    
    CRITICAL PERSONA INSTRUCTION:
    {persona_instruction}
    
    Output ONLY the Working Title. No quotes, no pleasantries.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview', 
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[ERROR] Premise generation failed: {e}")
        return raw_keywords
    
def _get_prompt(topic_title, persona_instruction, channel_aesthetic="Shot on 35mm film, anamorphic lens, f/2.8, atmospheric, highly detailed, muted colors"):
    return f"""
    You are an expert YouTube Shorts retention engineer, scriptwriter, and AI image prompt specialist. 
    Your goal is to write a highly engaging 60-second script about: "{topic_title}" that achieves a 70%+ "Viewed" rate.
    
    CRITICAL PERSONA INSTRUCTION:
    {persona_instruction}
    
    IMPORTANT: Embody this persona implicitly through the tone, vocabulary, and pacing of the `voiceover` and the aesthetic choices in the `ai_prompt`. DO NOT announce the persona explicitly. 
    
    CRITICAL RULES FOR RETENTION:
    1. THE HOOK: The first 3 seconds must be a pattern interrupt. Start with a mind-bending fact or captivating concept.
    2. THE LOOP: The final sentence of the script MUST seamlessly, grammatically flow directly back into the very first sentence of Scene 1. 
    3. AUDIO PACING: Use frequent em-dashes (—) for dramatic pauses, ellipses (...) for trailing thoughts to make the voiceover sound cinematic and human.
    
    CRITICAL RULES FOR FLUX-SCHNELL IMAGE GENERATION (The `ai_prompt` field):
    1. PROSE, NOT KEYWORDS: Write fluid, highly descriptive paragraphs.
    2. STRICT SPATIAL ORDER: Structure every prompt: [Subject Appearance] -> [Subject Action] -> [Foreground/Background Details] -> [Lighting Physics].
    3. SCALE & VERTICAL DEPTH: Tell me what is in the immediate foreground, and what looms massive in the distant background.
    4. NO NEGATIVE PROMPTS: Never use words like "no," "without," or "empty."
    5. CHANNEL BRANDING: You MUST append this exact string to the very end of EVERY ai_prompt: "{channel_aesthetic}"

    ASSET ROUTING RULES:
    - Determine if the scene needs a real historical/space photograph (`archive_wikimedia` or `archive_nasa`) or a generated cinematic image (`ai`).
    - If archival, provide a clean `archive_query` (e.g., 'Nikola Tesla portrait').
    - ALWAYS provide an `ai_prompt` as a fallback, even for archival scenes!

    Aim for exactly 4 to 6 scenes. Combined voiceover must be 130 to 150 words.
    """

def generate_script_gemini(api_key, topic_title, persona_instruction):
    print(f"[INFO] Requesting script from Gemini for: '{topic_title}'...")
    client = genai.Client(api_key=api_key)
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=_get_prompt(topic_title, persona_instruction),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Script, 
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"[WARNING] Gemini Failed: {e}")
        return None

def generate_script_groq(topic_title, persona_instruction):
    print(f"[INFO] Falling back to Groq Cloud (Llama 3.3 70B Versatile)...")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("[ERROR] GROQ_API_KEY not found in environment variables.")
        return None
        
    client = Groq(api_key=groq_api_key)
    
    # Dump the Pydantic schema to JSON so the model knows the exact structure
    schema_json = json.dumps(Script.model_json_schema(), indent=2)
    prompt = _get_prompt(topic_title, persona_instruction) + f"\n\nYou MUST return valid JSON strictly matching this schema:\n{schema_json}"
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7 # Slight bump for narrative creativity
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[ERROR] Groq Fallback failed: {e}")
        return None

def draft_script(topic_title, persona_instruction):
    # Attempt Primary Cloud (Gemini)
    script_data = generate_script_gemini(os.getenv("GEMINI_API_KEY"), topic_title, persona_instruction)
    
    # Attempt Backup Cloud (Groq) if Gemini fails or returns a dictionary containing an error
    if not script_data or (isinstance(script_data, dict) and "error" in script_data):
        script_data = generate_script_groq(topic_title, persona_instruction)
        
    return script_data