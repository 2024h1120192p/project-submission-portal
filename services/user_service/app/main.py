
from fastapi import FastAPI, HTTPException
from libs.events.schemas import User
from .store import store
from fastapi import status
from typing import List

app = FastAPI()

@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    await store.create(user)
    return user

@app.get("/users/{id}", response_model=User)
async def get_user(id: str):
    u = await store.get(id)
    if not u:
        raise HTTPException(404)
    return u

@app.get("/users", response_model=List[User])
async def list_users():
    return await store.list()

@app.put("/users/{id}", response_model=User)
async def update_user(id: str, user: User):
    existing = await store.get(id)
    if existing is None:
        raise HTTPException(404)
    return await store.update(id, user)

@app.delete("/users/{id}")
async def delete_user(id: str):
    u = await store.delete(id)
    if not u:
        raise HTTPException(404)
    return {"deleted": True}
