import os
import glob
from src.video_engine import create_video
from src.logger import get_factory_logger

logger = get_factory_logger()

def run_render():
    logger.info("========================================")
    logger.info("        STATION 4: VIDEO ASSEMBLY       ")
    logger.info("========================================")
    
    audio_path = "data/assets/voiceover.mp3"
    subs_path = "data/assets/subtitles.vtt"
    
    # Grab all generated scene images and sort them alphabetically so they stay in order
    image_paths = sorted(glob.glob("data/assets/scene_*.jpg"))
    
    output_filename = "data/assets/FINAL_OUTPUT.mp4"

    if not image_paths:
        logger.error("No images found in data/assets/. Run 03_generate_assets.py first.")
        return

    success = create_video(audio_path, image_paths, subs_path, output_filename)
    
    if success:
        logger.info(f"\n[SUCCESS] Video ready for upload: {output_filename}")
    else:
        logger.error("Video assembly failed during rendering.")

if __name__ == "__main__":
    run_render()