"""Async client for Notification Service."""

import httpx
from libs.events.schemas import Notification
from typing import List, Optional


class AsyncHTTPClient:
    """Base async HTTP client."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)

    async def get(self, url: str, **kwargs):
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self._client.post(url, **kwargs)

    async def put(self, url: str, **kwargs):
        return await self._client.put(url, **kwargs)

    async def delete(self, url: str, **kwargs):
        return await self._client.delete(url, **kwargs)

    async def close(self):
        await self._client.aclose()


class NotificationServiceClient:
    """Async client for interacting with the Notification Service.
    
    This client provides methods to send notifications and retrieve
    notification history for users.
    
    Example:
        ```python
        client = NotificationServiceClient("http://localhost:8005")
        notification = await client.send("user_123", "Your submission was processed")
        notifications = await client.get_user_notifications("user_123")
        ```
    """
    
    def __init__(self, base_url: str):
        """Initialize the notification service client.
        
        Args:
            base_url: Base URL of the notification service (e.g., http://localhost:8005)
        """
        self.client = AsyncHTTPClient(base_url)
    
    async def send(self, user_id: str, message: str) -> Optional[Notification]:
        """Send a notification to a user.
        
        Args:
            user_id: ID of the user to notify
            message: Notification message
            
        Returns:
            Optional[Notification]: Created notification if successful, None otherwise
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        resp = await self.client.post(
            "/notify",
            json={"user_id": user_id, "message": message}
        )
        if resp.status_code in (200, 201):
            return Notification(**resp.json())
        return None
    
    async def get_user_notifications(self, user_id: str) -> List[Notification]:
        """Get all notifications for a specific user.
        
        Args:
            user_id: User ID to fetch notifications for
            
        Returns:
            List[Notification]: List of notifications for the user (newest first)
        """
        resp = await self.client.get(f"/notifications/{user_id}")
        if resp.status_code == 200:
            return [Notification(**n) for n in resp.json()]
        return []
    
    async def get_all_notifications(self) -> List[Notification]:
        """Get all notifications in the system.
        
        Returns:
            List[Notification]: All notifications (newest first)
        """
        resp = await self.client.get("/notifications")
        if resp.status_code == 200:
            return [Notification(**n) for n in resp.json()]
        return []
    
    async def close(self):
        """Close the HTTP client connection."""
        await self.client.close()
