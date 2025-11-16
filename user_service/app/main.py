from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
from .store import store
from libs.events.schemas import User

app = FastAPI()

@app.post("/users")
def create_user(user: User):
    store.create(user)
    return user

@app.get("/users/{id}")
def get_user(id: str):
    u = store.get(id)
    if not u:
        raise HTTPException(404)
    return u

@app.get("/users")
def list_users():
    return store.list()

@app.put("/users/{id}")
def update_user(id: str, user: User):
    if store.get(id) is None:
        raise HTTPException(404)
    return store.update(id, user)

@app.delete("/users/{id}")
def delete_user(id: str):
    u = store.delete(id)
    if not u:
        raise HTTPException(404)
    return {"deleted": True}
