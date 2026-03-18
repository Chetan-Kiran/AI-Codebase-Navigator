from fastapi import APIRouter
import os

from ai.groq_client import analyze_codebase_structure
from ai.groq_client import ask_question_about_repo
from tools.list_files import list_repository_files
from tools.read_files import read_repository_code
from tools.search_files import find_relevant_files
from tools.read_files import read_specific_files
from tools.git_tools import git_log
from ai.groq_client import summarize_commits
from tools.git_tools import git_file_history

router = APIRouter()

@router.post("/analyze-structure")
def analyze_structure(repo_path: str = "."):

    try:

        print("PATH:", repo_path)

        print("ABS:", os.path.abspath(repo_path))

        structure = list_repository_files(repo_path)[:1000]

        code = read_repository_code(repo_path)

        summary = analyze_codebase_structure(structure, code)

        return {
            "repo_structure": structure,
            "ai_analysis": summary
        }

    except Exception as e:
        return {"error": str(e)}

# @router.post("/ask-repo")
# def ask_repo(repo_path: str, question: str):

#     structure = list_repository_files(repo_path)[:1000]
#     code = read_repository_code(repo_path)

#     context = f"""
# Answer the question based on the repository.

# Repository:
# {structure}

# Code:
# {code}

# Question:
# {question}
# """

#     answer = ask_question_about_repo(context)

#     return {"answer": answer}

#this endpoint is updated version uses RAG (Smart file search)

@router.post("/ask-repo")
def ask_repo(repo_path: str, question: str):

    MAX_CHARS = 4000
    # 1. find relevant files
    files = find_relevant_files(repo_path, question)

    print("FILES SELECTED:", files)
    # 2. read only those files
    code = read_specific_files(files)[:MAX_CHARS]

    print("CODE LENGTH:", len(code))
    # 3. build context
    context = f"""
You are a senior software engineer.

STRICT RULES:
- Answer ONLY using the provided code
- If not found, say "Not found in repository"
- Be precise and technical

FILES:
{code}

QUESTION:
{question}
"""

    # 4. ask AI
    answer = ask_question_about_repo(context)

    return {
        "files_used": files,
        "answer": answer
    }

@router.post("/chat")
def chat(repo_path: str, message: str):

    files = find_relevant_files(repo_path, message)
    print("FILES SELECTED:", files)

    code = read_specific_files(files)[:4000]

    context = f"""
You are an expert coding assistant.

Help the user understand the repository.

RULES:
- Use only given code
- Explain clearly
- If unsure, say so

CODE:
{code}

USER MESSAGE:
{message}
"""

    reply = ask_question_about_repo(context)

    return {
        "files_used": files,
        "reply": reply
    }

@router.post("/analyze-commits")
def analyze_commits(repo_path: str):

    commits = ""  # ✅ always defined

    try:
        print("REPO PATH:", repo_path)

        commits = git_log(repo_path)
        print("COMMITS:", commits)

        # ✅ safe check
        if not commits.strip():
            return {
                "error": "No commits found",
                "details": commits
            }

        # ✅ AI call separately protected
        try:
            summary = summarize_commits(commits[:2000])
        except Exception as ai_error:
            return {
                "raw_commits": commits,
                "analysis": "AI failed to summarize",
                "ai_error": str(ai_error)
            }

        return {
            "raw_commits": commits,
            "analysis": summary
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "error": "Internal failure",
            "details": str(e),
            "commits": commits
        }

@router.post("/file-history")
def file_history(repo_path: str, file: str):
    history = git_file_history(repo_path, file)

    return {
        "file": file,
        "history": history
    }