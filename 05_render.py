import os
import glob
import subprocess
import json
import random
from src.cleanup_engine import archive_and_cleanup

def get_random_bg_music(base_dir):
    """Presents a menu of music categories (subfolders), then picks a random track from the selection."""
    music_dir = os.path.join(base_dir, "data", "music")
    
    if not os.path.exists(music_dir):
        print("[WARNING] Music directory not found. Proceeding without background music.")
        return None
        
    # Dynamically find all subdirectories (categories) inside data/music/
    categories = [d for d in os.listdir(music_dir) if os.path.isdir(os.path.join(music_dir, d))]
    
    # If no subfolders exist, just scan the root folder
    if not categories:
        print("[INFO] No subfolders found in data/music/. Scanning root folder...")
        target_dir = music_dir
    else:
        print("\n========================================")
        print("          SELECT MUSIC VIBE             ")
        print("========================================")
        print("[-1] No Music (Voiceover Only)")
        print("[0] Surprise Me (Random Category)")
        for i, cat in enumerate(categories):
            print(f"[{i + 1}] {cat}")
        print("-" * 40)
        
        while True:
            choice = input(f"Select a vibe (-1 to {len(categories)}): ").strip()
            
            # The manual bypass for a pure voiceover
            if choice == "-1":
                print("[INFO] Opted for no background music. Proceeding with pure voiceover.")
                return None
                
            # We check if it's a digit (handles 0 and positive numbers)
            if choice.isdigit():
                choice_idx = int(choice)
                if choice_idx == 0:
                    selected_cat = random.choice(categories)
                    target_dir = os.path.join(music_dir, selected_cat)
                    print(f"[INFO] Algorithm selected: {selected_cat}")
                    break
                elif 1 <= choice_idx <= len(categories):
                    selected_cat = categories[choice_idx - 1]
                    target_dir = os.path.join(music_dir, selected_cat)
                    print(f"[INFO] You selected: {selected_cat}")
                    break
            print("[ERROR] Invalid selection. Please enter a valid number.")

    # Now grab all audio tracks strictly from the target directory
    tracks = []
    for file in os.listdir(target_dir):
        if file.lower().endswith((".mp3", ".wav", ".m4a")):
            tracks.append(os.path.join(target_dir, file))
            
    if not tracks:
        print(f"[WARNING] No audio tracks found in {target_dir}. Proceeding without music.")
        return None
        
    selected_track = random.choice(tracks)
    return selected_track

def get_audio_duration(audio_path):
    """Uses ffprobe to extract the exact length of the audio file in seconds."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
    return float(result.stdout.strip())

def animate_image(image_path, output_path, duration):
    """Applies a cinematic slow zoom (Ken Burns) using FFmpeg's zoompan filter."""
    print(f"[INFO] Animating {os.path.basename(image_path)} ({duration:.2f}s)...")
    
    # The zoompan math: slowly pushes in on the center of the image
    zoom_filter = (
        f"scale=1080x1920,zoompan=z='min(zoom+0.0005,1.5)':d={int(duration*30)}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
    )
    
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-vf", zoom_filter,
        "-c:v", "h264_videotoolbox", # M4 Apple Silicon Hardware Encode
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def render_pipeline():
    print("========================================")
    print("        STATION 5: FFmpeg RENDERER      ")
    print("========================================")
    
    # 1. Path Setup (Using absolute paths to prevent OS confusion)
    base_dir = os.path.abspath(os.getcwd())
    assets_dir = os.path.join(base_dir, "data", "assets")
    subs_path = os.path.join(assets_dir, "subtitles.vtt")
    ass_path = os.path.join(assets_dir, "subtitles.ass")
    fonts_dir = os.path.join(assets_dir, "fonts")
    final_output = os.path.join(base_dir, "data", "final_short.mp4")

    # --- Dynamic Voiceover Discovery ---
    audio_path = None
    for file in os.listdir(assets_dir):
        # We use .lower() so it catches .WAV, .Wav, .mp3, .MP3 safely
        if file.lower().endswith(('.wav', '.mp3')):
            audio_path = os.path.join(assets_dir, file)
            break # We found it, stop searching

    if not audio_path:
        print("[ERROR] No voiceover audio file (.wav or .mp3) found in the assets directory.")
        return # Kill the render if the audio is missing
    
    print(f"[INFO] Voiceover detected: {os.path.basename(audio_path)}")
    
    # 2. Calculate Timings
    print("[INFO] Analyzing audio track...")
    total_duration = get_audio_duration(audio_path)
    
    # Find all generated images
    images = sorted(glob.glob(os.path.join(assets_dir, "scene_*.jpg")))
    if not images:
        print("[ERROR] No images found in data/assets/")
        return
        
    duration_per_scene = total_duration / len(images)
    print(f"[INFO] Total Audio: {total_duration:.2f}s | Allocating {duration_per_scene:.2f}s per scene.")
    
    # 3. Animate Each Scene
    temp_clips = []
    for i, img in enumerate(images):
        temp_clip = os.path.join(assets_dir, f"temp_clip_{i}.mp4")
        animate_image(img, temp_clip, duration_per_scene)
        temp_clips.append(temp_clip)
        
    # 4. Concatenate the Animated Clips
    print("[INFO] Stitching animated clips together...")
    concat_file = os.path.join(assets_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip}'\n")
            
    merged_video = os.path.join(assets_dir, "merged_video.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy", merged_video
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # 5. The Final Burn (Video + Voice + Background Music + Subtitles)
    print("[INFO] Multiplexing neural voice, background music, and subtitles...")
    
    bg_music_path = get_random_bg_music(base_dir)
    
    # The base inputs (Video = 0, Voice = 1)
    final_cmd = [
        "ffmpeg", "-y", 
        "-i", merged_video, 
        "-i", audio_path
    ]

    if bg_music_path:
        print(f"[INFO] Injecting atmospheric track: {os.path.basename(bg_music_path)}")
        
        # Easily tweak your background music volume here (0.15 = 15%, 0.20 = 20%)
        bg_volume = 0.15 
        
        final_cmd.extend(["-i", bg_music_path])
        
        # We dynamically inject the bg_volume variable into the FFmpeg graph
        audio_filter = f"[2:a]volume={bg_volume}[bg];[1:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        
        final_cmd.extend([
            "-filter_complex", audio_filter,
            "-map", "0:v",       # Grab the video
            "-map", "[aout]",    # Grab our newly mixed audio track
            "-c:v", "h264_videotoolbox", 
            "-vf", f"ass='{ass_path}':fontsdir='{fonts_dir}'",
            "-c:a", "aac", "-b:a", "192k",
            final_output
        ])
    else:
        print("[WARNING] No music found in data/music/. Proceeding with voiceover only.")
        final_cmd.extend([
            "-c:v", "h264_videotoolbox", 
            "-vf", f"ass='{ass_path}':fontsdir='{fonts_dir}'",
            "-c:a", "aac", "-b:a", "192k",
            final_output
        ])
        
    subprocess.run(final_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
    print(f"[SUCCESS] Pipeline complete! Final video saved to: {final_output}")
    
    # 6. Cleanup Temporary Files
    for clip in temp_clips:
        os.remove(clip)
    os.remove(concat_file)
    os.remove(merged_video)

    archive_and_cleanup(base_dir, final_output)

if __name__ == "__main__":
    render_pipeline()