import os
from pathlib import Path

def list_repository_files(directory: str = ".") -> str:
    ignore_dirs = {".git", "__pycache__", "venv", ".venv", "node_modules"}

    output_lines = []
    base_path = Path(directory).resolve()

    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        path = Path(root)

        level = len(path.relative_to(base_path).parts) if path != base_path else 0
        indent = "  " * level

        if path != base_path:
            output_lines.append(f"{indent}📁 {path.name}/")

        for file in files:
            output_lines.append(f"{indent}  📄 {file}")

    return "\n".join(output_lines)