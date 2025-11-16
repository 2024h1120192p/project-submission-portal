from fastapi import FastAPI
from libs.events.schemas import Submission, PlagiarismResult
from .engine import run_plagiarism_pipeline

app = FastAPI()

def emit_plagiarism_checked(event: PlagiarismResult):
    print("EMIT_KAFKA_EVENT", event.model_dump())

@app.post("/check", response_model=PlagiarismResult)
def check(sub: Submission):
    result = run_plagiarism_pipeline(sub)
    emit_plagiarism_checked(result)
    return result
