
from typing import Dict
from libs.events.schemas import User
import asyncio

class UserStore:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self._lock = asyncio.Lock()

    async def create(self, user: User):
        async with self._lock:
            self.users[user.id] = user
            return user

    async def get(self, user_id: str):
        async with self._lock:
            return self.users.get(user_id)

    async def list(self):
        async with self._lock:
            return list(self.users.values())

    async def update(self, user_id: str, user: User):
        async with self._lock:
            self.users[user_id] = user
            return user

    async def delete(self, user_id: str):
        async with self._lock:
            return self.users.pop(user_id, None)

store = UserStore()
