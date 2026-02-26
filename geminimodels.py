import google.generativeai as genai
import keys

# Paste your API key here
genai.configure(api_key=keys.GEMINI_API_KEY)

print("Available Models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)