from tools.git_tools import git_log, git_commit_detail
from ai.groq_client import analyze_commit_risk


def find_bug_introducing_commit(repo_path: str):

    commits_raw = git_log(repo_path, limit=5)

    if not commits_raw.strip():
        return {"error": "No commits found"}

    results = []

    for line in commits_raw.split("\n"):
        parts = line.split(" ", 1)

        if len(parts) < 2:
            continue

        commit_id = parts[0].strip()
        message = parts[1].strip()

        commit_data = git_commit_detail(repo_path, commit_id)[:2000]

        try:
            analysis = analyze_commit_risk(commit_data)
        except Exception as e:
            analysis = f"AI error: {str(e)}"

        results.append({
            "commit": commit_id,
            "message": message,
            "analysis": analysis
        })

    # 🔥 Simple logic: pick commit mentioning bug OR risky
    for r in results:
        if "bug" in r["message"].lower() or "HIGH" in r["analysis"]:
            return {
                "bug_commit": r,
                "all_checked": results
            }

    return {
        "message": "No clear bug commit found",
        "all_checked": results
    }