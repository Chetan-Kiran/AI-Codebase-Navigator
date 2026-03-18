from fastapi import FastAPI
from app.api import router

app = FastAPI()

app.include_router(router)

@app.get("/")
def home():
    return {"message": "AI Codebase Navigator is running"}