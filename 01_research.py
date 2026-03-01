import os
import csv
from dotenv import load_dotenv
from src.scraper import get_youtube_client, get_dynamic_queries, search_target_videos, calculate_outlier_scores
from src.logger import get_factory_logger

logger = get_factory_logger()

def run_research():
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logger.error("Missing YOUTUBE_API_KEY in .env file")
        return

    youtube = get_youtube_client(api_key)
    queries = get_dynamic_queries("niches.txt")
    
    logger.info("========================================")
    logger.info("        STATION 0: RESEARCH PHASE       ")
    logger.info("========================================")

    os.makedirs("data/logs", exist_ok=True)
    all_results = []

    for query in queries:
        videos = search_target_videos(youtube, query, max_results=10) # Increased batch size
        analyzed = calculate_outlier_scores(youtube, videos)
        all_results.extend(analyzed)

    # Sort all results globally by Outlier Score
    all_results.sort(key=lambda x: x["outlier_score"], reverse=True)

    # 1. Terminal Output (A clean, scannable table of the top 5)
    logger.info(f"\n{'OUTLIER':<10} | {'VELOCITY':<10} | {'DAYS OLD':<10} | {'TITLE'}")
    logger.info("-" * 80)
    for vid in all_results[:5]:
        outlier_str = f"{vid['outlier_score']}x"
        vel_str = f"{vid['velocity']}/day"
        logger.info(f"{outlier_str:<10} | {vel_str:<10} | {vid['days_old']:<10} | {vid['title'][:40]}...")

    # 2. CSV Export (The full analytical report)
    csv_path = "data/logs/research_report.csv"
    with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Query", "Title", "Views", "Subscribers", "Outlier Score", "Days Old", "Velocity (Views/Day)", "Video URL"])
        
        for vid in all_results:
            video_url = f"https://www.youtube.com/watch?v={vid['video_id']}"
            writer.writerow([
                vid["query"], 
                vid["title"], 
                vid["views"], 
                vid["subs"], 
                vid["outlier_score"], 
                vid["days_old"], 
                vid["velocity"], 
                video_url
            ])

    logger.info(f"\n[SUCCESS] Full analytical report saved to {csv_path}")
    logger.info("Review the CSV, pick your favorite topic, and run 02_draft.py \"Your Topic\"")

if __name__ == "__main__":
    run_research()