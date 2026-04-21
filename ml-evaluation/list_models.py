import google.generativeai as genai
from dotenv import load_dotenv
import os

# test1234

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

print("=== Generation models ===")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)

print("\n=== Embedding models ===")
for m in genai.list_models():
    if 'embedContent' in m.supported_generation_methods:
        print(m.name)