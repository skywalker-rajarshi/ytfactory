import sys
import json
import os
from dotenv import load_dotenv
from src.llm_engine import draft_script, generate_narrative_premise
from src.logger import get_factory_logger
from src.persona_manager import get_persona_selection

logger = get_factory_logger()

def get_factory_inputs():
    """The Master Router: Gathers inputs and determines if middleware is needed."""
    logger.info("\n========================================")
    logger.info("         STATION 1: INPUT ROUTER        ")
    logger.info("========================================")
    
    # 1. Select Input Mode
    print("[1] Direct Topic (e.g., 'Who is Dostoevsky?') -> Bypasses Middleware")
    print("[2] Raw Keywords (e.g., '#space #blackhole') -> Uses Middleware")
    mode = input("Select input mode (1 or 2): ").strip()
    
    raw_input = input("\nEnter your payload: ").strip()
    
    # 2. Fire the Persona Manager (Replaces hardcoded Tone Map)
    persona_instruction = get_persona_selection()
    
    # 3. Execute Routing Logic
    if mode == "2":
        logger.info(f"[INFO] Routing keywords through Middleware to generate premise...")
        final_topic = generate_narrative_premise(raw_input, persona_instruction)
        logger.info(f"\n[SUCCESS] Middleware Output: {final_topic}\n")
    else:
        final_topic = raw_input
        logger.info(f"\n[SUCCESS] Direct Injection: {final_topic}\n")
        
    return final_topic, persona_instruction

def run_drafting():
    load_dotenv()
    os.makedirs("data/logs", exist_ok=True)
    
    # Fire the interactive router
    final_topic, persona_instruction = get_factory_inputs()
    
    logger.info("========================================")
    logger.info("        STATION 2: SCRIPT DRAFTING      ")
    logger.info("========================================")
    
    logger.info("[INFO] Drafting highly optimized Shorts script...")
    
    # Pass both the topic and the persona to the backend engine
    script_json = draft_script(final_topic, persona_instruction) 
    
    if not script_json:
        logger.error(f"Script drafting failed for topic: {final_topic}")
        sys.exit(1)

    output_path = "data/logs/latest_script.json"
    with open(output_path, "w") as f:
        json.dump(script_json, f, indent=2)
        
    logger.info(f"[SUCCESS] Script saved to {output_path}")

if __name__ == "__main__":
    run_drafting()