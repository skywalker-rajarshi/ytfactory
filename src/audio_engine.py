import edge_tts
import os

async def generate_audio(script_json, output_audio="data/assets/voiceover.mp3", output_subs="data/assets/subtitles.vtt"):
    """Generates audio and a word-by-word VTT subtitle file."""
    print(f"[INFO] Generating cinematic voiceover and word-level subtitles...")
    
    full_text = ""
    for scene in script_json.get("scenes", []):
        full_text += scene.get("voiceover", "") + " "
        
    if not full_text.strip():
        print("[ERROR] No voiceover text found in the script.")
        return False

    VOICE = "en-GB-RyanNeural" 
    
    communicate = edge_tts.Communicate(
        text=full_text, 
        voice=VOICE, 
        rate="-10%", 
        pitch="-5Hz"
    )
    
    submaker = edge_tts.SubMaker()
    
    # We stream the generation to catch the WordBoundary events for subtitles
    with open(output_audio, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])

    with open(output_subs, "w", encoding="utf-8") as file:
        file.write(submaker.generate_subs())
    
    print(f"[SUCCESS] Audio and subtitles saved successfully!")
    return True