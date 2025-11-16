from fastapi import FastAPI
from libs.events.schemas import Submission
from .store import SubmissionStore
from datetime import datetime, timezone
import uuid

app = FastAPI()
store = SubmissionStore()

def emit_submission_uploaded(event: dict):
    # stub emit
    print("KAFKA: submission_uploaded ->", event)

@app.post("/submissions", response_model=Submission)
def create_submission(sub: Submission):
    new_sub = Submission(
        id=sub.id or str(uuid.uuid4()),
        user_id=sub.user_id,
        assignment_id=sub.assignment_id,
        uploaded_at=sub.uploaded_at or datetime.now(timezone.utc),
        file_url=sub.file_url,
        text=sub.text,
    )
    store.save(new_sub)
    emit_submission_uploaded(new_sub.model_dump())
    return new_sub

@app.get("/submissions/{submission_id}", response_model=Submission)
def get_submission(submission_id: str):
    return store.get(submission_id)

@app.get("/submissions/user/{user_id}", response_model=list[Submission])
def get_by_user(user_id: str):
    return store.get_by_user(user_id)
