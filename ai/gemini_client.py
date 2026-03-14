from google import genai
from app.config import config

client = genai.Client(api_key=config.GEMINI_API_KEY)

def analyze_codebase_structure(structure_text: str) -> str:
    # return "API working successfully"
    prompt = f"""
You are a senior software architect.

Analyze the following repository file structure and explain:
- what the project likely does
- the main components
- the architecture style.

Repository structure:
{structure_text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        return f"Gemini API Error: {str(e)}"