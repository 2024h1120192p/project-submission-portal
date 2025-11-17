from datetime import datetime
from uuid import uuid4
from libs.events.schemas import Notification
from typing import List
import asyncio


class NotificationStore:
    """In-memory notification store with timestamps.
    
    Thread-safe async implementation for storing and retrieving notifications.
    """
    
    def __init__(self):
        self.items: list[Notification] = []
        self._lock = asyncio.Lock()

    async def add(self, user_id: str, message: str) -> Notification:
        """Add a new notification to the store.
        
        Args:
            user_id: ID of the user to notify
            message: Notification message
            
        Returns:
            Notification: Created notification with generated ID and timestamp
        """
        async with self._lock:
            notification = Notification(
                id=str(uuid4()),
                user_id=user_id,
                message=message,
                created_at=datetime.now()
            )
            self.items.append(notification)
            return notification
    
    async def get_by_user(self, user_id: str) -> List[Notification]:
        """Get all notifications for a specific user.
        
        Args:
            user_id: User ID to filter by
            
        Returns:
            List[Notification]: Notifications for the user, sorted by timestamp (newest first)
        """
        async with self._lock:
            user_notifications = [
                n for n in self.items if n.user_id == user_id
            ]
            # Sort by created_at descending (newest first)
            return sorted(user_notifications, key=lambda x: x.created_at, reverse=True)
    
    async def list(self) -> List[Notification]:
        """Get all notifications.
        
        Returns:
            List[Notification]: All notifications, sorted by timestamp (newest first)
        """
        async with self._lock:
            return sorted(self.items, key=lambda x: x.created_at, reverse=True)
    
    async def get(self, notification_id: str) -> Notification | None:
        """Get a notification by ID.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Notification | None: Notification if found, None otherwise
        """
        async with self._lock:
            for notification in self.items:
                if notification.id == notification_id:
                    return notification
            return None


store = NotificationStore()
