import os
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro

def _format_vtt_time(seconds):
    """Formats raw seconds into the strict VTT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def _format_ass_time(seconds):
    """Formats raw seconds into the ASS timestamp format (H:MM:SS.cs)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def get_voice_selection():
    """Maps Kokoro voices to their emotional tones and allows user selection."""
    # The Tone Map: Linking Kokoro profile IDs to their cinematic vibe
    voice_map = {
        "1": {"id": "am_michael", "tone": "Deep, dramatic, cinematic (Male)"},
        "2": {"id": "af_bella",   "tone": "Soft, breathy, melancholic (Female)"},
        "3": {"id": "am_adam",    "tone": "Clear, grounded, conversational (Male)"},
        "4": {"id": "bf_emma",    "tone": "Cold, clinical, British (Female)"},
        "5": {"id": "bm_george",  "tone": "Warm, authoritative, British (Male)"},
        "6": {"id": "af_sky",     "tone": "Crisp, modern, documentary (Female)"}
    }
    
    print("\n========================================")
    print("         SELECT NEURAL VOICE TONE       ")
    print("========================================")
    
    for key, info in voice_map.items():
        print(f"[{key}] {info['id'].ljust(12)} | Vibe: {info['tone']}")
    print("-" * 40)
    
    while True:
        choice = input("Select a voice (1-6) or press Enter for default [am_michael]: ").strip()
        
        # Default to Michael if you just hit Enter to speed up the workflow
        if not choice:
            print("[INFO] Defaulting to: am_michael")
            return "am_michael"
            
        if choice in voice_map:
            selected = voice_map[choice]["id"]
            print(f"[INFO] Voice locked: {selected}")
            return selected
            
        print("[ERROR] Invalid selection. Please enter a number from 1 to 6.")

def get_subtitle_preferences():
    """Scans for fonts and presents a style menu for the subtitles."""
    print("\n========================================")
    print("         SELECT TYPOGRAPHY & STYLE      ")
    print("========================================")
    
    # --- 1. Font Discovery ---
    fonts_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "assets", "fonts"))
    available_fonts = []
    
    if os.path.exists(fonts_dir):
        for f in os.listdir(fonts_dir):
            if f.lower().endswith(('.ttf', '.otf')):
                available_fonts.append(f)
                
    if not available_fonts:
        print("[WARNING] No .ttf or .otf fonts found in data/assets/fonts/")
        print("[INFO] Defaulting to system Arial.")
        selected_font = "Arial"
    else:
        print("Available Fonts:")
        for i, font in enumerate(available_fonts):
            print(f"[{i + 1}] {font}")
            
        while True:
            choice = input(f"Select a font (1-{len(available_fonts)}) or press Enter for default [1]: ").strip()
            if not choice:
                selected_font = available_fonts[0].rsplit('.', 1)[0] # Strip the .ttf extension
                break
            if choice.isdigit() and 1 <= int(choice) <= len(available_fonts):
                selected_font = available_fonts[int(choice) - 1].rsplit('.', 1)[0]
                break
            print("[ERROR] Invalid selection.")
            
    print(f"[INFO] Font locked: {selected_font}")

    # --- 2. Animation Style Menu ---
    print("\nAvailable Animation Styles:")
    print("[1] The Hormozi (White text, Cyan word-by-word highlight)")
    print("[2] The Warning (White text, Yellow word-by-word highlight)")
    print("[3] Blood Drive (White text, Red word-by-word highlight)")
    print("[4] Netflix Minimal (Static White text, no animation)")
    
    # ASS Colors are BGR (Blue-Green-Red). e.g., Cyan is 00FFFF00 (Alpha-BB-GG-RR)
    styles_map = {
        "1": {"active": "&H00FFFF00&", "inactive": "&H00FFFFFF&"}, # Cyan
        "2": {"active": "&H0000FFFF&", "inactive": "&H00FFFFFF&"}, # Yellow
        "3": {"active": "&H000000FF&", "inactive": "&H00FFFFFF&"}, # Red
        "4": {"active": None,          "inactive": "&H00FFFFFF&"}  # Static White
    }
    
    while True:
        choice = input("Select a style (1-4) or press Enter for default [1]: ").strip()
        if not choice:
            style_config = styles_map["1"]
            break
        if choice in styles_map:
            style_config = styles_map[choice]
            break
        print("[ERROR] Invalid selection.")

    return selected_font, style_config

def generate_audio_offline(script_json, audio_path):
    """Generates ultra-realistic voiceover using the local Kokoro Neural Network."""
    
    # 1. Trigger the Tone Router before booting the heavy neural net
    selected_voice = get_voice_selection()
    
    print("[INFO] Booting Kokoro Neural TTS Engine (Offline)...")
    full_text = " ".join([scene["voiceover"] for scene in script_json["scenes"]])
    
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
        kokoro = Kokoro("models/kokoro/kokoro-v1.0.onnx", "models/kokoro/voices-v1.0.bin")
    except Exception as e:
        print(f"[ERROR] Failed to load Kokoro models: {e}")
        return False

    try:
        print(f"[INFO] Synthesizing speech array using profile: {selected_voice}...")
        # We pass your dynamically selected voice into the engine
        samples, sample_rate = kokoro.create(full_text, voice=selected_voice, speed=0.9, lang="en-us")
        
        sf.write(audio_path, samples, sample_rate)
        print(f"[SUCCESS] Cinematic neural audio saved to {audio_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Audio synthesis failed: {e}")
        return False

def generate_subtitles_locally(audio_path, vtt_path, ass_path, font_name, style_config):
    """Uses Whisper to generate subtitles and mathematically applies the chosen style."""
    print("\n[INFO] Booting local Whisper AI to map word timestamps...")
    
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    segments_gen, info = model.transcribe(audio_path, word_timestamps=True)
    segments = list(segments_gen)
    
    # --- 1. GENERATE THE VTT BACKUP ---
    vtt_lines = ["WEBVTT\n\n"]
    for segment in segments:
        for word in segment.words:
            start_str = _format_ass_time(word.start).replace(".", ",") # VTT uses comma
            end_str = _format_ass_time(word.end).replace(".", ",")
            vtt_lines.append(f"{start_str} --> {end_str}\n{word.word.strip()}\n\n")
            
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.writelines(vtt_lines)
    print(f"[SUCCESS] VTT backup mapped and saved.")

    # --- 2. GENERATE THE ASS MASTER FILE ---
    # We dynamically inject the font_name here
    ass_lines = [
        "[Script Info]\n",
        "ScriptType: v4.00+\n",
        "PlayResX: 1080\n",
        "PlayResY: 1920\n",
        "WrapStyle: 1\n\n",
        "[V4+ Styles]\n",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n",
        f"Style: Default,{font_name},80,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,5,20,20,0,1\n\n",
        "[Events]\n",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    ]

    for segment in segments:
        words = segment.words
        chunks = []
        current_chunk = []
        
        # Group words into chunks of 3 for mobile layout
        for w in words:
            current_chunk.append(w)
            if len(current_chunk) == 3 or w.word.strip()[-1] in [".", ",", "?", "!"]:
                chunks.append(current_chunk)
                current_chunk = []
        if current_chunk:
            chunks.append(current_chunk)

        # Build the dynamic highlight logic
        for chunk in chunks:
            # If "Netflix Minimal" is selected, just write the sentence once without highlight logic
            if style_config["active"] is None:
                start_time = _format_ass_time(chunk[0].start)
                end_time = _format_ass_time(chunk[-1].end)
                full_text = " ".join([w.word.strip() for w in chunk])
                ass_lines.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{full_text}\n")
                continue

            # Otherwise, build the Karaoke animation frames
            for i, active_word in enumerate(chunk):
                start_time = _format_ass_time(active_word.start)
                end_time = _format_ass_time(chunk[i+1].start) if i < len(chunk) - 1 else _format_ass_time(active_word.end)

                text_parts = []
                for j, w in enumerate(chunk):
                    clean_word = w.word.strip()
                    if i == j: # The active word gets the color tag
                        text_parts.append(f"{{\\c{style_config['active']}}}{clean_word}{{\\c{style_config['inactive']}}}")
                    else:
                        text_parts.append(clean_word)

                full_text = " ".join(text_parts)
                ass_lines.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{full_text}\n")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.writelines(ass_lines)
    print(f"[SUCCESS] ASS styled subtitles saved to {ass_path}")

async def generate_audio(script_json, audio_path, vtt_path, ass_path):
    """The master function that Station 3 calls."""
    # 1. Generate Voice
    success = generate_audio_offline(script_json, audio_path)
    
    # 2. Ask for Subtitle Styling
    font_name, style_config = get_subtitle_preferences()
    
    if success:
        # 3. Generate Styled Subs
        generate_subtitles_locally(audio_path, vtt_path, ass_path, font_name, style_config)