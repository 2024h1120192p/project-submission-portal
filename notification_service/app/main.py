from fastapi import FastAPI
from pydantic import BaseModel
from .store import store

app = FastAPI()

class NotifyRequest(BaseModel):
    user_id: str
    message: str

@app.post("/notify")
def notify(req: NotifyRequest):
    return store.add(req.user_id, req.message)
