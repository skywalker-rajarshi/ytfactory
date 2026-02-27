import sys
import json
import os
from dotenv import load_dotenv
from src.llm_engine import draft_script, generate_narrative_premise
from src.logger import get_factory_logger

logger = get_factory_logger()

def run_drafting(raw_input):
    load_dotenv()
    logger.info("========================================")
    logger.info("        STATION 2: SCRIPT DRAFTING      ")
    logger.info("========================================")
    
    os.makedirs("data/logs", exist_ok=True)
    
    # 1. The Middleware Translation
    logger.info(f"[INFO] Raw Input Received: {raw_input}")
    logger.info("[INFO] Generating Provocative Premise...")
    
    premise = generate_narrative_premise(raw_input)
    logger.info(f"\n[DIRECTIVE] => {premise}\n")
    
    # 2. The Main Script Generation
    logger.info("[INFO] Drafting highly optimized Shorts script...")
    script_json = draft_script(premise) # Pass the expanded premise, not the hashtags
    
    if not script_json:
        logger.error(f"Script drafting failed for topic: {premise}")
        sys.exit(1)

    output_path = "data/logs/latest_script.json"
    with open(output_path, "w") as f:
        json.dump(script_json, f, indent=2)
        
    logger.info(f"[SUCCESS] Script saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Missing topic argument. Usage: python3 02_draft.py \"Topic\"")
        sys.exit(1)
    
    target_topic = sys.argv[1]
    run_drafting(target_topic)