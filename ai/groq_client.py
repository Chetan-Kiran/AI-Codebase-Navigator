from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_codebase_structure(structure: str, code: str):

    prompt = f"""
You are a senior software architect.

Analyze the following repository.

IMPORTANT RULES:
- Only use the information given
- Do not guess technologies
- If unsure, say "not enough information"

REPOSITORY STRUCTURE
{structure}

CODE SNIPPETS
{code}

Explain:

1. What the project likely does
2. Architecture
3. Technologies used
4. Main components
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content

def ask_question_about_repo(context: str):

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": context}],
        temperature=0.2
    )

    return response.choices[0].message.content

def summarize_commits(commits: str):

    if not commits:
        return "No commits to summarize"

    try:
        prompt = f"""
You are a senior software engineer.

Analyze these git commits and summarize:

- What kind of project this is
- What work has been done
- Development stage (early / mid / mature)

COMMITS:
{commits}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI Error: {str(e)}"