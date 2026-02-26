import os
import json
from google import genai
import ollama

def _get_prompt(topic_title, channel_aesthetic="Shot on 35mm film, anamorphic lens, f/2.8, melancholic, atmospheric, highly detailed, muted colors"):
    return f"""
    You are an expert YouTube Shorts retention engineer, scriptwriter, and AI image prompt specialist. 
    Your goal is to write a highly engaging 60-second script about: "{topic_title}" that achieves a 70%+ "Viewed" rate.
    
    CRITICAL RULES FOR RETENTION:
    1. THE HOOK: The first 3 seconds must be a pattern interrupt. Start with a mind-bending fact or terrifying concept. NEVER use introductory phrases.
    2. THE LOOP: The final sentence of the script MUST seamlessly, grammatically flow directly back into the very first sentence of Scene 1. 
    3. AUDIO PACING: Use frequent em-dashes (—) for dramatic pauses, ellipses (...) for trailing thoughts to make the AI voiceover sound cinematic and human.
    
    CRITICAL RULES FOR FLUX-SCHNELL IMAGE GENERATION:
    1. PROSE, NOT KEYWORDS: Flux runs on natural language. Write fluid, highly descriptive paragraphs. NEVER use comma-separated AI buzzwords (e.g., "masterpiece, 8k, trending").
    2. STRICT SPATIAL ORDER: Structure every prompt in this exact flow: [Subject Appearance] -> [Subject Action & Position in Frame] -> [Foreground/Background Details] -> [Lighting Physics].
    3. SCALE & VERTICAL DEPTH: Because this is a 9:16 vertical video, you must explicitly describe scale and depth. Tell me what is in the immediate foreground, and what looms massive in the distant background.
    4. NO NEGATIVE PROMPTS: The model cannot understand absence. Never use words like "no," "without," or "empty." Instead of "no people," describe "a barren, desolate wasteland."
    5. CHANNEL BRANDING: You MUST append the following exact aesthetic string to the very end of EVERY visual_idea: "{channel_aesthetic}"
    
    You MUST output ONLY valid JSON in the exact following format:
    {{
      "title": "[Insert Title Under 50 Characters]",
      "scenes": [
        {{
          "scene_number": 1,
          "visual_idea": "[Describe the subject and environment actively] + {channel_aesthetic}",
          "voiceover": "[Insert exactly what the narrator will say]"
        }}
      ]
    }}
    Aim for exactly 4 to 6 scenes. Combined voiceover must be 130 to 150 words.
    """

def generate_script_gemini(api_key, topic_title):
    print(f"[INFO] Requesting script from Gemini for: '{topic_title}'...")
    client = genai.Client(api_key=api_key)
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=_get_prompt(topic_title),
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"[WARNING] Gemini Failed: {e}")
        return None

def generate_script_ollama(topic_title, model_name="llama3"):
    print(f"[INFO] Falling back to local Ollama ({model_name})...")
    try:
        response = ollama.chat(
            model=model_name, 
            messages=[{'role': 'user', 'content': _get_prompt(topic_title)}],
            format='json'
        )
        return json.loads(response['message']['content'])
    except Exception as e:
        print(f"[ERROR] Ollama also failed: {e}")
        return None

def draft_script(topic_title):
    gemini_key = os.getenv("GEMINI_API_KEY")
    script_data = generate_script_gemini(gemini_key, topic_title)
    if not script_data:
        script_data = generate_script_ollama(topic_title)
    return script_data