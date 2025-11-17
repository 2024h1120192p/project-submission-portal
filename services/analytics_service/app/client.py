"""Client for interacting with the analytics service from other services."""
import httpx
from libs.events.schemas import AnalyticsWindow
from typing import List, Optional


class AnalyticsServiceClient:
    """Async client for analytics service operations.
    
    Provides methods to interact with the analytics service API.
    Uses httpx.AsyncClient for async HTTP requests.
    """
    
    def __init__(self, base_url: str):
        """Initialize client with base URL.
        
        Args:
            base_url: Base URL of the analytics service (e.g., http://localhost:8004)
        """
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)
    
    async def get_latest(self) -> Optional[AnalyticsWindow]:
        """Get the latest analytics window.
        
        Returns:
            AnalyticsWindow if available, None otherwise
        """
        try:
            resp = await self._client.get("/analytics/latest")
            if resp.status_code == 200:
                return AnalyticsWindow(**resp.json())
            return None
        except Exception as e:
            print(f"Error fetching latest analytics: {e}")
            return None
    
    async def get_history(self) -> List[AnalyticsWindow]:
        """Get all historical analytics windows.
        
        Returns:
            List of AnalyticsWindow objects, empty list if error or no data
        """
        try:
            resp = await self._client.get("/analytics/history")
            if resp.status_code == 200:
                return [AnalyticsWindow(**w) for w in resp.json()]
            return []
        except Exception as e:
            print(f"Error fetching analytics history: {e}")
            return []
    
    async def compute_analytics(self) -> Optional[AnalyticsWindow]:
        """Trigger computation of new analytics window.
        
        This fetches submission counts and plagiarism averages from
        other services and creates a new analytics window.
        
        Returns:
            AnalyticsWindow if successful, None otherwise
        """
        try:
            resp = await self._client.post("/analytics/compute")
            if resp.status_code == 200:
                return AnalyticsWindow(**resp.json())
            return None
        except Exception as e:
            print(f"Error computing analytics: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
