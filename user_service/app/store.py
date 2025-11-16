from typing import Dict
from libs.events.schemas import User

class UserStore:
    def __init__(self):
        self.users: Dict[str, User] = {}

    def create(self, user: User):
        self.users[user.id] = user
        return user

    def get(self, user_id: str):
        return self.users.get(user_id)

    def list(self):
        return list(self.users.values())

    def update(self, user_id: str, user: User):
        self.users[user_id] = user
        return user

    def delete(self, user_id: str):
        return self.users.pop(user_id, None)

store = UserStore()
