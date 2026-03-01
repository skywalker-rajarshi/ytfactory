import os
import subprocess

def harvest_playlist(url, category_name):
    """Downloads an entire YouTube playlist as MP3s into a categorized vault."""
    print(f"\n[INFO] Initializing Harvester for category: {category_name.upper()}")
    
    base_dir = os.path.abspath(os.getcwd())
    vault_dir = os.path.join(base_dir, "data", "music", category_name)
    os.makedirs(vault_dir, exist_ok=True)
    
    # We command yt-dlp to extract audio, convert to high-quality mp3, 
    # and name the file cleanly inside the target directory.
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0", # 0 is best quality
        "-o", f"{vault_dir}/%(title)s.%(ext)s",
        "--yes-playlist",
        url
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[SUCCESS] Vault populated: {vault_dir}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Harvester failed: {e}")

if __name__ == "__main__":
    # Example: Ripping a royalty-free dark ambient playlist
    print("========================================")
    print("           THE VAULT HARVESTER          ")
    print("========================================")
    playlist_url = input("Enter YouTube Playlist/Video URL: ")
    category = input("Enter Vibe Category (e.g., surreal_dread, ethereal_synth): ")
    
    if playlist_url and category:
        harvest_playlist(playlist_url, category.replace(" ", "_"))