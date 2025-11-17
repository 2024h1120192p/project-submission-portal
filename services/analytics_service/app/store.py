"""In-memory storage for analytics windows (simulates Firestore)."""
from datetime import datetime, timezone
from libs.events.schemas import AnalyticsWindow
from typing import List, Optional

# In-memory Firestore simulation
ANALYTICS_DB: List[AnalyticsWindow] = []


async def add_window(window: AnalyticsWindow) -> None:
    """Add a new analytics window to storage.
    
    Args:
        window: AnalyticsWindow object to store
    """
    ANALYTICS_DB.append(window)


async def get_latest() -> Optional[AnalyticsWindow]:
    """Get the most recent analytics window.
    
    Returns:
        AnalyticsWindow if data exists, None otherwise
    """
    if not ANALYTICS_DB:
        return None
    return ANALYTICS_DB[-1]


async def get_history() -> List[AnalyticsWindow]:
    """Get all analytics windows ordered by timestamp.
    
    Returns:
        List of all AnalyticsWindow objects
    """
    return ANALYTICS_DB
