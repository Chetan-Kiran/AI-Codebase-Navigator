import os
from pathlib import Path

def list_repository_files(directory: str = ".") -> str:
    """Lists all files in the repository directory, ignoring common paths."""
    
    ignore_dirs = {'.git', '__pycache__', 'venv', 'node_modules', '.idea', '.vscode'}
    output_lines = []
    
    base_path = Path(directory).resolve()
    
    for root, dirs, files in os.walk(base_path):
        # Remove ignored directories from dirs so os.walk doesn't dive into them
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        path = Path(root)
        level = len(path.relative_to(base_path).parts) if path != base_path else 0
        indent = '  ' * level
        
        if path != base_path:
            output_lines.append(f"{indent}📁 {path.name}/")
            
        subindent = '  ' * (level + 1)
        for f in files:
            output_lines.append(f"{subindent}📄 {f}")
            
    return "\n".join(output_lines)