import string
import requests
import json
import os
from dotenv import load_dotenv
from src.llm_engine import draft_script # Re-using your Gemini connection
from google import genai

def get_youtube_suggestions(seed_word):
    """Scrapes the undocumented YouTube Auto-Suggest API using the alphabet soup method."""
    print(f"[INFO] Mining YouTube Auto-Suggest for seed: '{seed_word}'...")
    suggestions = []
    
    # We query the seed word + a space + every letter of the alphabet
    search_queries = [f"{seed_word} "] + [f"{seed_word} {letter}" for letter in string.ascii_lowercase]
    
    for query in search_queries:
        # This is the hidden endpoint browsers use for dropdown suggestions
        url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={query}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # The API returns a list where the second item is the list of suggestions
                data = json.loads(response.text)
                suggestions.extend(data[1])
        except Exception as e:
            print(f"[WARNING] Failed to fetch suggestions for {query}: {e}")
            
    # Remove duplicates and clean up
    unique_suggestions = list(set(suggestions))
    print(f"[SUCCESS] Extracted {len(unique_suggestions)} raw human search queries.")
    return unique_suggestions

def refine_ideas_with_llm(raw_queries):
    """Passes the boring raw queries to Gemini to turn them into viral Short concepts."""
    print("[INFO] Pushing raw data to Gemini for creative refinement...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    queries_text = "\n".join(raw_queries)
    
    prompt = f"""
    You are a YouTube Shorts strategist. Below is a list of actual, data-backed search queries humans are typing into YouTube.
    Most of them are boring. I need you to find the underlying interests in this data and generate 10 highly engaging, 
    slightly melancholic or terrifying YouTube Shorts concepts based on them.
    
    Format the output as a simple list of 10 titles, one per line, with no numbers or bullet points.
    
    RAW QUERIES:
    {queries_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
        )
        # Split the text block into a clean Python list
        refined_ideas = [line.strip() for line in response.text.split('\n') if line.strip()]
        return refined_ideas
    except Exception as e:
        print(f"[ERROR] LLM refinement failed: {e}")
        return []

def run_discovery(seed_word):
    load_dotenv()
    print("========================================")
    print("      STATION 0: THE DISCOVERY ENGINE   ")
    print("========================================")
    
    raw_data = get_youtube_suggestions(seed_word)
    
    if not raw_data:
        print("[ERROR] No data found.")
        return
        
    viral_concepts = refine_ideas_with_llm(raw_data)
    
    if viral_concepts:
        with open("niches.txt", "w") as f:
            for concept in viral_concepts:
                f.write(f"{concept}\n")
        print("\n[SUCCESS] niches.txt has been populated with 10 hybrid viral concepts!")
        print("You can now run 'python3 01_research.py' to analyze their performance.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("[ERROR] Provide a seed word. Usage: python3 00_discovery.py \"space\"")
        sys.exit(1)
        
    seed = sys.argv[1]
    run_discovery(seed)