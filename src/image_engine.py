import os
import requests
import time
import random

def generate_all_images(script_json, base_filename="data/assets/scene"):
    master_seed = random.randint(1, 999999)
    print(f"[INFO] Locking visual consistency with Master Seed: {master_seed}")
    print("[INFO] Generating images via Replicate HTTP API with Exponential Backoff...")

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

        output_filename = f"{base_filename}_{scene_num}.jpg"

        payload = {
            "input": {
                "prompt": visual_prompt, # Trusting the LLM prose directly
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
                
                # If we hit the rate limit, trigger the backoff
                if response.status_code == 429:
                    wait_time = base_delay * (2 ** attempt) # 10s, 20s, 40s...
                    print(f"[WARNING] 429 Rate Limit hit. Retrying Scene {scene_num} in {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                
                # If it's a different error, this will raise it
                response.raise_for_status()
                prediction = response.json()
                
                # Break out of the retry loop if the POST request succeeded
                break 
                
            except Exception as e:
                print(f"[ERROR] HTTP request failed: {e}")
                # If it's not a 429, we still want to retry just in case it's a network blip
                time.sleep(base_delay)
                
        else:
            print(f"[ERROR] Scene {scene_num} permanently failed after {max_retries} retries. Skipping.")
            continue

        # --- THE POLLING LOOP ---
        try:
            while prediction["status"] not in ["succeeded", "failed", "canceled"]:
                time.sleep(2) # Increased polling delay to prevent secondary rate limits
                poll_resp = requests.get(prediction["urls"]["get"], headers=headers)
                poll_resp.raise_for_status()
                prediction = poll_resp.json()

            if prediction["status"] != "succeeded":
                print(f"[ERROR] Scene {scene_num} generation failed on Replicate's end: {prediction.get('error')}")
                continue

            image_url = prediction["output"][0]
            img_data = requests.get(image_url).content
            
            with open(output_filename, "wb") as handler:
                handler.write(img_data)
            
            print(f"[SUCCESS] Scene {scene_num} saved to {output_filename}")
            image_paths.append(output_filename)

        except Exception as e:
            print(f"[ERROR] Failed to download or poll Scene {scene_num}: {e}")

        # A baseline 5-second rest before moving to the NEXT scene
        print("[INFO] Resting for 5 seconds before next scene...")
        time.sleep(5)

    return image_paths