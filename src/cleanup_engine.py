import os
import shutil
import datetime
import time

def enforce_retention_policy(base_dir, days_to_keep=1):
    """The Garbage Collector: Scans the image archive and deletes expired files."""
    print("[INFO] Enforcing 24-hour TTL (Time-To-Live) on archived images...")
    image_archive_dir = os.path.join(base_dir, "data", "archives", "images")
    os.makedirs(image_archive_dir, exist_ok=True)
    
    current_time = time.time()
    retention_seconds = days_to_keep * 86400 # 86,400 seconds in a day
    
    deleted_count = 0
    for filename in os.listdir(image_archive_dir):
        file_path = os.path.join(image_archive_dir, filename)
        if os.path.isfile(file_path):
            # Check the file's last modified timestamp
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > retention_seconds:
                os.remove(file_path)
                deleted_count += 1
                
    if deleted_count > 0:
        print(f"[CLEANUP] Garbage Collector removed {deleted_count} expired images.")

def archive_and_cleanup(base_dir, final_output):
    """Moves the video and images to archives, deletes ephemeral assets, and triggers GC."""
    print("\n========================================")
    print("        FACTORY RESET & ARCHIVING       ")
    print("========================================")
    
    # --- 1. THE FAIL-SAFE ---
    if not os.path.exists(final_output):
        print("[ERROR] Final video not found! Halting cleanup to preserve assets for debugging.")
        return
        
    # --- 2. ARCHIVE THE VIDEO ---
    archive_dir = os.path.join(base_dir, "data", "archives")
    os.makedirs(archive_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_video_path = os.path.join(archive_dir, f"short_{timestamp}.mp4")
    shutil.move(final_output, archived_video_path)
    print(f"[SUCCESS] Final video archived to: {archived_video_path}")

    # --- 3. SWEEP THE FLOOR & ARCHIVE IMAGES ---
    image_archive_dir = os.path.join(archive_dir, "images")
    os.makedirs(image_archive_dir, exist_ok=True)
    assets_dir = os.path.join(base_dir, "data", "assets")
    
    print("[INFO] Archiving images and sweeping ephemeral data...")
    for filename in os.listdir(assets_dir):
        file_path = os.path.join(assets_dir, filename)
        
        if os.path.isfile(file_path): 
            if filename.endswith(".jpg"):
                archived_img_path = os.path.join(image_archive_dir, f"{timestamp}_{filename}")
                shutil.move(file_path, archived_img_path)
            else:
                os.remove(file_path)
                
    # --- 4. RUN THE GARBAGE COLLECTOR ---
    enforce_retention_policy(base_dir)
    print("[SUCCESS] Factory floor wiped clean. Pipeline ready for next run.")