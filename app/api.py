from fastapi import APIRouter
from tools.list_files import list_repository_files
from ai.gemini_client import analyze_codebase_structure

router = APIRouter()

@router.post("/analyze-structure")
def analyze(repo_path: str = "."):
    files = list_repository_files(repo_path)
    summary = analyze_codebase_structure(files)
    return {"summary": summary}