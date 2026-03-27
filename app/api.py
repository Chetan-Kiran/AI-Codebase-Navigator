import os
import json
import shutil
from fastapi import APIRouter

from mcp_core.mcp_router2 import mcp_router2

from ai.groq_client import analyze_codebase_structure
from ai.groq_client import ask_question_about_repo
from ai.groq_client import summarize_commits
from ai.groq_client import analyze_diff 
from ai.groq_client import analyze_commit_risk
from ai.groq_client import analyze_commit_timeline
from ai.groq_client import groq_chat

from tools.list_files import list_repository_files
from tools.read_files import read_repository_code
from tools.search_files import find_relevant_files
from tools.read_files import read_specific_files
from tools.git_tools import (
    git_log,
    git_commit_detail,
    git_commit_files,
    git_log_detailed,
    git_diff_commit,
    clone_repo,
    git_file_history
)

from typing import Optional, List, Union

from mcp_core.bug_finder import find_bug_introducing_commit
from tool_registry import (
    risk_analysis_tool,
    commit_summary_tool,
    diff_analysis_tool,
    bug_origin_tool,
    repo_qa_tool
)

router = APIRouter()

def resolve_repo_path(repo_path: Optional[str]):
    if repo_path is None:
        repo_path = "."
    repo_path = repo_path.strip()

    if "repo_path" in repo_path:
        repo_path = repo_path.split("=")[-1].strip()

    if repo_path.startswith("http"):
        path = clone_repo(repo_path)

        if isinstance(path, str) and path.startswith("Error"):
            raise Exception(path)

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
        "answer": answer,
        "files_used": files
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
def commit_intelligence(repo_path: Optional[str] = None, repo_url: Optional[str] = None, commit_id: str = ""):

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

@router.post("/list-files")
def list_files_api(repo_path: str):
    repo_path = resolve_repo_path(repo_path)
    files = list_repository_files(repo_path)

    return {
        "files": files[:500]
    }

@router.post("/read-file")
def read_file_api(repo_path: str, file_path: str):
    repo_path = resolve_repo_path(repo_path)

    full_path = os.path.join(repo_path, file_path)

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {"content": str(content)[:5000]}
    except Exception as e:
        return {"error": str(e)}

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

@router.post("/explain-file")
def explain_file(repo_path: str, file_path: str):

    code = read_specific_files([file_path])[:3000]

    context = f"""
You are a senior developer.

Explain this file clearly:

{code}
"""

    answer = ask_question_about_repo(context)

    return {
        "file": file_path,
        "explanation": answer
    }

from fastapi import Query

##This is the new endpoint for MCP Router version 2, which uses AI to decide the tool and flow but not @mcp.tool()##
@router.post("/chat-ai")
def chat_ai(repo_path: str = Query(...), message: str = Query(...)):
    repo_path = resolve_repo_path(repo_path)

    result = mcp_router2(repo_path, message)

    if "error" in result:
        return {"error": result["error"], "status": "error"}

    return {
        "type": result.get("type", "unknown"),
        "answer": result.get("data", "No answer"),
        "files_used": result.get("files_used", [])
    }

##This is for manulal tool routing, not used in current code but can be adapted for future###
# @router.post("/chat-ai")
# def chat_ai(repo_path: str, message: str):
#     repo_path = resolve_repo_path(repo_path)

#     result = mcp_router(repo_path, message)

#     return {
#         "type": result.get("type"),
#         "answer": result.get("data"),
#         "files_used": result.get("files_used", [])
#     }


## this is for @mcp.tool() version, not used in current code but can be adapted for future###
# @router.post("/chat-ai")
# def chat_ai(repo_path: str, message: str):
#     repo_path = resolve_repo_path(repo_path)

    # # 1. Complete Tool Definitions
    # tools = [
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "risk_analysis_tool",
    #             "description": "Analyze recent commit risk",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {"repo_path": {"type": "string"}},
    #                 "required": ["repo_path"]
    #             }
    #         }
    #     },
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "repo_qa_tool",
    #             "description": "Answer questions about the codebase using file context",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {
    #                     "repo_path": {"type": "string"},
    #                     "question": {"type": "string"}
    #                 },
    #                 "required": ["repo_path", "question"]
    #             }
    #         }
    #     },
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "diff_analysis_tool",
    #             "description": "Analyze the diff of the latest commit",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {"repo_path": {"type": "string"}},
    #                 "required": ["repo_path"]
    #             }
    #         }
    #     },
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "bug_origin_tool",
    #             "description": "Find the commit that introduced a bug",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {"repo_path": {"type": "string"}},
    #                 "required": ["repo_path"]
    #             }
    #         }
    #     },
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "commit_summary_tool",
    #             "description": "Summarize the latest 5 commits",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {"repo_path": {"type": "string"}},
    #                 "required": ["repo_path"]
    #             }
    #         }
    #     }
    #     # Add bug_origin_tool and diff_analysis_tool here similarly...
    # ]

    # messages = [{"role": "user", "content": message}]

    # # 2. Initial AI Call
    # response = groq_chat(messages, tools=tools)
    # msg = response.choices[0].message

    # # 3. Execution Loop
    # iterations = 0
    # while msg.tool_calls and iterations < 5:
    #     # We MUST append the assistant message that requested the tools
    #     messages.append(msg)
        
    #     for tool_call in msg.tool_calls:
    #         name = tool_call.function.name
    #         args = json.loads(tool_call.function.arguments)
    #         current_path = args.get("repo_path") or repo_path

    #         # Direct tool execution
    #         if name == "risk_analysis_tool":
    #             result = risk_analysis_tool(current_path)
    #         elif name == "commit_summary_tool":
    #             result = commit_summary_tool(current_path)
    #         elif name == "repo_qa_tool":
    #             result = repo_qa_tool(current_path, args.get("question", message))
    #         elif name == "diff_analysis_tool":
    #             result = diff_analysis_tool(current_path)
    #         elif name == "bug_origin_tool":
    #             result = bug_origin_tool(current_path)

    #         # ... add other elif blocks for your other tools
    #         else:
    #             result = f"Error: Tool {name} not found."

    #         # IMPORTANT: Append the tool result with the correct ID
    #         messages.append({
    #             "role": "tool",
    #             "name": name,
    #             "tool_call_id": tool_call.id,
    #             "content": str(result)
    #         })

    #     # 4. Get the final response from AI using the tool outputs
    #     response = groq_chat(messages, tools=tools) # Pass tools again if you want multi-turn
    #     msg = response.choices[0].message
    #     iterations += 1

    # return {
    #     "answer": msg.content
    # }

