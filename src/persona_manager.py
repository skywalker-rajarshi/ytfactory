import json
import os

def load_personas():
    """Fetches the personas from the external JSON configuration."""
    # Maps to your absolute path: config/personas.json
    config_path = os.path.join(os.path.abspath(os.getcwd()), "config", "personas.json")
    
    if not os.path.exists(config_path):
        print(f"[ERROR] Persona config not found at {config_path}")
        return {}
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_persona_selection():
    """Presents the dynamic menu and returns the selected persona's prompt instructions."""
    personas = load_personas()
    
    if not personas:
        return "Adopt a highly engaging, cinematic tone." # Fallback
        
    print("\nSelect the Director's Persona:")
    for key, data in personas.items():
        print(f"[{key}] {data['name']}")
    print("[0] Custom Persona (Type your own constraints)")
    
    while True:
        choice = input("\nSelect persona (0 or key): ").strip()
        
        if choice == "0":
            return input("Enter custom rhetorical constraints: ")
            
        if choice in personas:
            selected = personas[choice]
            print(f"[INFO] Persona locked: {selected['name']}")
            return selected["prompt"]
            
        print("[ERROR] Invalid selection.")