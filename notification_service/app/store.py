from datetime import datetime
from uuid import uuid4
from libs.events.schemas import Notification

class NotificationStore:
    def __init__(self):
        self.items: list[Notification] = []

    def add(self, user_id: str, message: str) -> Notification:
        n = Notification(
            id=str(uuid4()),
            user_id=user_id,
            message=message,
            created_at=datetime.now()
        )
        self.items.append(n)
        return n

store = NotificationStore()
