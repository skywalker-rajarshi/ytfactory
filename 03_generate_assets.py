import os
import json
import asyncio
from dotenv import load_dotenv
from src.audio_engine import generate_audio
from src.image_engine import generate_all_images
from src.logger import get_factory_logger

logger = get_factory_logger()

async def run_asset_generation():
    load_dotenv()
    logger.info("========================================")
    logger.info("      STATION 3: ASSET GENERATION       ")
    logger.info("========================================")
    
    os.makedirs("data/assets", exist_ok=True)
    
    try:
        with open("data/logs/latest_script.json", "r") as f:
            script_json = json.load(f)
    except FileNotFoundError:
        logger.error("latest_script.json not found. Run 02_draft.py first.")
        return

    # Generate Audio
    audio_path = "data/assets/audio.wav"
    vtt_path = "data/assets/subtitles.vtt"
    ass_path = "data/assets/subtitles.ass"
    
    # 1. Generate Audio & Dual Subtitles
    await generate_audio(script_json, audio_path, vtt_path, ass_path)

    # # Generate Images
    # base_image_path = "data/assets/scene"
    # generate_all_images(script_json, base_filename=base_image_path)
    
    # logger.info("[SUCCESS] All assets generated in data/assets/")

if __name__ == "__main__":
    asyncio.run(run_asset_generation())