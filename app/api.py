import os
from fastapi import APIRouter
import shutil

from ai.groq_client import analyze_codebase_structure
from ai.groq_client import ask_question_about_repo
from ai.groq_client import summarize_commits
from ai.groq_client import analyze_diff 
from ai.groq_client import analyze_commit_risk
from ai.groq_client import analyze_commit_timeline
from ai.groq_client import analyze_diff

from tools.list_files import list_repository_files
from tools.read_files import read_repository_code
from tools.search_files import find_relevant_files
from tools.read_files import read_specific_files
from tools.git_tools import git_log
from tools.git_tools import git_file_history
from tools.git_clone import clone_repo
# from tools.git_tools import git_diff_commit 
from tools.git_tools import git_commit_detail
from tools.git_tools import git_commit_files
from tools.git_tools import git_log_detailed
from tools.git_tools import git_commit_files
from tools.git_tools import git_diff_commit
# from tools.git_tools import clone_repo

from mcp.bug_finder import find_bug_introducing_commit
from mcp.router import mcp_router

router = APIRouter()

def resolve_repo_path(repo_path: str):
    repo_path = repo_path.strip()

    if "repo_path" in repo_path:
        repo_path = repo_path.split("=")[-1].strip()

    if repo_path.startswith("http"):
        path = clone_repo(repo_path)

        # ✅ safety check
        if isinstance(path, tuple):
            path = path[0]

        if isinstance(path, str) and path.startswith("Error"):
            raise Exception(path)

        print("CLONED PATH:", path)
        return path

    return repo_path

@router.post("/analyze-structure")
def analyze_structure(repo_path: str = "."):

    try:
        repo_path = resolve_repo_path(repo_path)
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

    repo_path = resolve_repo_path(repo_path)

    MAX_CHARS = 4000

    files = find_relevant_files(repo_path, question)

    # 🔥 CRITICAL FIX
    files = [f[0] if isinstance(f, tuple) else f for f in files]

    # 🔥 fallback
    if not files:
        print("⚠️ No relevant files found, using full repo")
        code = read_repository_code(repo_path)[:MAX_CHARS]
    else:
        code = read_specific_files(files)[:MAX_CHARS]   

    print("FILES SELECTED:", files)

    print("FILES TYPE:", type(files))
    for f in files:
        print("FILE:", f, "TYPE:", type(f))

    context = f"""
        You are a senior software engineer.

        FILES:
        {code}

        QUESTION:
        {question}
    """

    answer = ask_question_about_repo(context)

    return {
        "files_used": files,
        "answer": answer
    }

@router.post("/chat")
def chat(repo_path: str, message: str):

    repo_path = resolve_repo_path(repo_path)

    files = find_relevant_files(repo_path, message)
    print("FILES SELECTED:", files)

    files = [f[0] if isinstance(f, tuple) else f for f in files]
    
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

    repo_path = resolve_repo_path(repo_path)
    
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
    repo_path = resolve_repo_path(repo_path)
    
    history = git_file_history(repo_path, file)

    return {
        "file": file,
        "history": history
    }

@router.post("/analyze-diff")
def analyze_diff_api(repo_path: str, commit_id: str):
    repo_path = resolve_repo_path(repo_path)
    # diff = git_diff_commit(repo_path, commit_id )
    diff = git_commit_detail(repo_path, commit_id)
    summary = analyze_diff(diff[:2000])

    return {
        "diff": diff,
        "analysis": summary
    }

@router.post("/commit-risk")
def commit_risk(repo_path: str, commit_id: str):

    repo_path = resolve_repo_path(repo_path)
    try:
        commit_data = git_commit_detail(repo_path, commit_id)

        if not commit_data.strip():
            return {"error": "No commit data found"}

        analysis = analyze_commit_risk(commit_data[:3000])

        return {
            "commit_id": commit_id,
            "analysis": analysis
        }

    except Exception as e:
        return {"error": str(e)}

@router.post("/commit-intelligence")
def commit_intelligence(repo_path: str = None, repo_url: str = None, commit_id: str = ""):

    repo_path = resolve_repo_path(repo_path)
    temp_dir = None

    try:
        # 🔥 decide source
        if repo_url:
            # temp_dir, error = clone_repo(repo_url)
            temp_dir = clone_repo(repo_url)

            if temp_dir.startswith("Error"):
                return {"error": temp_dir}

            repo_path = temp_dir

        if not repo_path:
            return {"error": "Provide repo_path or repo_url"}

        # ✅ your existing logic
        files = git_commit_files(repo_path, commit_id)
        diff = git_diff_commit(repo_path, commit_id)

        diff_limited = diff[:3000]

        diff_analysis = analyze_diff(diff_limited)
        risk_analysis = analyze_commit_risk(diff_limited)

        return {
            "commit": commit_id,
            "files": files,
            "diff_analysis": diff_analysis,
            "risk_analysis": risk_analysis
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        # 🧹 cleanup
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

@router.post("/repo-timeline")
def repo_timeline_basic(repo_path: str):

    repo_path = resolve_repo_path(repo_path)

    try:
        raw_commits = git_log(repo_path, limit=5)

        if not raw_commits.strip():
            return {"timeline": []}

        timeline = []

        for line in raw_commits.split("\n"):
            parts = line.split(" ", 1)

            if len(parts) < 2:
                continue

            timeline.append({
                "commit": parts[0],
                "message": parts[1]
            })

        return {"timeline": timeline}

    except Exception as e:
        return {"error": str(e)}

@router.post("/repo-timeline-deep")
def repo_timeline_deep(repo_path: str):

    repo_path = resolve_repo_path(repo_path)

    try:
        raw_commits = git_log(repo_path, limit=5)

        if not raw_commits or "Error" in raw_commits:
            return {"error": "Failed to fetch commits"}

        timeline = []

        for line in raw_commits.split("\n"):
            parts = line.split(" ", 1)

            if len(parts) < 2:
                continue

            commit_id = parts[0].strip()
            message = parts[1].strip()

            commit_data = git_commit_detail(repo_path, commit_id)[:2000]

            try:
                analysis = analyze_commit_risk(commit_data)
            except Exception as e:
                analysis = f"AI failed: {str(e)}"

            timeline.append({
                "commit": commit_id,
                "message": message,
                "analysis": analysis
            })

        return {"timeline": timeline}

    except Exception as e:
        return {"error": str(e)}

@router.post("/chat-ai")
def chat_ai(repo_path: str, message: str):
    repo_path = resolve_repo_path(repo_path)

    result = mcp_router(repo_path, message)

    return {
        "type": result.get("type"),
        "answer": result.get("data"),
        "files_used": result.get("files_used", [])
    }

@router.post("/find-bug")
def find_bug(repo_path: str):
    repo_path = resolve_repo_path(repo_path)
    return find_bug_introducing_commit(repo_path)

@router.post("/commit-files")
def commit_files(repo_path: str, commit_id: str):
    repo_path = resolve_repo_path(repo_path)
    try:
        files = git_commit_files(repo_path, commit_id)

        if not files:
            return {"error": "No files found"}

        return {
            "commit": commit_id.strip(),
            "files": files
        }

    except Exception as e:
        return {"error": str(e)}

@router.post("/commit-diff-analysis")
def commit_diff_analysis(repo_path: str, commit_id: str):
    repo_path = resolve_repo_path(repo_path)
    try:
        diff = git_diff_commit(repo_path, commit_id)

        if not diff.strip():
            return {"error": "No diff found"}

        summary = analyze_diff(diff[:3000])  # prevent token overflow

        return {
            "commit": commit_id.strip(),
            "diff": diff,
            "analysis": summary
        }

    except Exception as e:
        return {"error": str(e)}