# from mcp.server.fastmcp import FastMCP

from tools.git_tools import git_log, git_commit_detail, git_diff
from tools.search_files import find_relevant_files
from tools.read_files import read_specific_files, read_repository_code
from mcp_core.bug_finder import find_bug_introducing_commit

from ai.groq_client import (
    ask_question_about_repo,
    analyze_commit_risk,
    analyze_diff,
    summarize_commits
)

# mcp = FastMCP("Tools")

# @mcp.tool()
def risk_analysis_tool(repo_path: str) -> str:
    commits = git_log(repo_path, limit=3)
    if not commits or "Error" in commits:
        return "No commits found to analyze."
    
    latest_commit = commits.split("\n")[0].split(" ")[0]
    commit_data = git_commit_detail(repo_path, latest_commit)
    return analyze_commit_risk(commit_data[:2000])

# @mcp.tool()
def commit_summary_tool(repo_path: str) -> str:
    commits = git_log(repo_path, limit=5)

    if not commits.strip():
        return "No commits found to summarize."
    
    return summarize_commits(commits[:2000])


# @mcp.tool()
def diff_analysis_tool(repo_path: str) -> str:
    diff = git_diff(repo_path)

    if not diff.strip():
        return "No differences found in the latest commit."
    
    return analyze_diff(diff[:2000])


# @mcp.tool()
def bug_origin_tool(repo_path: str) -> str:

    if not git_log(repo_path, limit=1).strip():
        return "No commits found to analyze for bugs."
    
    return find_bug_introducing_commit(repo_path)


# @mcp.tool()
def repo_qa_tool(repo_path: str, question: str) -> str:
    files = find_relevant_files(repo_path, question)
    files = [f[0] if isinstance(f, tuple) else f for f in files]

    if not files:
        code = read_repository_code(repo_path)[:4000]
    else:
        code = read_specific_files(files)[:4000]

    context = f"""
You are a senior software engineer.

Explain clearly and concisely.

CODE:
{code}

QUESTION:
{question}
"""

    return ask_question_about_repo(context)

# if __name__ == "__main__":
#     mcp.run()

Tools = {
    "risk_analysis": risk_analysis_tool,
    "commit_summary": commit_summary_tool,
    "diff_analysis": diff_analysis_tool,
    "bug_origin": bug_origin_tool,
    "repo_qa": repo_qa_tool
}