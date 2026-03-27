import subprocess
import os
import tempfile
import shutil

def run_git_command(repo_path, command):
    try:
        repo_path = os.path.abspath(repo_path)

        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",   # ✅ FIX
            errors="ignore"     # ✅ FIX (prevents crash)
        )

        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"

        return result.stdout.strip()

    except Exception as e:
        return f"Exception: {str(e)}"


# ✅ last N commits
def git_log(repo_path, limit=10):
    return run_git_command(
        repo_path,
        ["git", "log", f"--oneline", f"-{limit}"]
    )


# ✅ files changed in commit
def git_commit_files(repo_path, commit_id):
    commit_id = commit_id.strip()

    return run_git_command(
        repo_path,
        ["git", "show", "--name-only", "--pretty=format:", commit_id]
    )


# ✅ full commit detail (message + diff)
def git_commit_detail(repo_path, commit_id):
    commit_id = commit_id.strip()

    return run_git_command(
        repo_path,
        ["git", "show", commit_id]
    )

# def git_diff_commit(repo_path, commit_id):
#     commit_id = commit_id.strip()

#     return run_git_command(
#         repo_path,
#         ["git", "show", commit_id]
#     )   


# ✅ diff between commits
def git_diff(repo_path):
    return run_git_command(
        repo_path,
        ["git", "diff", "HEAD~1", "HEAD"]
    )


# ✅ file history
def git_file_history(repo_path, file):
    return run_git_command(
        repo_path,
        ["git", "log", "--oneline", "--", file]
    )

def git_log_detailed(repo_path, limit=10):
    return run_git_command(
        repo_path,
        ["git", "log", f"-{limit}", "--pretty=format:%h|%s"]
    )

def git_commit_files(repo_path, commit_id):
    commit_id = commit_id.strip()

    output = run_git_command(
        repo_path,
        ["git", "show", "--name-only", "--pretty=format:", commit_id]
    )

    # convert to list
    files = [f.strip() for f in output.split("\n") if f.strip()]

    return files

def git_diff_commit(repo_path, commit_id):
    commit_id = commit_id.strip()

    return run_git_command(
        repo_path,
        ["git", "show", commit_id]
    )

def clone_repo(repo_url: str):

    CLONE_DIR = "cloned_repos"

    repo_name = repo_url.split("/")[-1].replace(".git", "").strip()
    repo_path = os.path.join(CLONE_DIR, repo_name)

    try:
        if not os.path.exists(CLONE_DIR):
            os.makedirs(CLONE_DIR)

        repo_name = repo_url.split("/")[-1].replace(".git", "").strip()
        local_path = os.path.join(CLONE_DIR, repo_name)

        if os.path.exists(local_path):
            subprocess.run(["git", "-C", repo_path, "pull"], check=True)
            return local_path

        subprocess.run(
            ["git", "clone", repo_url, local_path],
            check=True,
            capture_output=True,
            text=True
        )

        return local_path

    except Exception as e:
        return f"Error: {str(e)}"