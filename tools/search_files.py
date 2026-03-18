import os
import re

IGNORE_DIRS = {"venv", ".venv", "__pycache__", "node_modules", ".git"}

def extract_keywords(query: str):
    return re.findall(r'\w+', query.lower())


def find_relevant_files(repo_path: str, query: str, max_files: int = 3):
    keywords = extract_keywords(query)

    scored_files = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            path = os.path.join(root, file)

            score = 0
            file_lower = file.lower()

            # filename match
            score += sum(2 for word in keywords if word in file_lower)

            # 🔥 content match
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read(1000).lower()

                score += sum(1 for word in keywords if word in content)

            except:
                continue

            if score > 0:
                scored_files.append((score, path))

    scored_files.sort(reverse=True)

    return [file for _, file in scored_files[:max_files]]