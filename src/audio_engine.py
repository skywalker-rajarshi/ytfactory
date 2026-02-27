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

def generate_audio_offline(script_json, audio_path):
    """Generates ultra-realistic voiceover using the local Kokoro Neural Network."""
    print("[INFO] Booting Kokoro Neural TTS Engine (Offline)...")
    full_text = " ".join([scene["voiceover"] for scene in script_json["scenes"]])
    
    try:
        # Load the neural network into memory
        kokoro = Kokoro("models/kokoro/kokoro-v1.0.onnx", "models/kokoro/voices-v1.0.bin")
    except Exception as e:
        print(f"[ERROR] Failed to load Kokoro models. Did you run the curl downloads? {e}")
        return False

    try:
        # am_michael is a deep, highly cinematic male voice. 
        # We slow the speed to 0.9 for a heavier, more dramatic read.
        print("[INFO] Synthesizing speech array...")
        samples, sample_rate = kokoro.create(full_text, voice="am_michael", speed=0.9, lang="en-us")
        
        # Write the numpy array to a high-fidelity WAV file
        sf.write(audio_path, samples, sample_rate)
        print(f"[SUCCESS] Cinematic neural audio saved to {audio_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Audio synthesis failed: {e}")
        return False

def generate_vtt_locally(audio_path, subs_path):
    """Uses a local Whisper AI model to listen to the audio and map word timestamps."""
    print("[INFO] Booting local Whisper AI to map word timestamps...")
    
    # Loads the tiny model locally (runs flawlessly on M-series chips)
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(audio_path, word_timestamps=True)
    
    vtt_lines = ["WEBVTT\n\n"]
    word_count = 0
    
    for segment in segments:
        for word in segment.words:
            word_count += 1
            start_str = _format_vtt_time(word.start)
            end_str = _format_vtt_time(word.end)
            vtt_lines.append(f"{start_str} --> {end_str}\n{word.word.strip()}\n\n")

    with open(subs_path, "w", encoding="utf-8") as f:
        f.writelines(vtt_lines)
        
    print(f"[SUCCESS] Subtitles mapped and saved to {subs_path} ({word_count} words)")

async def generate_audio(script_json, audio_path, subs_path):
    """The master function that Station 3 calls."""
    success = generate_audio_offline(script_json, audio_path)
    
    if success:
        generate_vtt_locally(audio_path, subs_path)