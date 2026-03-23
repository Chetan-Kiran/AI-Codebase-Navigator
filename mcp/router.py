from tools.git_tools import git_log, git_commit_detail, git_diff
from tools.search_files import find_relevant_files
from tools.read_files import read_specific_files
# from tools.git_clone import clone_repo
# from app.api import resolve_repo_path
from tools.read_files import read_repository_code
from mcp.bug_finder import find_bug_introducing_commit

from ai.groq_client import (
    ask_question_about_repo,
    analyze_commit_risk,
    analyze_diff,
    summarize_commits
)


# def mcp_router(repo_path: str, user_message: str):
#     repo_path = resolve_repo_path(repo_path)
#     """
#     Decide which tools to use based on user message
#     """

#     message = user_message.lower()

#     try:
#         # 🔥 1. Commit-related questions
#         if "bug" in message or "error" in message or "issue" in message:
#             commits = git_log(repo_path, limit=3)
#             latest_commit = commits.split("\n")[0].split(" ")[0]

#             commit_data = git_commit_detail(repo_path, latest_commit)
#             risk = analyze_commit_risk(commit_data[:2000])

#             return {
#                 "type": "risk_analysis",
#                 "data": risk
#             }

#         # 🔥 2. Bug / risk detection
#         elif "commit" in message or "history" in message:
#             commits = git_log(repo_path, limit=5)
#             summary = summarize_commits(commits[:2000])

#             return {
#                 "type": "commit_analysis",
#                 "data": summary
#             }

#         # 🔥 3. Diff analysis
#         elif "change" in message or "diff" in message:
#             diff = git_diff(repo_path)
#             analysis = analyze_diff(diff[:2000])

#             return {
#                 "type": "diff_analysis",
#                 "data": analysis
#             }

#         elif "which commit" in message or "introduced bug" in message:
#             result = find_bug_introducing_commit(repo_path)

#             return {
#                 "type": "bug_origin",
#                 "data": result
#             }
            
#         # 🔥 4. Default → Repo Q&A (RAG)
#         else:
#             files = find_relevant_files(repo_path, user_message)
#             files = [f[0] if isinstance(f, tuple) else f for f in files]

#             if not files:
#                 code = read_repository_code(repo_path)[:4000]
#             else:
#                 code = read_specific_files(files)[:4000]    
            
#             context = f"""
# You are an expert coding assistant.

# CODE:
# {code}

# USER:
# {user_message}
# """

#             answer = ask_question_about_repo(context)

#             return {
#                 "type": "repo_qa",
#                 "files_used": files,
#                 "data": answer
#             }

#     except Exception as e:
#         return {
#             "error": str(e)
#         }

from tools.read_files import read_specific_files, read_repository_code

def mcp_router(repo_path: str, user_message: str):

    message = user_message.lower()

    try:
        if "bug" in message or "error" in message:
            commits = git_log(repo_path, limit=3)
            latest_commit = commits.split("\n")[0].split(" ")[0]

            commit_data = git_commit_detail(repo_path, latest_commit)
            risk = analyze_commit_risk(commit_data[:2000])

            return {"type": "risk_analysis", "data": risk}

        elif "commit" in message:
            commits = git_log(repo_path, limit=5)
            summary = summarize_commits(commits[:2000])

            return {"type": "commit_analysis", "data": summary}

        elif "diff" in message or "change" in message:
            diff = git_diff(repo_path)
            analysis = analyze_diff(diff[:2000])

            return {"type": "diff_analysis", "data": analysis}

        elif "introduced bug" in message:
            result = find_bug_introducing_commit(repo_path)
            return {"type": "bug_origin", "data": result}

        else:
            files = find_relevant_files(repo_path, user_message)

            # ✅ FIX tuple issue
            files = [f[0] if isinstance(f, tuple) else f for f in files]

            print("FILES:", files)

            # ✅ SAFE fallback
            if not files:
                code = read_repository_code(repo_path)[:4000]
            else:
                code = read_specific_files(files)[:4000]

            context = f"""
You are an expert coding assistant.

CODE:
{code}

USER:
{user_message}
"""

            answer = ask_question_about_repo(context)

            return {
                "type": "repo_qa",
                "files_used": files,
                "data": answer
            }

    except Exception as e:
        return {"error": str(e)}