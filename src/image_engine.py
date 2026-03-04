import os
import requests
import time
import random
import json
from PIL import Image, ImageStat
from src.archive_fetcher import get_archival_image

def is_image_corrupted(file_path):
    """Checks if an image is dead via file size OR pixel variance."""
    if not os.path.exists(file_path):
        return True
        
    file_size_kb = os.path.getsize(file_path) / 1024
    if file_size_kb < 10:
        print(f"[WARNING] Image too small ({file_size_kb:.2f} KB).")
        return True
        
    try:
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            stat = ImageStat.Stat(img)
            if sum(stat.var) < 1.0:
                print(f"[WARNING] Image lacks visual data. It is likely blank.")
                return True
    except Exception as e:
        print(f"[WARNING] Pillow could not read the image data: {e}")
        return True
        
    return False

def generate_flux_image_replicate(prompt, output_filename, master_seed):
    """Your original Replicate engine, adapted to run scene-by-scene."""
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("[ERROR] Missing REPLICATE_API_TOKEN in .env file.")
        return False

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Prefer": "wait"
    }
    
    payload = {
        "input": {
            "prompt": prompt, 
            "aspect_ratio": "9:16",
            "output_format": "jpg",
            "num_outputs": 1,
            "output_quality": 100,
            "num_inference_steps": 4,
            "go_fast": True,
            "seed": master_seed
        }
    }

    endpoint = "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions"
    max_retries = 5
    base_delay = 10

    # --- THE EXPONENTIAL BACKOFF RETRY LOOP ---
    for attempt in range(max_retries):
        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            
            if response.status_code == 429:
                wait_time = base_delay * (2 ** attempt)
                print(f"[WARNING] 429 Rate Limit hit. Retrying in {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            prediction = response.json()
            break 
            
        except Exception as e:
            print(f"[ERROR] HTTP request failed: {e}")
            time.sleep(base_delay)
    else:
        print(f"[ERROR] Permanently failed after {max_retries} retries.")
        return False

    # --- THE POLLING LOOP ---
    try:
        while prediction["status"] not in ["succeeded", "failed", "canceled"]:
            time.sleep(2) 
            poll_resp = requests.get(prediction["urls"]["get"], headers=headers)
            poll_resp.raise_for_status()
            prediction = poll_resp.json()

        if prediction["status"] != "succeeded":
            print(f"[ERROR] Generation failed on Replicate's end: {prediction.get('error')}")
            return False

        image_url = prediction["output"][0]
        img_data = requests.get(image_url).content
        
        with open(output_filename, "wb") as handler:
            handler.write(img_data)
        
        print(f"[SUCCESS] AI Asset saved to {output_filename}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to download or poll: {e}")
        return False

def generate_all_images(script_json, base_filename="data/assets/scene"):
    """
    The Decision Router: Tries Archive first, falls back to Replicate/Flux.
    """
    os.makedirs(os.path.dirname(base_filename), exist_ok=True)
    master_seed = random.randint(1, 999999)
    print(f"\n[INFO] Locking visual consistency with Master Seed: {master_seed}")
    
    print("========================================")
    print("        STATION 2: ASSET ROUTER         ")
    print("========================================")
    
    scenes = script_json.get("scenes", [])
    if not scenes:
        print("[ERROR] No scenes found in the JSON script.")
        return []

    image_paths = []

    for index, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", index + 1)
        asset_type = scene.get("asset_type", "ai")
        output_path = f"{base_filename}_{scene_num}.jpg"
        
        print(f"\n[INFO] Processing Scene {scene_num} (Asset Type: {asset_type})...")
        success = False
        
        # --- ATTEMPT 1: Archival Fetch ---
        if asset_type in ["archive_wikimedia", "archive_nasa"]:
            source = "nasa" if "nasa" in asset_type else "wikimedia"
            query = scene.get("archive_query")
            
            if query:
                print(f"[INFO] Attempting to fetch '{query}' from {source}...")
                fetched = get_archival_image(query, output_path, source)
                
                # Check for the "Black JPG" error
                if fetched and not is_image_corrupted(output_path):
                    success = True
                    image_paths.append(output_path)
                elif fetched:
                    os.remove(output_path) # Delete the corrupted file
            else:
                print("[WARNING] Asset type is archive, but no archive_query was provided.")
                
        # --- ATTEMPT 2: Replicate/Flux Fallback (Self-Healing) ---
        if not success:
            if asset_type != "ai":
                print("[INFO] Archival fetch failed or returned invalid data. Triggering AI Fallback.")
                
            print(f"[INFO] Generating cinematic AI image via Replicate (flux-schnell)...")
            ai_prompt = scene.get("ai_prompt")
            
            if ai_prompt:
                if generate_flux_image_replicate(ai_prompt, output_path, master_seed):
                    image_paths.append(output_path)
            else:
                print(f"[ERROR] No ai_prompt available to fallback on for scene {scene_num}!")
                
        # Baseline rest before next scene
        print("[INFO] Resting for 5 seconds before next scene...")
        time.sleep(5)

    return image_paths
