from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import os

current_dir = os.getcwd()
font_path = os.path.join(current_dir, "data", "assets", "fonts", "Montserrat-Bold.ttf")

def parse_vtt_time(time_str):
    """Converts VTT timestamp (00:00:01.230) to seconds."""
    parts = time_str.replace(',', '.').split(':')
    seconds = float(parts[-1])
    minutes = int(parts[-2])
    hours = int(parts[-3]) if len(parts) > 2 else 0
    return hours * 3600 + minutes * 60 + seconds

def get_subtitles(vtt_path):
    """Parses the VTT file into a list of subtitle dictionaries."""
    subs = []
    if not os.path.exists(vtt_path):
        return subs

    with open(vtt_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
        
    i = 0
    while i < len(lines):
        if '-->' in lines[i]:
            times = lines[i].split(' --> ')
            start = parse_vtt_time(times[0].strip())
            end = parse_vtt_time(times[1].strip())
            i += 1
            text = lines[i].strip()
            subs.append({"start": start, "end": end, "text": text})
        i += 1
    return subs

def create_video(audio_path, image_paths, vtt_path, output_filename="data/assets/final_video.mp4"):
    print(f"\n[INFO] Assembling multi-scene video with hardcoded subtitles...")

    try:
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        time_per_image = total_duration / len(image_paths)

        # 1. Stitch Background Images
        clips = []
        for img_path in image_paths:
            if os.path.exists(img_path):
                clip = ImageClip(img_path).with_duration(time_per_image)
                clips.append(clip)
        
        base_video = concatenate_videoclips(clips, method="compose")

        # 2. Generate Subtitle Clips
        print("[INFO] Overlaying text graphics...")
        subs_data = get_subtitles(vtt_path)
        subtitle_clips = []
        
        for sub in subs_data:
            # MoviePy v2.0 syntax for TextClip
            txt_clip = TextClip(
                font=font_path, # Change to any font installed on your Mac
                text=sub['text'],
                font_size=90,
                color='white',
                stroke_color='black',
                stroke_width=3
            ).with_position('center').with_start(sub['start']).with_end(sub['end'])
            
            subtitle_clips.append(txt_clip)

        # 3. Composite everything together
        final_video = CompositeVideoClip([base_video] + subtitle_clips)
        final_video = final_video.with_audio(audio_clip)

        print("[INFO] Rendering final MP4 via Apple Silicon Hardware Engine...")
        final_video.write_videofile(
            output_filename,
            fps=24,
            codec="h264_videotoolbox", # Routes to the M-series hardware media engine
            audio_codec="aac",
            bitrate="8000k",           # Ensures high quality for Shorts
            logger=None                # (preset and threads are largely ignored by videotoolbox)
        )
        

        audio_clip.close()
        final_video.close()
        base_video.close()

        print(f"[SUCCESS] Video rendered successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Video assembly failed: {e}")
        return False