import os
import requests
import time
import random

def generate_all_images(script_json, base_filename="data/assets/scene"):
    # 1. Generate a single master seed for this specific video
    master_seed = random.randint(1, 999999)
    print(f"[INFO] Locking visual consistency with Master Seed: {master_seed}")

    """Loops through the JSON script and generates an image for every scene."""
    print("[INFO] Generating images for all scenes via Replicate HTTP API...")

    image_paths = []
    api_token = os.getenv("REPLICATE_API_TOKEN")
    
    if not api_token:
        print("[ERROR] Missing REPLICATE_API_TOKEN in .env file.")
        return []

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Prefer": "wait"
    }
    
    scenes = script_json.get("scenes", [])
    if not scenes:
        print("[ERROR] No scenes found in the JSON script.")
        return []

    for index, scene in enumerate(scenes):
        scene_num = index + 1
        print(f"\n[INFO] Processing Scene {scene_num}/{len(scenes)}...")
        
        visual_prompt = scene.get("visual_idea", "")
        if not visual_prompt:
            print(f"[WARNING] No visual prompt for scene {scene_num}, skipping.")
            continue

        enhanced_prompt = f"{visual_prompt}, cinematic lighting, 8k resolution, highly detailed, atmospheric, vivid colors"
        output_filename = f"{base_filename}_{scene_num}.jpg"

        payload = {
            "input": {
                "prompt": enhanced_prompt,
                "aspect_ratio": "9:16",
                "output_format": "jpg",
                "num_outputs": 1,
                "output_quality": 100,
                "num_inference_steps": 4,
                "go_fast": True,
                "seed": master_seed
            }
        }

        try:
            endpoint = "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions"
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            prediction = response.json()

            while prediction["status"] not in ["succeeded", "failed", "canceled"]:
                time.sleep(1)
                poll_resp = requests.get(prediction["urls"]["get"], headers=headers)
                poll_resp.raise_for_status()
                prediction = poll_resp.json()

            if prediction["status"] != "succeeded":
                print(f"[ERROR] Scene {scene_num} failed: {prediction.get('error')}")
                continue

            image_url = prediction["output"][0]
            img_data = requests.get(image_url).content
            
            with open(output_filename, "wb") as handler:
                handler.write(img_data)
            
            print(f"[SUCCESS] Scene {scene_num} saved to {output_filename}")
            image_paths.append(output_filename)

        except Exception as e:
            print(f"[ERROR] HTTP request failed for Scene {scene_num}: {e}")

    return image_paths