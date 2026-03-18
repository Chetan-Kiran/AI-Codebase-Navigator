import subprocess

def run_git_command(repo_path: str, command: list) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        return result.stdout.strip()
    except Exception as e:
        return f"Exception: {str(e)}"


def git_log(repo_path: str) -> str:
    """
    Get last 5 commits (oneline)
    """
    return run_git_command(repo_path, ["git", "log", "--oneline", "-5"])


def git_file_history(repo_path: str, file: str) -> str:
    """
    Get commit history of a specific file
    """
    return run_git_command(repo_path, ["git", "log", "--oneline", "--", file])