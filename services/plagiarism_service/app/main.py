from fastapi import FastAPI
from libs.events.schemas import Submission, PlagiarismResult
from libs.events.kafka import emit_event
from .engine import run_plagiarism_pipeline

app = FastAPI()

@app.post("/check", response_model=PlagiarismResult)
def check(sub: Submission):
    result = run_plagiarism_pipeline(sub)
    emit_event("plagiarism_checked", result.model_dump())
    return result
