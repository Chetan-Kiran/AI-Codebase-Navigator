import os

def read_repository_code(repo_path: str, max_total_chars: int = 4000):
    code_data = []
    total_chars = 0

    IGNORE_DIRS = {"venv", ".venv", "__pycache__", "node_modules", ".git"}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".java", ".cpp")):
                path = os.path.join(root, file)

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read(800)  # limit per file

                    snippet = f"\nFILE: {file}\n{content}\n------\n"

                    if total_chars + len(snippet) > max_total_chars:
                        return "\n".join(code_data)

                    code_data.append(snippet)
                    total_chars += len(snippet)

                except:
                    pass

    return "\n".join(code_data)

def read_specific_files(files):
    code = ""

    for file in files:

        # 🔥 SAFETY FIX
        if isinstance(file, (tuple, list)):
            file = file[0]

        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                code += f"\n\nFILE: {file}\n"
                code += f.read()

        except Exception as e:
            print(f"Error reading {file}: {e}")

    return code