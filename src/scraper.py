from googleapiclient.discovery import build
from datetime import datetime, timezone
import time

def get_youtube_client(api_key):
    """Initializes and returns the YouTube Data API client."""
    return build("youtube", "v3", developerKey=api_key)

def get_dynamic_queries(filepath="niches.txt"):
    """Reads search queries from a file."""
    try:
        with open(filepath, "r") as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"[WARNING] {filepath} not found. Returning empty list.")
        return []

def search_target_videos(youtube, query, max_results=10):
    """Searches YouTube specifically for Shorts and captures publish dates."""
    print(f"[INFO] Searching YouTube Shorts for: '{query}'...")
    
    # 1. Append #shorts to the query to force the algorithm's hand
    shorts_query = f"{query} #shorts"
    
    search_response = youtube.search().list(
        q=shorts_query,
        part="id,snippet",
        type="video",
        videoDuration="short", # 2. Native API filter: strictly limits to videos under 4 minutes
        order="relevance",     # 3. Pulls videos with actual algorithmic traction
        maxResults=max_results
    ).execute()

    videos = []
    for item in search_response.get("items", []):
        videos.append({
            "query": query,
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel_id": item["snippet"]["channelId"],
            "channel_title": item["snippet"]["channelTitle"],
            "published_at": item["snippet"]["publishedAt"]
        })
    return videos

def calculate_outlier_scores(youtube, videos_data):
    """Calculates Outlier Score and Velocity (Views per Day)."""
    if not videos_data: return []

    video_ids = ",".join([vid["video_id"] for vid in videos_data])
    channel_ids = ",".join({vid["channel_id"] for vid in videos_data})
    
    video_response = youtube.videos().list(part="statistics", id=video_ids).execute()
    video_stats = {item["id"]: int(item["statistics"].get("viewCount", 0)) for item in video_response.get("items", [])}
        
    channel_response = youtube.channels().list(part="statistics", id=channel_ids).execute()
    channel_stats = {item["id"]: int(item["statistics"].get("subscriberCount", 0)) for item in channel_response.get("items", [])}
        
    outlier_results = []
    current_time = datetime.now(timezone.utc)

    for vid in videos_data:
        views = video_stats.get(vid["video_id"], 0)
        subs = channel_stats.get(vid["channel_id"], 0)
        outlier_score = round(views / subs, 2) if subs > 0 else 0
        
        # Calculate Age and Velocity
        published_date = datetime.strptime(vid["published_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        days_old = (current_time - published_date).days
        days_old = max(1, days_old) # Prevent division by zero
        velocity = round(views / days_old, 2)
        
        vid.update({
            "views": views, 
            "subs": subs, 
            "outlier_score": outlier_score,
            "days_old": days_old,
            "velocity": velocity
        })
        outlier_results.append(vid)
        
    outlier_results.sort(key=lambda x: x["outlier_score"], reverse=True)
    return outlier_results