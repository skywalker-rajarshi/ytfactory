import os
import requests
from io import BytesIO
from PIL import Image, ImageFilter

def fetch_wikimedia_image_url(query):
    """Hits the Wikimedia Commons API to find the top public domain image for a query."""
    print(f"[INFO] Searching Wikimedia Archives for: '{query}'...")
    
    # Wikimedia requires a User-Agent for API requests
    headers = {
        "User-Agent": "ShortsFactory/1.0 (Automated Documentary Pipeline)"
    }
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": "6", # '6' restricts the search strictly to Files/Images
        "gsrsearch": f"{query} filetype:bitmap",
        "gsrlimit": "1",     # We only want the top result
        "prop": "imageinfo",
        "iiprop": "url"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            print("[WARNING] No archival images found for that query.")
            return None
        
        # Extract the direct image URL from the confusing Wikimedia JSON structure
        first_page = list(pages.values())[0]
        image_url = first_page.get("imageinfo", [{}])[0].get("url")
        return image_url
        
    except Exception as e:
        print(f"[ERROR] Archive fetch failed: {e}")
        return None
    
def fetch_nasa_image_url(query):
    """Hits the NASA Image API and extracts a high-res .jpg file."""
    print(f"[INFO] Searching NASA Archives for: '{query}'...")
    url = "https://images-api.nasa.gov/search"
    params = {
        "q": query,
        "media_type": "image"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("collection", {}).get("items", [])
        if not items:
            print("[WARNING] No NASA images found for that query.")
            return None
            
        # NASA's API is a bit nested. The initial search gives us a 'collection' URL 
        # that contains all the different resolutions for the image.
        collection_url = items[0].get("href")
        if not collection_url:
            return None
            
        # Hit the collection URL to get the array of actual image links
        collection_response = requests.get(collection_url)
        collection_urls = collection_response.json()
        
        # We want a high-res JPEG, but we want to avoid massive 100MB .tif files 
        # or tiny thumbnails, so we filter the list.
        jpg_urls = [u for u in collection_urls if u.endswith('.jpg') and '~thumb' not in u]
        
        # Grab the highest quality JPEG available
        image_url = jpg_urls[0] if jpg_urls else collection_urls[0]
        
        # NASA's API sometimes returns http instead of https, which causes security blocks.
        image_url = image_url.replace("http://", "https://")
        return image_url
        
    except Exception as e:
        print(f"[ERROR] NASA fetch failed: {e}")
        return None

def normalize_for_shorts(image_bytes, output_path):
    """
    Takes any archival image, creates a 1080x1920 blurred background, 
    and centers the original image to prevent FFmpeg crashes.
    """
    target_size = (1080, 1920)
    
    # Open the raw downloaded image
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    print(f"[INFO] Raw archive resolution: {img.width}x{img.height}")
    
    # 1. --- Create the Blurred Background ---
    img_ratio = img.width / img.height
    target_ratio = target_size[0] / target_size[1]
    
    # Calculate how to scale the image so it completely fills the 1080x1920 background
    if img_ratio > target_ratio:
        new_height = target_size[1]
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_size[0]
        new_height = int(new_width / img_ratio)
        
    bg = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Crop the exact center of the scaled image
    left = (new_width - target_size[0]) / 2
    top = (new_height - target_size[1]) / 2
    right = (new_width + target_size[0]) / 2
    bottom = (new_height + target_size[1]) / 2
    bg = bg.crop((left, top, right, bottom))
    
    # Apply a heavy cinematic blur and darken it by 40% so the foreground text pops
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    bg = bg.point(lambda p: p * 0.6) 

    # 2. --- Add the Crisp Foreground Image ---
    fg = img.copy()
    fg.thumbnail(target_size, Image.Resampling.LANCZOS) # Scale down to fit inside 1080x1920
    
    # Calculate exact center paste coordinates
    paste_x = (target_size[0] - fg.width) // 2
    paste_y = (target_size[1] - fg.height) // 2
    
    # Paste the crisp image onto the dark, blurred background
    bg.paste(fg, (paste_x, paste_y))
    
    # Save the final normalized asset
    bg.save(output_path, "JPEG", quality=95)
    print(f"[SUCCESS] Normalized archival asset saved to: {output_path}")

def get_archival_image(query, output_path, source="wikimedia"):
    """Master function to orchestrate the fetch and normalization from multiple databases."""
    if source == "nasa":
        image_url = fetch_nasa_image_url(query)
    else:
        image_url = fetch_wikimedia_image_url(query)
    
    if not image_url:
        return False
        
    print(f"[INFO] Downloading artifact: {image_url}")
    
    headers = {
        "User-Agent": "ShortsFactory/1.0 (Automated Documentary Pipeline)"
    }
    
    try:
        response = requests.get(image_url, headers=headers)
        response.raise_for_status()
        
        normalize_for_shorts(response.content, output_path)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to process image: {e}")
        return False
