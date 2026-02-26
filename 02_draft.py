import sys
import json
import os
from dotenv import load_dotenv
from src.llm_engine import draft_script
from src.logger import get_factory_logger

logger = get_factory_logger()

def run_drafting(topic):
    load_dotenv()
    logger.info("========================================")
    logger.info("        STATION 2: SCRIPT DRAFTING      ")
    logger.info("========================================")
    
    script_json = draft_script(topic)
    if not script_json:
        # This will print to terminal AND permanently save to data/logs/error_log.txt
        logger.error(f"Script drafting failed for topic: {topic}")
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