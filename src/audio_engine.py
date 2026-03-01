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

def generate_subtitles_locally(audio_path, vtt_path, ass_path):
    """Uses Whisper to generate both a lightweight VTT backup and a stylized ASS file."""
    print("[INFO] Booting local Whisper AI to map word timestamps...")
    
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    segments_gen, info = model.transcribe(audio_path, word_timestamps=True)
    
    # We convert the generator to a list so we can loop over the data twice without re-transcribing
    segments = list(segments_gen)
    
    # --- 1. GENERATE THE VTT BACKUP ---
    vtt_lines = ["WEBVTT\n\n"]
    for segment in segments:
        for word in segment.words:
            start_str = _format_vtt_time(word.start)
            end_str = _format_vtt_time(word.end)
            vtt_lines.append(f"{start_str} --> {end_str}\n{word.word.strip()}\n\n")
            
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.writelines(vtt_lines)
    print(f"[SUCCESS] VTT backup mapped and saved to {vtt_path}")

    # --- 2. GENERATE THE ASS MASTER FILE ---
    # ASS Header for 1080x1920 video. 
    # Note: ASS colors are BGR (Blue-Green-Red). Cyan is 00FFFF00. White is 00FFFFFF.
    ass_lines = [
        "[Script Info]\n",
        "ScriptType: v4.00+\n",
        "PlayResX: 1080\n",
        "PlayResY: 1920\n",
        "WrapStyle: 1\n\n",
        "[V4+ Styles]\n",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n",
        "Style: Default,Montserrat-Bold,80,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,5,20,20,0,1\n\n",
        "[Events]\n",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    ]

    for segment in segments:
        words = segment.words
        chunks = []
        current_chunk = []
        
        # Group words into chunks of 3 for that punchy Shorts aesthetic
        for w in words:
            current_chunk.append(w)
            if len(current_chunk) == 3 or w.word.strip()[-1] in [".", ",", "?", "!"]:
                chunks.append(current_chunk)
                current_chunk = []
        if current_chunk:
            chunks.append(current_chunk)

        # Build the dynamic highlight logic
        for chunk in chunks:
            for i, active_word in enumerate(chunk):
                start_time = _format_ass_time(active_word.start)
                
                # To prevent flickering, keep the text on screen until the NEXT word starts
                if i < len(chunk) - 1:
                    end_time = _format_ass_time(chunk[i+1].start)
                else:
                    end_time = _format_ass_time(active_word.end)

                text_parts = []
                for j, w in enumerate(chunk):
                    clean_word = w.word.strip()
                    if i == j:
                        # Wrap the active word in the Cyan color tag
                        text_parts.append(f"{{\\c&H00FFFF00&}}{clean_word}{{\\c&H00FFFFFF&}}")
                    else:
                        text_parts.append(clean_word)

                full_text = " ".join(text_parts)
                ass_lines.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{full_text}\n")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.writelines(ass_lines)
    print(f"[SUCCESS] ASS animated subtitles saved to {ass_path}")

async def generate_audio(script_json, audio_path, vtt_path, ass_path):
    """The master function that Station 3 calls."""
    success = generate_audio_offline(script_json, audio_path)
    if success:
        generate_subtitles_locally(audio_path, vtt_path, ass_path)