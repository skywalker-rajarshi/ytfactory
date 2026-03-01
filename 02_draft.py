import sys
import json
import os
from dotenv import load_dotenv
from src.llm_engine import draft_script, generate_narrative_premise
from src.logger import get_factory_logger

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
    
    # 2. Select Tone Profile
    print("\nSelect the Tone Profile:")
    print("[1] Existential & Cinematic (Heavy, melancholic, introspective)")
    print("[2] Hard Science & Factual (Objective, educational, clear)")
    print("[3] Fast-Paced Tech (Punchy, analytical, systems-focused)")
    print("[4] Dark Historical (Gritty, grounded, biographical)")
    tone_choice = input("Select tone (1-4): ").strip()
    
    tone_map = {
        "1": "heavy, melancholic, and deeply introspective.",
        "2": "highly factual, objective, educational, and clear. Avoid overly poetic language.",
        "3": "punchy, analytical, high-energy, focusing on systems and mechanics.",
        "4": "gritty, grounded, biographical, focusing on realities without over-romanticizing."
    }
    tone_profile = tone_map.get(tone_choice, tone_map["1"])
    
    # 3. Execute Routing Logic
    if mode == "2":
        logger.info(f"[INFO] Routing keywords through Middleware to generate premise...")
        final_topic = generate_narrative_premise(raw_input, tone_profile)
        logger.info(f"\n[SUCCESS] Middleware Output: {final_topic}\n")
    else:
        final_topic = raw_input
        logger.info(f"\n[SUCCESS] Direct Injection: {final_topic}\n")
        
    return final_topic, tone_profile

def run_drafting():
    load_dotenv()
    os.makedirs("data/logs", exist_ok=True)
    
    # Fire the interactive router
    final_topic, tone_profile = get_factory_inputs()
    
    logger.info("========================================")
    logger.info("        STATION 2: SCRIPT DRAFTING      ")
    logger.info("========================================")
    
    logger.info("[INFO] Drafting highly optimized Shorts script...")
    
    # Pass both the topic and the tone to the backend engine
    script_json = draft_script(final_topic, tone_profile) 
    
    if not script_json:
        logger.error(f"Script drafting failed for topic: {final_topic}")
        sys.exit(1)

    output_path = "data/logs/latest_script.json"
    with open(output_path, "w") as f:
        json.dump(script_json, f, indent=2)
        
    logger.info(f"[SUCCESS] Script saved to {output_path}")

if __name__ == "__main__":
    run_drafting()