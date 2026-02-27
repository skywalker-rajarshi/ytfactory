import os
import glob
import subprocess
import json
from src.cleanup_engine import archive_and_cleanup

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
    print("        STATION 4: FFmpeg RENDERER      ")
    print("========================================")
    
    # 1. Path Setup (Using absolute paths to prevent OS confusion)
    base_dir = os.path.abspath(os.getcwd())
    assets_dir = os.path.join(base_dir, "data", "assets")
    audio_path = os.path.join(assets_dir, "voiceover.mp3")
    subs_path = os.path.join(assets_dir, "subtitles.vtt")
    ass_path = os.path.join(assets_dir, "subtitles.ass")
    fonts_dir = os.path.join(assets_dir, "fonts")
    final_output = os.path.join(base_dir, "data", "final_short.mp4")
    
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
    
    # 5. The Final Burn (Audio + Subtitles + Hardware Acceleration)
    print("[INFO] Burning subtitles and multiplexing audio...")
    
    # FFmpeg requires a specific syntax to pass the custom font directory and styling
    # We use Montserrat-Bold, size 24, center aligned (Alignment=2), with a nice margin
    style = "Fontname=Montserrat-Bold,Fontsize=22,PrimaryColour=&H00FFFF,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=150"
    
    final_cmd = [
        "ffmpeg", "-y", 
        "-i", merged_video, 
        "-i", audio_path,
        "-c:v", "h264_videotoolbox", 
        "-vf", f"ass='{ass_path}':fontsdir='{fonts_dir}'", # Uses the native ASS filter
        "-c:a", "aac", "-b:a", "192k",
        final_output
    ]
    
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